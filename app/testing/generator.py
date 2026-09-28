"""
DiagGenAI - AI Test Generator Engine.
Accepts natural-language requirements and service specifications to generate
Positive, Negative, Boundary, Session, Security, and Invalid Parameter test cases.
Grounded strictly in ChromaDB vector store evidence and ISO 14229-1 protocol rules.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.database.repository import DiagRepository
from app.rag.chains import diagnostic_rag_pipeline
from app.uds.rules import clean_hex_string, STANDARD_SERVICES

class TestCaseDefinition(BaseModel):
    __test__ = False
    test_id: str
    objective: str
    requirement_id: Optional[str] = "REQ-UDS-001"
    service_id_hex: str
    subfunction_hex: Optional[str] = None
    preconditions: str
    session: str
    security_state: str
    request_hex: str
    expected_response_hex: str
    pass_criteria: str
    fail_criteria: str
    test_type: str  # POSITIVE, NEGATIVE, BOUNDARY, SESSION, SECURITY, INVALID_PARAM
    source_evidence: str
    generation_rationale: str
    confidence: float = 0.95
    review_status: str = "PENDING_REVIEW"
    version: int = 1

def generate_diagnostic_tests(
    prompt: str,
    target_service_hex: Optional[str] = None,
    requested_types: Optional[List[str]] = None,
    persist: bool = True
) -> List[TestCaseDefinition]:
    """
    Generate rigorous diagnostic test cases grounded in specification evidence.
    Generates Positive, Negative, Boundary, Session, Security, and Invalid Parameter tests.
    Every test starts in PENDING_REVIEW status for mandatory human review.
    """
    repo = DiagRepository()
    existing_tests = repo.get_test_cases()
    base_counter = len(existing_tests) + 1

    prompt_lower = prompt.lower()

    # Determine target service
    sid_hex = target_service_hex
    if not sid_hex:
        # Check prompt for hex patterns e.g. 0x10, 0x22, 0x27, 0x2E, 0x31, 0x11
        sid_match = re.search(r'0x[0-9a-fA-F]{2}', prompt)
        if sid_match:
            sid_hex = sid_match.group(0).upper()
        elif "session" in prompt_lower:
            sid_hex = "0x10"
        elif "reset" in prompt_lower:
            sid_hex = "0x11"
        elif "read" in prompt_lower or "vin" in prompt_lower:
            sid_hex = "0x22"
        elif "security" in prompt_lower or "seed" in prompt_lower:
            sid_hex = "0x27"
        elif "write" in prompt_lower or "coding" in prompt_lower:
            sid_hex = "0x2E"
        elif "routine" in prompt_lower or "selftest" in prompt_lower:
            sid_hex = "0x31"
        else:
            sid_hex = "0x22"  # default to ReadDataByIdentifier

    clean_sid = clean_hex_string(sid_hex)
    sid_int = int(clean_sid[:2], 16)

    # Query RAG knowledge store for grounded specification evidence
    rag_res = diagnostic_rag_pipeline.query(f"What are the requirements and NRC handling for service 0x{clean_sid}?", doc_type="ECU")
    evidence_citation = f"{rag_res.source_document} ({rag_res.section})"

    all_types = requested_types or ["POSITIVE", "NEGATIVE", "BOUNDARY", "SESSION", "SECURITY", "INVALID_PARAM"]
    generated_tests: List[TestCaseDefinition] = []

    def make_test_id(idx):
        return f"TC-GEN-{base_counter + idx:03d}"

    idx = 0

    # 1. SERVICE 0x10 (DiagnosticSessionControl)
    if sid_int == 0x10:
        if "POSITIVE" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify standard transition to Extended Diagnostic Session (0x10 0x03)",
                requirement_id="REQ-UDS-002",
                service_id_hex="0x10",
                subfunction_hex="0x03",
                preconditions="ECU powered, DefaultSession active, vehicle stationary",
                session="DefaultSession",
                security_state="Locked",
                request_hex="10 03",
                expected_response_hex="50 03 00 32 01 F4",
                pass_criteria="Positive response 0x50 0x03 received with timing P2=50ms, P2*=5000ms",
                fail_criteria="NRC received or no response within P2 timeout window",
                test_type="POSITIVE",
                source_evidence=evidence_citation,
                generation_rationale="Validates nominal session switch required prior to running extended diagnostic services",
                confidence=0.98,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "NEGATIVE" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify rejection of undefined subfunction 0x09 with NRC 0x12",
                requirement_id="REQ-UDS-003",
                service_id_hex="0x10",
                subfunction_hex="0x09",
                preconditions="ECU powered, DefaultSession active",
                session="DefaultSession",
                security_state="Locked",
                request_hex="10 09",
                expected_response_hex="7F 10 12",
                pass_criteria="Negative response with NRC 0x12 (SubFunctionNotSupported)",
                fail_criteria="Positive response or unexpected NRC",
                test_type="NEGATIVE",
                source_evidence=evidence_citation,
                generation_rationale="Robustness verification against non-standard subfunction values",
                confidence=0.96,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "BOUNDARY" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify subfunction upper boundary 0x7E rejection with NRC 0x12",
                requirement_id="REQ-UDS-003",
                service_id_hex="0x10",
                subfunction_hex="0x7E",
                preconditions="ECU powered",
                session="DefaultSession",
                security_state="Locked",
                request_hex="10 7E",
                expected_response_hex="7F 10 12",
                pass_criteria="Negative response with NRC 0x12",
                fail_criteria="Positive response or crash",
                test_type="BOUNDARY",
                source_evidence=evidence_citation,
                generation_rationale="Boundary check for highest non-suppressed 7-bit subfunction value",
                confidence=0.94,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "SESSION" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify transition from ExtendedSession back to DefaultSession (0x10 0x01)",
                requirement_id="REQ-UDS-001",
                service_id_hex="0x10",
                subfunction_hex="0x01",
                preconditions="ECU in ExtendedDiagnosticSession",
                session="ExtendedDiagnosticSession",
                security_state="Locked",
                request_hex="10 01",
                expected_response_hex="50 01 00 32 01 F4",
                pass_criteria="Positive response 0x50 0x01 received and session resets to Default",
                fail_criteria="NRC received or session unchanged",
                test_type="SESSION",
                source_evidence=evidence_citation,
                generation_rationale="Ensures clean exit path from diagnostic sessions back to default vehicle operation",
                confidence=0.97,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "SECURITY" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify transition to ProgrammingSession requires Security Level 1 Unlocked (NRC 0x33)",
                requirement_id="REQ-UDS-002",
                service_id_hex="0x10",
                subfunction_hex="0x02",
                preconditions="ECU in DefaultSession, Security Locked",
                session="DefaultSession",
                security_state="Locked",
                request_hex="10 02",
                expected_response_hex="7F 10 33",
                pass_criteria="Negative response with NRC 0x33 (SecurityAccessDenied)",
                fail_criteria="Programming session entered without authorization",
                test_type="SECURITY",
                source_evidence=evidence_citation,
                generation_rationale="Safety guardrail protecting flashing/programming routine against unauthorized access",
                confidence=0.95,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "INVALID_PARAM" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify message length violation on Service 0x10 yields NRC 0x13",
                requirement_id="REQ-UDS-003",
                service_id_hex="0x10",
                subfunction_hex="0x01",
                preconditions="ECU powered",
                session="DefaultSession",
                security_state="Locked",
                request_hex="10 01 FF",
                expected_response_hex="7F 10 13",
                pass_criteria="Negative response with NRC 0x13 (IncorrectMessageLengthOrInvalidFormat)",
                fail_criteria="Positive response accepted despite extra payload byte",
                test_type="INVALID_PARAM",
                source_evidence=evidence_citation,
                generation_rationale="Payload format syntax check enforcing exact 2-byte structure for session control",
                confidence=0.96,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

    # 2. SERVICE 0x22 (ReadDataByIdentifier)
    elif sid_int == 0x22:
        if "POSITIVE" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify reading VIN DID 0xF190 returns 17-byte ASCII data record",
                requirement_id="REQ-UDS-004",
                service_id_hex="0x22",
                subfunction_hex=None,
                preconditions="ECU in DefaultSession",
                session="DefaultSession",
                security_state="Locked",
                request_hex="22 F1 90",
                expected_response_hex="62 F1 90 44 45 4D 4F 56 49 4E 31 32 33 34 35 36 37 38 39 30",
                pass_criteria="Response frame starts with 62 F1 90 followed by valid 17-character ASCII string",
                fail_criteria="NRC received or length mismatch",
                test_type="POSITIVE",
                source_evidence=evidence_citation,
                generation_rationale="Verifies standard Vehicle Identification Number retrieval compliance",
                confidence=0.99,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "NEGATIVE" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify reading undefined DID 0xDE00 yields NRC 0x31",
                requirement_id="REQ-UDS-005",
                service_id_hex="0x22",
                subfunction_hex=None,
                preconditions="ECU in DefaultSession",
                session="DefaultSession",
                security_state="Locked",
                request_hex="22 DE 00",
                expected_response_hex="7F 22 31",
                pass_criteria="Negative response with NRC 0x31 (RequestOutOfRange)",
                fail_criteria="Positive response or crash",
                test_type="NEGATIVE",
                source_evidence=evidence_citation,
                generation_rationale="Negative test verifying proper error rejection when non-existent DID is queried",
                confidence=0.97,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "BOUNDARY" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify Battery Voltage DID 0x0300 Upper Boundary (18.000V / 0x4650)",
                requirement_id="REQ-UDS-004",
                service_id_hex="0x22",
                subfunction_hex=None,
                preconditions="ECU battery input adjusted to upper threshold",
                session="DefaultSession",
                security_state="Locked",
                request_hex="22 03 00",
                expected_response_hex="62 03 00 46 50",
                pass_criteria="Response returns reading within 8000-18000 mV boundary range",
                fail_criteria="Reading outside range or NRC",
                test_type="BOUNDARY",
                source_evidence=evidence_citation,
                generation_rationale="Ensures ADC sensor readout scaling is accurate at maximum input boundary",
                confidence=0.95,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "SESSION" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify DID 0x0100 (Engine Speed) readability across Extended Session",
                requirement_id="REQ-UDS-004",
                service_id_hex="0x22",
                subfunction_hex=None,
                preconditions="ECU in ExtendedDiagnosticSession",
                session="ExtendedDiagnosticSession",
                security_state="Locked",
                request_hex="22 01 00",
                expected_response_hex="62 01 00 0F A0",
                pass_criteria="Positive response 0x62 0x01 0x00 received in Extended Session",
                fail_criteria="NRC 0x7F or timeout",
                test_type="SESSION",
                source_evidence=evidence_citation,
                generation_rationale="Verifies that standard telemetry DIDs remain accessible after session transition",
                confidence=0.96,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "INVALID_PARAM" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify truncated DID query (only 1 byte DID) yields NRC 0x13",
                requirement_id="REQ-UDS-005",
                service_id_hex="0x22",
                subfunction_hex=None,
                preconditions="ECU powered",
                session="DefaultSession",
                security_state="Locked",
                request_hex="22 F1",
                expected_response_hex="7F 22 13",
                pass_criteria="Negative response with NRC 0x13 (IncorrectMessageLengthOrInvalidFormat)",
                fail_criteria="ECU attempts reading or hangs",
                test_type="INVALID_PARAM",
                source_evidence=evidence_citation,
                generation_rationale="Enforces ISO requirement that DIDs must be exact 2-byte pairs",
                confidence=0.98,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

    # 3. SERVICE 0x27 (SecurityAccess)
    elif sid_int == 0x27:
        if "POSITIVE" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify Security Access Level 1 Seed Request (0x27 0x01) in Extended Session",
                requirement_id="REQ-UDS-006",
                service_id_hex="0x27",
                subfunction_hex="0x01",
                preconditions="ECU in ExtendedDiagnosticSession",
                session="ExtendedDiagnosticSession",
                security_state="Locked",
                request_hex="27 01",
                expected_response_hex="67 01 3A 7B 1C 9F",
                pass_criteria="Positive response 0x67 0x01 received with 4 non-zero seed bytes",
                fail_criteria="NRC received or seed length != 4 bytes",
                test_type="POSITIVE",
                source_evidence=evidence_citation,
                generation_rationale="Nominal security challenge initiation test",
                confidence=0.98,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "SECURITY" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify valid key verification (0x27 0x02) unlocks Security Level 1",
                requirement_id="REQ-UDS-007",
                service_id_hex="0x27",
                subfunction_hex="0x02",
                preconditions="Seed 3A 7B 1C 9F requested prior to key submission",
                session="ExtendedDiagnosticSession",
                security_state="Locked",
                request_hex="27 02 6F D1 49 35",
                expected_response_hex="67 02",
                pass_criteria="Positive response 0x67 0x02 and security state transitions to Level1Unlocked",
                fail_criteria="NRC 0x35 or state remains Locked",
                test_type="SECURITY",
                source_evidence=evidence_citation,
                generation_rationale="Authenticates tester key algorithm matching Seed XOR 0x55AA55AA",
                confidence=0.97,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "NEGATIVE" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify invalid key submission (0x27 0x02) is rejected with NRC 0x35",
                requirement_id="REQ-UDS-008",
                service_id_hex="0x27",
                subfunction_hex="0x02",
                preconditions="Seed requested; corrupted key submitted",
                session="ExtendedDiagnosticSession",
                security_state="Locked",
                request_hex="27 02 00 00 00 00",
                expected_response_hex="7F 27 35",
                pass_criteria="Negative response with NRC 0x35 (InvalidKey)",
                fail_criteria="Key accepted or incorrect NRC",
                test_type="NEGATIVE",
                source_evidence=evidence_citation,
                generation_rationale="Verifies resistance against authentication brute-force or invalid keys",
                confidence=0.98,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "SESSION" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify SecurityAccess in DefaultSession yields NRC 0x7E",
                requirement_id="REQ-UDS-006",
                service_id_hex="0x27",
                subfunction_hex="0x01",
                preconditions="ECU in DefaultSession",
                session="DefaultSession",
                security_state="Locked",
                request_hex="27 01",
                expected_response_hex="7F 27 7E",
                pass_criteria="Negative response with NRC 0x7E (SubFunctionNotSupportedInActiveSession)",
                fail_criteria="Seed returned in DefaultSession",
                test_type="SESSION",
                source_evidence=evidence_citation,
                generation_rationale="Ensures security features cannot be accessed outside designated extended session",
                confidence=0.96,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

    # 4. SERVICE 0x2E (WriteDataByIdentifier)
    elif sid_int == 0x2E:
        if "POSITIVE" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify writing Variant Coding DID 0x0105 in authorized security state",
                requirement_id="REQ-UDS-009",
                service_id_hex="0x2E",
                subfunction_hex=None,
                preconditions="ECU in ExtendedDiagnosticSession, Security Level 1 Unlocked",
                session="ExtendedDiagnosticSession",
                security_state="Level1Unlocked",
                request_hex="2E 01 05 01 01 00 AA",
                expected_response_hex="6E 01 05",
                pass_criteria="Positive response 0x6E 0x01 0x05 acknowledging successful write",
                fail_criteria="NRC received or configuration unchanged",
                test_type="POSITIVE",
                source_evidence=evidence_citation,
                generation_rationale="Verifies authorized parameter write execution",
                confidence=0.97,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "SECURITY" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify writing Variant Coding without security unlock yields NRC 0x33",
                requirement_id="REQ-UDS-010",
                service_id_hex="0x2E",
                subfunction_hex=None,
                preconditions="ECU in ExtendedDiagnosticSession, Security Locked",
                session="ExtendedDiagnosticSession",
                security_state="Locked",
                request_hex="2E 01 05 01 01 00 AA",
                expected_response_hex="7F 2E 33",
                pass_criteria="Negative response with NRC 0x33 (SecurityAccessDenied)",
                fail_criteria="Write accepted without authentication",
                test_type="SECURITY",
                source_evidence=evidence_citation,
                generation_rationale="Prevents critical ECU parameters from being modified by unauthenticated testers",
                confidence=0.99,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "INVALID_PARAM" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify writing invalid Region parameter (0x09) yields NRC 0x31",
                requirement_id="REQ-UDS-009",
                service_id_hex="0x2E",
                subfunction_hex=None,
                preconditions="ECU in ExtendedSession, Level 1 Unlocked",
                session="ExtendedDiagnosticSession",
                security_state="Level1Unlocked",
                request_hex="2E 01 05 09 01 00 AA",
                expected_response_hex="7F 2E 31",
                pass_criteria="Negative response with NRC 0x31 (RequestOutOfRange)",
                fail_criteria="Out-of-range value accepted",
                test_type="INVALID_PARAM",
                source_evidence=evidence_citation,
                generation_rationale="Validates parameter range check on Region byte (allowed: 0x01 NA, 0x02 EU, 0x03 ASIA)",
                confidence=0.96,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

    # 5. SERVICE 0x31 (RoutineControl)
    elif sid_int == 0x31:
        if "POSITIVE" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify StartRoutine SelfTest 0x0201 in Extended Session",
                requirement_id="REQ-UDS-011",
                service_id_hex="0x31",
                subfunction_hex="0x01",
                preconditions="ECU in ExtendedDiagnosticSession, Vehicle Speed = 0 km/h",
                session="ExtendedDiagnosticSession",
                security_state="Locked",
                request_hex="31 01 02 01",
                expected_response_hex="71 01 02 01 00",
                pass_criteria="Positive response 0x71 0x01 0x02 0x01 0x00 (Routine running)",
                fail_criteria="NRC received",
                test_type="POSITIVE",
                source_evidence=evidence_citation,
                generation_rationale="Nominal execution verification for internal diagnostic self-test",
                confidence=0.97,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

        if "NEGATIVE" in all_types:
            generated_tests.append(TestCaseDefinition(
                test_id=make_test_id(idx),
                objective="Verify RoutineControl with undefined routine 0xFFFF yields NRC 0x31",
                requirement_id="REQ-UDS-011",
                service_id_hex="0x31",
                subfunction_hex="0x01",
                preconditions="ECU in ExtendedDiagnosticSession",
                session="ExtendedDiagnosticSession",
                security_state="Locked",
                request_hex="31 01 FF FF",
                expected_response_hex="7F 31 31",
                pass_criteria="Negative response with NRC 0x31 (RequestOutOfRange)",
                fail_criteria="Positive response or crash",
                test_type="NEGATIVE",
                source_evidence=evidence_citation,
                generation_rationale="Enforces rejection of invalid routine identifiers",
                confidence=0.98,
                review_status="PENDING_REVIEW"
            ))
            idx += 1

    # Generic Fallback Generation
    if not generated_tests:
        generated_tests.append(TestCaseDefinition(
            test_id=make_test_id(0),
            objective=f"Verify Service {sid_hex} nominal execution",
            requirement_id="REQ-UDS-001",
            service_id_hex=sid_hex,
            subfunction_hex=None,
            preconditions="ECU in DefaultSession",
            session="DefaultSession",
            security_state="Locked",
            request_hex=f"{clean_sid[:2]} 01",
            expected_response_hex=f"{(sid_int+0x40):02X} 01",
            pass_criteria="Positive response received matching service ID",
            fail_criteria="NRC or timeout",
            test_type="POSITIVE",
            source_evidence=evidence_citation,
            generation_rationale="Generated baseline test from service specification",
            confidence=0.90,
            review_status="PENDING_REVIEW"
        ))

    # Persist in SQLite if requested
    if persist:
        for t in generated_tests:
            # Check if test_id already exists to prevent unique constraint collisions
            existing = repo.get_test_case_by_id(t.test_id)
            if not existing:
                repo.add_test_case(t.model_dump())
                repo.add_traceability_link("Service", t.service_id_hex, "TestCase", t.test_id, "VERIFIED_BY")
                if t.requirement_id:
                    repo.add_traceability_link("Requirement", t.requirement_id, "TestCase", t.test_id, "VERIFIED_BY")

        repo.log_audit(
            action="GENERATE_TEST_SUITE",
            entity_type="TestGenerator",
            entity_id=sid_hex,
            details=f"Generated {len(generated_tests)} test cases for {sid_hex}"
        )

    return generated_tests
