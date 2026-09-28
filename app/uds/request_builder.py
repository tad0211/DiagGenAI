from typing import List, Optional
from app.uds.models import UDSRequestBuildInput, UDSRequestBuildOutput
from app.uds.rules import clean_hex_string, format_hex_bytes, STANDARD_SERVICES
from app.database.repository import DiagRepository

def build_uds_request(input_data: UDSRequestBuildInput) -> UDSRequestBuildOutput:
    repo = DiagRepository()
    sid_clean = clean_hex_string(input_data.service_id_hex)
    if not sid_clean:
        sid_clean = "22"
    sid_int = int(sid_clean[:2], 16)

    tokens = [f"{sid_int:02X}"]

    # Check database service definition
    db_service = repo.get_service_by_hex(f"0x{sid_clean}")
    service_name = db_service.name if db_service else STANDARD_SERVICES.get(sid_int, {}).get("name", "UnknownService")

    # Add Subfunction if present
    subfunc_str = ""
    if input_data.subfunction_hex:
        sf_clean = clean_hex_string(input_data.subfunction_hex)
        if sf_clean:
            sf_byte = f"{int(sf_clean[:2], 16):02X}"
            tokens.append(sf_byte)
            subfunc_str = f"Subfunction 0x{sf_byte}"

    # Add DID if present
    if input_data.did_hex:
        did_clean = clean_hex_string(input_data.did_hex)
        if len(did_clean) == 4:
            tokens.append(did_clean[0:2])
            tokens.append(did_clean[2:4])
        elif len(did_clean) == 2:
            tokens.append("F1")
            tokens.append(did_clean)

    # Add extra payload parameters
    if input_data.parameters_hex:
        params_clean = clean_hex_string(input_data.parameters_hex)
        for i in range(0, len(params_clean), 2):
            tokens.append(params_clean[i:i+2])

    request_hex = " ".join(tokens)

    # Expected Positive Response
    pos_sid = f"{(sid_int + 0x40):02X}"
    if sid_int == 0x10:
        pos_rsp = f"50 {tokens[1] if len(tokens) > 1 else '01'} 00 32 01 F4"
    elif sid_int == 0x11:
        pos_rsp = f"51 {tokens[1] if len(tokens) > 1 else '01'}"
    elif sid_int == 0x22:
        did_part = " ".join(tokens[1:]) if len(tokens) > 1 else "F1 90"
        pos_rsp = f"62 {did_part} [DATA]"
    elif sid_int == 0x27:
        if len(tokens) > 1 and tokens[1] == "01":
            pos_rsp = "67 01 3A 7B 1C 9F"
        else:
            pos_rsp = "67 02"
    elif sid_int == 0x2E:
        did_part = " ".join(tokens[1:3]) if len(tokens) > 2 else "01 05"
        pos_rsp = f"6E {did_part}"
    elif sid_int == 0x31:
        routine_part = " ".join(tokens[1:]) if len(tokens) > 1 else "01 02 01"
        pos_rsp = f"71 {routine_part} 00"
    else:
        pos_rsp = f"{pos_sid} ..."

    preconditions = f"ECU Powered; Active Session: {input_data.session}; Security State: {input_data.security_state}"
    source_evidence = f"ISO 14229-1:2020 & Synthetic BCM Spec Section for Service 0x{sid_int:02X}"
    explanation = f"Structured UDS request for service {service_name} (0x{sid_int:02X}) assembled with {len(tokens)} bytes payload."

    return UDSRequestBuildOutput(
        request_hex=request_hex,
        formatted_bytes=tokens,
        preconditions=preconditions,
        expected_response=pos_rsp,
        source_evidence=source_evidence,
        explanation=explanation
    )
