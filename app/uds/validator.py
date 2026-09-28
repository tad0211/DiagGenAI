from typing import Optional, List, Dict, Any
from app.uds.models import ValidationResult, ValidationStatus, ValidationIssue
from app.uds.rules import (
    clean_hex_string, hex_to_bytes, STANDARD_SERVICES, STANDARD_NRCS,
    DID_REGISTRY, VALIDATION_RULES_REGISTRY
)
from app.database.repository import DiagRepository

def validate_uds_request(
    request_hex: str,
    active_session: str = "DefaultSession",
    active_security: str = "Locked",
    simulated_vehicle_speed: float = 0.0
) -> ValidationResult:
    """
    Perform deterministic validation on a UDS request frame according to ISO 14229-1
    and indexed ECU specification rules.
    """
    clean_hex = clean_hex_string(request_hex)
    repo = DiagRepository()
    issues: List[ValidationIssue] = []

    if not clean_hex:
        return ValidationResult(
            status=ValidationStatus.INVALID,
            request_hex="",
            service_id_hex="",
            issues=[
                ValidationIssue(
                    rule="RULE_HEX_FORMAT",
                    reason="The diagnostic request contains no hex bytes.",
                    suggested_correction="Provide at least a 1-byte UDS Service Identifier (e.g., 22 F1 90).",
                    source_evidence="ISO 14229-1 Section 7",
                    severity="ERROR"
                )
            ]
        )

    # Convert to bytes
    try:
        raw_bytes = hex_to_bytes(clean_hex)
    except Exception as e:
        return ValidationResult(
            status=ValidationStatus.INVALID,
            request_hex=request_hex,
            service_id_hex="",
            issues=[
                ValidationIssue(
                    rule="RULE_HEX_FORMAT",
                    reason=f"Malformed hexadecimal format: {str(e)}",
                    suggested_correction="Check that all tokens are valid 2-character hex numbers (0-9, A-F).",
                    source_evidence="ISO 14229-1 Frame Syntax",
                    severity="ERROR"
                )
            ]
        )

    sid = raw_bytes[0]
    sid_hex = f"0x{sid:02X}"
    req_len = len(raw_bytes)

    # 1. Service Validity Check
    db_service = repo.get_service_by_hex(sid_hex)
    std_info = STANDARD_SERVICES.get(sid)

    if not db_service and not std_info:
        issues.append(
            ValidationIssue(
                rule="RULE_SID_ISO_SUPPORT",
                reason=f"Service ID {sid_hex} is not supported by ISO 14229-1 or this ECU specification.",
                suggested_correction="Verify service ID. Supported services include 0x10, 0x11, 0x22, 0x27, 0x2E, 0x31.",
                source_evidence="ISO 14229-1 Service Table & Synthetic Spec",
                severity="ERROR"
            )
        )
        return ValidationResult(
            status=ValidationStatus.INVALID,
            request_hex=request_hex,
            service_id_hex=sid_hex,
            issues=issues,
            expected_nrc="0x11 (ServiceNotSupported)",
            expected_response_hex=f"7F {sid:02X} 11"
        )

    # 2. Check Service Session Prerequisite
    if db_service:
        required_session = db_service.session_prereq
        if required_session == "ExtendedDiagnosticSession" and active_session == "DefaultSession":
            issues.append(
                ValidationIssue(
                    rule="RULE_SESSION_PREREQUISITE",
                    reason=f"Service {db_service.name} ({sid_hex}) requires {required_session}, but current active session is {active_session}.",
                    suggested_correction="Send 0x10 0x03 to transition to Extended Diagnostic Session before invoking this service.",
                    source_evidence=f"Synthetic Spec Section for {db_service.name}",
                    severity="WARNING"
                )
            )

        # Check Service Security Prerequisite
        required_security = db_service.security_prereq
        if required_security == "Level1Unlocked" and active_security != "Level1Unlocked":
            issues.append(
                ValidationIssue(
                    rule="RULE_SECURITY_PREREQUISITE",
                    reason=f"Service {db_service.name} ({sid_hex}) requires Security Access Level 1, but ECU is currently {active_security}.",
                    suggested_correction="Perform SecurityAccess handshake (0x27 0x01 / 0x27 0x02) to unlock Level 1.",
                    source_evidence=f"Synthetic Spec Section for {db_service.name}",
                    severity="WARNING"
                )
            )

    # 3. Subfunction & Length Checks
    subfunction_hex = None
    has_subfunction = False
    if db_service and db_service.subfunctions:
        has_subfunction = True
    elif std_info and std_info["has_subfunc"]:
        has_subfunction = True

    is_suppress_pos_rsp = False

    if has_subfunction:
        if req_len < 2:
            issues.append(
                ValidationIssue(
                    rule="RULE_SUBFUNC_REQUIRED",
                    reason=f"Service {sid_hex} requires a subfunction byte, but only {req_len} byte was provided.",
                    suggested_correction=f"Add subfunction parameter (e.g., {sid_hex} 01).",
                    source_evidence="ISO 14229-1 Request Syntax",
                    severity="ERROR"
                )
            )
            return ValidationResult(
                status=ValidationStatus.INVALID,
                request_hex=request_hex,
                service_id_hex=sid_hex,
                issues=issues,
                expected_nrc="0x13 (IncorrectMessageLengthOrInvalidFormat)",
                expected_response_hex=f"7F {sid:02X} 13"
            )

        subfunction_byte = raw_bytes[1]
        is_suppress_pos_rsp = bool(subfunction_byte & 0x80)
        pure_subfunc = subfunction_byte & 0x7F
        subfunction_hex = f"0x{pure_subfunc:02X}"

        # Check if subfunction is valid for this service
        if db_service:
            valid_subfuncs = {sf.subfunction_hex.upper(): sf for sf in db_service.subfunctions}
            if subfunction_hex.upper() not in valid_subfuncs:
                issues.append(
                    ValidationIssue(
                        rule="RULE_SUBFUNC_SUPPORT",
                        reason=f"Subfunction {subfunction_hex} is not supported for service {sid_hex} in this ECU.",
                        suggested_correction=f"Supported subfunctions are: {list(valid_subfuncs.keys())}.",
                        source_evidence=f"Synthetic Spec Section for {db_service.name}",
                        severity="ERROR"
                    )
                )
            else:
                matched_sf = valid_subfuncs[subfunction_hex.upper()]
                if matched_sf.session_prereq == "ExtendedDiagnosticSession" and active_session == "DefaultSession":
                    issues.append(
                        ValidationIssue(
                            rule="RULE_SESSION_PREREQUISITE",
                            reason=f"Subfunction {matched_sf.name} ({subfunction_hex}) requires ExtendedDiagnosticSession.",
                            suggested_correction="Switch to Extended Session (10 03) first.",
                            source_evidence=f"Synthetic Spec Section for {db_service.name}",
                            severity="WARNING"
                        )
                    )
                if matched_sf.security_prereq == "Level1Unlocked" and active_security != "Level1Unlocked":
                    issues.append(
                        ValidationIssue(
                            rule="RULE_SECURITY_PREREQUISITE",
                            reason=f"Subfunction {matched_sf.name} ({subfunction_hex}) requires Level 1 security.",
                            suggested_correction="Unlock Level 1 security access (0x27 0x01 / 0x27 0x02) first.",
                            source_evidence=f"Synthetic Spec Section for {db_service.name}",
                            severity="WARNING"
                        )
                    )

        # Environmental condition checks (e.g. Programming Session requires vehicle speed == 0)
        if sid == 0x10 and pure_subfunc == 0x02 and simulated_vehicle_speed > 0:
            issues.append(
                ValidationIssue(
                    rule="RULE_PARAM_RANGE",
                    reason=f"Programming Session (0x10 0x02) rejected: Vehicle Speed is {simulated_vehicle_speed} km/h (must be 0.0).",
                    suggested_correction="Ensure simulated vehicle is stationary (Speed = 0 km/h) before requesting programming session.",
                    source_evidence="Synthetic Spec Section 2 (NRC 0x22 ConditionsNotCorrect)",
                    severity="ERROR"
                )
            )

    # 4. Service-Specific Payload & DID Parameter Validations
    if sid == 0x10:
        if req_len != 2:
            issues.append(
                ValidationIssue(
                    rule="RULE_PAYLOAD_LENGTH",
                    reason=f"DiagnosticSessionControl requires exactly 2 bytes (SID + Subfunction), got {req_len}.",
                    suggested_correction="Trim payload to 2 bytes, e.g. '10 01' or '10 03'.",
                    source_evidence="ISO 14229-1 Section 9",
                    severity="ERROR"
                )
            )

    elif sid == 0x11:
        if req_len != 2:
            issues.append(
                ValidationIssue(
                    rule="RULE_PAYLOAD_LENGTH",
                    reason=f"ECUReset requires exactly 2 bytes (SID + ResetType), got {req_len}.",
                    suggested_correction="Ensure format is exactly '11 01' or '11 03'.",
                    source_evidence="ISO 14229-1 Section 10",
                    severity="ERROR"
                )
            )

    elif sid == 0x22:  # ReadDataByIdentifier
        if req_len < 3:
            issues.append(
                ValidationIssue(
                    rule="RULE_PAYLOAD_LENGTH",
                    reason="ReadDataByIdentifier (0x22) requires a 2-byte DID (minimum 3 bytes total).",
                    suggested_correction="Provide a valid 2-byte DID, e.g., '22 F1 90'.",
                    source_evidence="ISO 14229-1 Section 11",
                    severity="ERROR"
                )
            )
        elif (req_len - 1) % 2 != 0:
            issues.append(
                ValidationIssue(
                    rule="RULE_PAYLOAD_LENGTH",
                    reason="DIDs must be formatted as pairs of 2 bytes.",
                    suggested_correction="Ensure all DIDs have exactly 2 bytes (e.g. 22 01 00).",
                    source_evidence="ISO 14229-1 Section 11",
                    severity="ERROR"
                )
            )
        else:
            did_hex = f"0x{raw_bytes[1]:02X}{raw_bytes[2]:02X}".upper()
            valid_dids = {"0XF190", "0X0100", "0X0200", "0X0300"}
            if db_service and db_service.parameters:
                for p in db_service.parameters:
                    if p.did_hex:
                        valid_dids.add(p.did_hex.strip().upper())
            if did_hex not in valid_dids:
                issues.append(
                    ValidationIssue(
                        rule="RULE_DID_SUPPORT",
                        reason=f"DID {did_hex} is not recognized by the ECU specification.",
                        suggested_correction=f"Supported DIDs: {sorted(list(valid_dids))}.",
                        source_evidence="Synthetic Spec Section 4 (ReadDataByIdentifier)",
                        severity="ERROR"
                    )
                )

    elif sid == 0x27:  # SecurityAccess
        if len(raw_bytes) >= 2:
            sf_byte = raw_bytes[1] & 0x7F
            if sf_byte == 0x01 and req_len != 2:
                issues.append(
                    ValidationIssue(
                        rule="RULE_PAYLOAD_LENGTH",
                        reason="RequestSeed (0x27 0x01) must be exactly 2 bytes.",
                        suggested_correction="Remove excess bytes: '27 01'.",
                        source_evidence="Synthetic Spec Section 5",
                        severity="ERROR"
                    )
                )
            elif sf_byte == 0x02 and req_len != 6:
                issues.append(
                    ValidationIssue(
                        rule="RULE_PAYLOAD_LENGTH",
                        reason=f"SendKey (0x27 0x02) requires exactly 4 key bytes (6 bytes total), got {req_len}.",
                        suggested_correction="Supply 4 key bytes, e.g. '27 02 6F D1 49 35'.",
                        source_evidence="Synthetic Spec Section 5",
                        severity="ERROR"
                    )
                )

    elif sid == 0x2E:  # WriteDataByIdentifier
        if req_len < 4:
            issues.append(
                ValidationIssue(
                    rule="RULE_PAYLOAD_LENGTH",
                    reason="WriteDataByIdentifier requires at least 4 bytes (SID + 2-byte DID + Data).",
                    suggested_correction="Include DID and data bytes (e.g., 2E 01 05 01 01 00 AA).",
                    source_evidence="Synthetic Spec Section 6",
                    severity="ERROR"
                )
            )
        else:
            did_hex = f"0x{raw_bytes[1]:02X}{raw_bytes[2]:02X}".upper()
            if did_hex == "0X0105": # Variant Coding (4 bytes data: Region, Lighting, TrailerMode, Checksum)
                if req_len != 7:
                    issues.append(
                        ValidationIssue(
                            rule="RULE_PAYLOAD_LENGTH",
                            reason=f"VariantCoding DID 0x0105 requires exactly 4 data bytes (7 bytes total), got {req_len}.",
                            suggested_correction="Format frame as: 2E 01 05 [Region] [Lighting] [Trailer] [Checksum].",
                            source_evidence="Synthetic Spec Section 6",
                            severity="ERROR"
                        )
                    )
                else:
                    # Check ranges
                    region_byte = raw_bytes[3]
                    lighting_byte = raw_bytes[4]
                    trailer_byte = raw_bytes[5]
                    if region_byte not in [1, 2, 3]:
                        issues.append(
                            ValidationIssue(
                                rule="RULE_PARAM_RANGE",
                                reason=f"Region parameter 0x{region_byte:02X} out of range (Allowed: 0x01 NA, 0x02 EU, 0x03 ASIA).",
                                suggested_correction="Set Byte 1 to 0x01, 0x02, or 0x03.",
                                source_evidence="Synthetic Spec Section 6",
                                severity="ERROR"
                            )
                        )
                    if lighting_byte not in [0, 1]:
                        issues.append(
                            ValidationIssue(
                                rule="RULE_PARAM_RANGE",
                                reason=f"Lighting parameter 0x{lighting_byte:02X} out of range (Allowed: 0x00 Halogen, 0x01 LED).",
                                suggested_correction="Set Byte 2 to 0x00 or 0x01.",
                                source_evidence="Synthetic Spec Section 6",
                                severity="ERROR"
                            )
                        )
                    if trailer_byte not in [0, 1]:
                        issues.append(
                            ValidationIssue(
                                rule="RULE_PARAM_RANGE",
                                reason=f"TrailerMode parameter 0x{trailer_byte:02X} out of range (Allowed: 0x00 Disabled, 0x01 Enabled).",
                                suggested_correction="Set Byte 3 to 0x00 or 0x01.",
                                source_evidence="Synthetic Spec Section 6",
                                severity="ERROR"
                            )
                        )

    # 5. Determine Overall Verdict
    has_error = any(iss.severity == "ERROR" for iss in issues)
    has_warning = any(iss.severity == "WARNING" for iss in issues)

    if not issues:
        status = ValidationStatus.VALID
        if is_suppress_pos_rsp:
            expected_response = "[Positive Response Suppressed (SPRB active)]"
        else:
            expected_response = f"{(sid + 0x40):02X} ..."
        expected_nrc = None
    elif has_warning and not has_error:
        status = ValidationStatus.REQUIRES_REVIEW
        expected_nrc = "0x7E, 0x7F, or 0x33"
        expected_response = f"7F {sid:02X} [NRC]"
    else:
        status = ValidationStatus.INVALID
        # Check specific expected NRC
        if any(iss.rule == "RULE_SID_ISO_SUPPORT" for iss in issues):
            expected_nrc = "0x11 (ServiceNotSupported)"
        elif any(iss.rule in ["RULE_SUBFUNC_REQUIRED", "RULE_PAYLOAD_LENGTH"] for iss in issues):
            expected_nrc = "0x13 (IncorrectMessageLengthOrInvalidFormat)"
        elif any(iss.rule == "RULE_SUBFUNC_SUPPORT" for iss in issues):
            expected_nrc = "0x12 (SubFunctionNotSupported)"
        elif any(iss.rule in ["RULE_DID_SUPPORT", "RULE_PARAM_RANGE"] for iss in issues):
            expected_nrc = "0x31 (RequestOutOfRange)"
        else:
            expected_nrc = "0x10 (GeneralReject)"
        expected_response = f"7F {sid:02X} {expected_nrc.split()[0]}"

    return ValidationResult(
        status=status,
        request_hex=request_hex,
        service_id_hex=sid_hex,
        subfunction_hex=subfunction_hex,
        issues=issues,
        expected_response_hex=expected_response,
        expected_nrc=expected_nrc,
        source_evidence="ISO 14229-1 & Synthetic BCM Diagnostic Specification"
    )
