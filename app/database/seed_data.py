import os
import json
import datetime
from app.database.repository import SessionLocal, init_db, DiagRepository
from app.database.models import (
    Document, Service, Subfunction, Parameter, Requirement,
    TestCase, TestResult, Review, Coverage, Traceability,
    SpecificationVersion, User, AuditLog
)

def seed_database():
    init_db()
    session = SessionLocal()
    repo = DiagRepository(session)

    try:
        # Check if already seeded
        if session.query(Service).count() > 0:
            print("[INFO] Database already contains services. Skipping seed.")
            return

        print("[INFO] Seeding DiagGenAI database with synthetic demonstration data...")

        # 1. Users
        user1 = User(username="lead_engineer", email="lead@automotive.local", role="Diagnostic_Engineer")
        user2 = User(username="quality_reviewer", email="qa@automotive.local", role="Reviewer")
        session.add_all([user1, user2])
        session.flush()

        # 2. Specification Versions & Documents
        doc_v1 = Document(
            name="Synthetic BCM Diagnostic Specification v1.0",
            version="1.0",
            doc_type="ECU",
            status="INDEXED",
            file_path="data/sample_specs/synthetic_bcm_diag_spec_v1.md",
            section="Complete Specification",
            metadata_json=json.dumps({
                "ecu": "Body Control Module (BCM)",
                "classification": "SYNTHETIC DEMONSTRATION DATA — NOT AN OEM SPECIFICATION",
                "standard": "ISO 14229-1"
            })
        )
        doc_v1_1 = Document(
            name="Synthetic BCM Diagnostic Specification v1.1",
            version="1.1",
            doc_type="ECU",
            status="INDEXED",
            file_path="data/sample_specs/synthetic_bcm_diag_spec_v1_1.md",
            section="Complete Specification",
            metadata_json=json.dumps({
                "ecu": "Body Control Module (BCM)",
                "classification": "SYNTHETIC DEMONSTRATION DATA — NOT AN OEM SPECIFICATION",
                "standard": "ISO 14229-1"
            })
        )
        session.add_all([doc_v1, doc_v1_1])
        session.flush()

        spec_ver1 = SpecificationVersion(
            spec_name="BCM Diagnostic Specification",
            version="1.0",
            file_path=doc_v1.file_path,
            active=True
        )
        spec_ver2 = SpecificationVersion(
            spec_name="BCM Diagnostic Specification",
            version="1.1",
            file_path=doc_v1_1.file_path,
            active=False
        )
        session.add_all([spec_ver1, spec_ver2])
        session.flush()

        # 3. Services
        s10 = Service(
            service_id_hex="0x10",
            name="DiagnosticSessionControl",
            description="Controls diagnostic session transitions (Default, Programming, Extended)",
            standard_ref="ISO 14229-1:2020",
            session_prereq="DefaultSession",
            security_prereq="None",
            positive_response_sid_hex="0x50"
        )
        s11 = Service(
            service_id_hex="0x11",
            name="ECUReset",
            description="Commands ECU restart (HardReset or SoftReset)",
            standard_ref="ISO 14229-1:2020",
            session_prereq="DefaultSession",
            security_prereq="None",
            positive_response_sid_hex="0x51"
        )
        s22 = Service(
            service_id_hex="0x22",
            name="ReadDataByIdentifier",
            description="Requests data record values from ECU by DID",
            standard_ref="ISO 14229-1:2020",
            session_prereq="DefaultSession",
            security_prereq="None",
            positive_response_sid_hex="0x62"
        )
        s27 = Service(
            service_id_hex="0x27",
            name="SecurityAccess",
            description="Performs challenge-response handshake to unlock secured diagnostic features",
            standard_ref="ISO 14229-1:2020",
            session_prereq="ExtendedDiagnosticSession",
            security_prereq="Locked",
            positive_response_sid_hex="0x67"
        )
        s2E = Service(
            service_id_hex="0x2E",
            name="WriteDataByIdentifier",
            description="Writes data record values to ECU by DID",
            standard_ref="ISO 14229-1:2020",
            session_prereq="ExtendedDiagnosticSession",
            security_prereq="Level1Unlocked",
            positive_response_sid_hex="0x6E"
        )
        s31 = Service(
            service_id_hex="0x31",
            name="RoutineControl",
            description="Starts, stops, or requests results of internal ECU self-tests",
            standard_ref="ISO 14229-1:2020",
            session_prereq="ExtendedDiagnosticSession",
            security_prereq="None",
            positive_response_sid_hex="0x71"
        )
        session.add_all([s10, s11, s22, s27, s2E, s31])
        session.flush()

        # 4. Subfunctions
        subfuncs = [
            # 0x10
            Subfunction(service_id=s10.id, subfunction_hex="0x01", name="DefaultSession", description="Transition to default session", session_prereq="DefaultSession", security_prereq="None"),
            Subfunction(service_id=s10.id, subfunction_hex="0x02", name="ProgrammingSession", description="Transition to flashing/programming session", session_prereq="ExtendedDiagnosticSession", security_prereq="Level1Unlocked"),
            Subfunction(service_id=s10.id, subfunction_hex="0x03", name="ExtendedDiagnosticSession", description="Transition to extended diagnostic session", session_prereq="DefaultSession", security_prereq="None"),
            # 0x11
            Subfunction(service_id=s11.id, subfunction_hex="0x01", name="HardReset", description="Performs hardware reset", session_prereq="DefaultSession", security_prereq="None"),
            Subfunction(service_id=s11.id, subfunction_hex="0x03", name="SoftReset", description="Performs software reset", session_prereq="DefaultSession", security_prereq="None"),
            # 0x27
            Subfunction(service_id=s27.id, subfunction_hex="0x01", name="RequestSeed_L1", description="Requests 4-byte seed for Level 1 access", session_prereq="ExtendedDiagnosticSession", security_prereq="Locked"),
            Subfunction(service_id=s27.id, subfunction_hex="0x02", name="SendKey_L1", description="Sends 4-byte computed key for Level 1 access", session_prereq="ExtendedDiagnosticSession", security_prereq="Locked"),
            # 0x31
            Subfunction(service_id=s31.id, subfunction_hex="0x01", name="StartRoutine", description="Starts specified routine", session_prereq="ExtendedDiagnosticSession", security_prereq="None"),
            Subfunction(service_id=s31.id, subfunction_hex="0x03", name="RequestRoutineResults", description="Requests routine execution results", session_prereq="ExtendedDiagnosticSession", security_prereq="None"),
        ]
        session.add_all(subfuncs)
        session.flush()

        # 5. Parameters & DIDs
        params = [
            # 0x22 DIDs
            Parameter(service_id=s22.id, param_name="VIN", byte_position=2, length_bytes=17, data_type="ASCII", did_hex="0xF190", description="Vehicle Identification Number"),
            Parameter(service_id=s22.id, param_name="EngineSpeed", byte_position=2, length_bytes=2, data_type="UINT16", min_value="0", max_value="16000", did_hex="0x0100", description="Simulated Engine Speed (0.25 rpm/bit)"),
            Parameter(service_id=s22.id, param_name="VehicleSpeed", byte_position=2, length_bytes=2, data_type="UINT16", min_value="0", max_value="25000", did_hex="0x0200", description="Simulated Vehicle Speed (0.01 km/h/bit)"),
            Parameter(service_id=s22.id, param_name="BatteryVoltage", byte_position=2, length_bytes=2, data_type="UINT16", min_value="8000", max_value="18000", did_hex="0x0300", description="Simulated Battery Voltage (0.001 V/bit)"),
            # 0x2E DIDs
            Parameter(service_id=s2E.id, param_name="VariantCoding", byte_position=2, length_bytes=4, data_type="HEX", did_hex="0x0105", description="BCM Variant Coding parameters"),
            # 0x31 Routine
            Parameter(service_id=s31.id, param_name="SelfTestRoutine", byte_position=3, length_bytes=2, data_type="HEX", did_hex="0x0201", description="BCM Self Test Routine ID"),
        ]
        session.add_all(params)
        session.flush()

        # 6. Requirements
        reqs = [
            Requirement(
                req_id="REQ-UDS-001",
                document_id=doc_v1.id,
                service_id=s10.id,
                title="Default Diagnostic Session Transition",
                description="The BCM shall support transition to DefaultSession (0x01) from any session with positive response 0x50 0x01 0x00 0x32 0x01 0xF4.",
                category="Session",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 2"
            ),
            Requirement(
                req_id="REQ-UDS-002",
                document_id=doc_v1.id,
                service_id=s10.id,
                title="Extended Diagnostic Session Transition",
                description="The BCM shall support transition to ExtendedDiagnosticSession (0x03) when in DefaultSession.",
                category="Session",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 2"
            ),
            Requirement(
                req_id="REQ-UDS-003",
                document_id=doc_v1.id,
                service_id=s10.id,
                title="Invalid Subfunction NRC 0x12 for Service 0x10",
                description="If an unsupported subfunction is requested on service 0x10, the BCM shall respond with NRC 0x12 (SubFunctionNotSupported).",
                category="Negative",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 2"
            ),
            Requirement(
                req_id="REQ-UDS-004",
                document_id=doc_v1.id,
                service_id=s22.id,
                title="Read VIN Data Identifier 0xF190",
                description="The BCM shall return the 17-byte ASCII VIN data record when queried with DID 0xF190 in Default or Extended session.",
                category="Functional",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 4"
            ),
            Requirement(
                req_id="REQ-UDS-005",
                document_id=doc_v1.id,
                service_id=s22.id,
                title="Unsupported DID Handling NRC 0x31",
                description="If a request is received for an undefined DID under service 0x22, the BCM shall return NRC 0x31 (RequestOutOfRange).",
                category="Negative",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 4"
            ),
            Requirement(
                req_id="REQ-UDS-006",
                document_id=doc_v1.id,
                service_id=s27.id,
                title="Security Access Seed Request",
                description="The BCM shall provide a non-zero 4-byte random seed when queried with 0x27 0x01 in ExtendedDiagnosticSession.",
                category="Security",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 5"
            ),
            Requirement(
                req_id="REQ-UDS-007",
                document_id=doc_v1.id,
                service_id=s27.id,
                title="Security Access Key Verification",
                description="The BCM shall unlock Security Level 1 upon receiving the valid 4-byte key matching Seed XOR 0x55AA55AA.",
                category="Security",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 5"
            ),
            Requirement(
                req_id="REQ-UDS-008",
                document_id=doc_v1.id,
                service_id=s27.id,
                title="Invalid Security Key NRC 0x35",
                description="If an incorrect key is provided with 0x27 0x02, the BCM shall reject the request with NRC 0x35 (InvalidKey).",
                category="Security",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 5"
            ),
            Requirement(
                req_id="REQ-UDS-009",
                document_id=doc_v1.id,
                service_id=s2E.id,
                title="Write Variant Coding Protected by Security Level 1",
                description="The BCM shall allow writing 4 bytes to DID 0x0105 only when in ExtendedSession and Security Level 1 is unlocked.",
                category="Functional",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 6"
            ),
            Requirement(
                req_id="REQ-UDS-010",
                document_id=doc_v1.id,
                service_id=s2E.id,
                title="Write Variant Coding Security Denial NRC 0x33",
                description="If 0x2E 0x0105 is attempted while Security Level 1 is locked, the BCM shall return NRC 0x33 (SecurityAccessDenied).",
                category="Negative",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 6"
            ),
            Requirement(
                req_id="REQ-UDS-011",
                document_id=doc_v1.id,
                service_id=s31.id,
                title="Start Self Test Routine 0x0201",
                description="The BCM shall start routine 0x0201 in ExtendedDiagnosticSession and return positive response 0x71 0x01 0x02 0x01 0x00.",
                category="Functional",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 7"
            ),
            Requirement(
                req_id="REQ-UDS-012",
                document_id=doc_v1.id,
                service_id=s11.id,
                title="ECU Hard Reset Execution",
                description="The BCM shall acknowledge HardReset (0x11 0x01) with 0x51 0x01 and reboot into DefaultSession.",
                category="Functional",
                verification_method="Test",
                source_doc="synthetic_bcm_diag_spec_v1.md",
                source_section="Section 3"
            ),
        ]
        session.add_all(reqs)
        session.flush()

        # 7. Initial Test Cases
        tcs = [
            TestCase(
                test_id="TC-UDS-001",
                objective="Verify transition to Extended Diagnostic Session (0x10 0x03)",
                requirement_id="REQ-UDS-002",
                service_id_hex="0x10",
                subfunction_hex="0x03",
                preconditions="ECU powered, Default Session active",
                session="DefaultSession",
                security_state="Locked",
                request_hex="10 03",
                expected_response_hex="50 03 00 32 01 F4",
                pass_criteria="Positive response 0x50 0x03 received with valid timing parameters",
                fail_criteria="NRC received or no response within P2 timeout",
                test_type="POSITIVE",
                source_evidence="synthetic_bcm_diag_spec_v1.md Section 2",
                generation_rationale="Verifies standard session switch prerequisite for diagnostic routines",
                confidence=0.98,
                review_status="APPROVED",
                version=1
            ),
            TestCase(
                test_id="TC-UDS-002",
                objective="Verify rejection of unsupported subfunction 0x09 on Service 0x10",
                requirement_id="REQ-UDS-003",
                service_id_hex="0x10",
                subfunction_hex="0x09",
                preconditions="ECU powered",
                session="DefaultSession",
                security_state="Locked",
                request_hex="10 09",
                expected_response_hex="7F 10 12",
                pass_criteria="Negative response received with NRC 0x12 (SubFunctionNotSupported)",
                fail_criteria="Positive response or unexpected NRC",
                test_type="NEGATIVE",
                source_evidence="synthetic_bcm_diag_spec_v1.md Section 2 NRC Handling",
                generation_rationale="Negative protocol robustness test for invalid subfunction",
                confidence=0.95,
                review_status="APPROVED",
                version=1
            ),
            TestCase(
                test_id="TC-UDS-003",
                objective="Verify reading Vehicle Identification Number (VIN) DID 0xF190",
                requirement_id="REQ-UDS-004",
                service_id_hex="0x22",
                subfunction_hex=None,
                preconditions="ECU in DefaultSession",
                session="DefaultSession",
                security_state="Locked",
                request_hex="22 F1 90",
                expected_response_hex="62 F1 90 44 45 4D 4F 56 49 4E 31 32 33 34 35 36 37 38 39 30",
                pass_criteria="Response starts with 62 F1 90 followed by 17 ASCII bytes",
                fail_criteria="NRC received or length not 20 bytes",
                test_type="POSITIVE",
                source_evidence="synthetic_bcm_diag_spec_v1.md Section 4",
                generation_rationale="Verifies readable identification data according to ISO standard DID",
                confidence=0.99,
                review_status="APPROVED",
                version=1
            ),
            TestCase(
                test_id="TC-UDS-004",
                objective="Verify reading unsupported DID 0xFFFF yields NRC 0x31",
                requirement_id="REQ-UDS-005",
                service_id_hex="0x22",
                subfunction_hex=None,
                preconditions="ECU in DefaultSession",
                session="DefaultSession",
                security_state="Locked",
                request_hex="22 FF FF",
                expected_response_hex="7F 22 31",
                pass_criteria="Negative response with NRC 0x31 (RequestOutOfRange)",
                fail_criteria="Positive response or unexpected NRC",
                test_type="NEGATIVE",
                source_evidence="synthetic_bcm_diag_spec_v1.md Section 4 NRC Handling",
                generation_rationale="Negative boundary test for non-existent DID identifier",
                confidence=0.97,
                review_status="APPROVED",
                version=1
            ),
            TestCase(
                test_id="TC-UDS-005",
                objective="Verify Security Access Seed Request (0x27 0x01) in Extended Session",
                requirement_id="REQ-UDS-006",
                service_id_hex="0x27",
                subfunction_hex="0x01",
                preconditions="ECU in ExtendedDiagnosticSession",
                session="ExtendedDiagnosticSession",
                security_state="Locked",
                request_hex="27 01",
                expected_response_hex="67 01 3A 7B 1C 9F",
                pass_criteria="Positive response 0x67 0x01 with 4-byte seed",
                fail_criteria="NRC received or seed length != 4 bytes",
                test_type="SECURITY",
                source_evidence="synthetic_bcm_diag_spec_v1.md Section 5",
                generation_rationale="Validates security access challenge generation",
                confidence=0.96,
                review_status="APPROVED",
                version=1
            ),
            TestCase(
                test_id="TC-UDS-006",
                objective="Verify Writing Variant Coding is rejected when Security Access is Locked (NRC 0x33)",
                requirement_id="REQ-UDS-010",
                service_id_hex="0x2E",
                subfunction_hex=None,
                preconditions="ECU in ExtendedDiagnosticSession, Security Locked",
                session="ExtendedDiagnosticSession",
                security_state="Locked",
                request_hex="2E 01 05 01 01 00 AA",
                expected_response_hex="7F 2E 33",
                pass_criteria="Negative response with NRC 0x33 (SecurityAccessDenied)",
                fail_criteria="Write succeeded or unexpected NRC returned",
                test_type="SECURITY",
                source_evidence="synthetic_bcm_diag_spec_v1.md Section 6",
                generation_rationale="Ensures safety-critical parameters cannot be overwritten without authentication",
                confidence=0.97,
                review_status="PENDING_REVIEW",
                version=1
            ),
            TestCase(
                test_id="TC-UDS-007",
                objective="Verify Battery Voltage DID 0x0300 Upper Boundary (18.000V)",
                requirement_id="REQ-UDS-004",
                service_id_hex="0x22",
                subfunction_hex=None,
                preconditions="ECU powered, battery input configured to upper threshold",
                session="DefaultSession",
                security_state="Locked",
                request_hex="22 03 00",
                expected_response_hex="62 03 00 46 50",
                pass_criteria="Positive response with voltage within 8000-18000 mV range",
                fail_criteria="NRC or voltage reading out of specification range",
                test_type="BOUNDARY",
                source_evidence="synthetic_bcm_diag_spec_v1.md Section 4",
                generation_rationale="Boundary validation for analog sensor range measurement",
                confidence=0.93,
                review_status="PENDING_REVIEW",
                version=1
            ),
        ]
        session.add_all(tcs)
        session.flush()

        # 8. Initial Reviews
        rev1 = Review(
            test_case_id=tcs[0].id,
            reviewer="lead_engineer",
            decision="APPROVED",
            comment="Verified against ISO 14229-1:2020 and synthetic spec v1.0",
            test_version=1
        )
        rev2 = Review(
            test_case_id=tcs[1].id,
            reviewer="lead_engineer",
            decision="APPROVED",
            comment="Negative NRC 0x12 expected response confirmed",
            test_version=1
        )
        rev3 = Review(
            test_case_id=tcs[2].id,
            reviewer="quality_reviewer",
            decision="APPROVED",
            comment="VIN DID format matches standard 17-char ASCII string",
            test_version=1
        )
        session.add_all([rev1, rev2, rev3])
        session.flush()

        # 9. Traceability Links
        trace_links = [
            Traceability(source_type="Requirement", source_id="REQ-UDS-001", target_type="Service", target_id="0x10", relation_type="IMPLEMENTED_IN"),
            Traceability(source_type="Requirement", source_id="REQ-UDS-002", target_type="Service", target_id="0x10", relation_type="IMPLEMENTED_IN"),
            Traceability(source_type="Requirement", source_id="REQ-UDS-002", target_type="TestCase", target_id="TC-UDS-001", relation_type="VERIFIED_BY"),
            Traceability(source_type="Requirement", source_id="REQ-UDS-003", target_type="TestCase", target_id="TC-UDS-002", relation_type="VERIFIED_BY"),
            Traceability(source_type="Requirement", source_id="REQ-UDS-004", target_type="Service", target_id="0x22", relation_type="IMPLEMENTED_IN"),
            Traceability(source_type="Requirement", source_id="REQ-UDS-004", target_type="TestCase", target_id="TC-UDS-003", relation_type="VERIFIED_BY"),
            Traceability(source_type="Requirement", source_id="REQ-UDS-005", target_type="TestCase", target_id="TC-UDS-004", relation_type="VERIFIED_BY"),
            Traceability(source_type="Requirement", source_id="REQ-UDS-006", target_type="TestCase", target_id="TC-UDS-005", relation_type="VERIFIED_BY"),
            Traceability(source_type="Requirement", source_id="REQ-UDS-010", target_type="TestCase", target_id="TC-UDS-006", relation_type="VERIFIED_BY"),
        ]
        session.add_all(trace_links)
        session.flush()

        # 10. Initial Test Simulation Results
        res1 = TestResult(
            test_case_id=tcs[0].id,
            request_sent_hex="10 03",
            expected_response_hex="50 03 00 32 01 F4",
            actual_response_hex="50 03 00 32 01 F4",
            outcome="PASS",
            diff_analysis="None - exact byte match",
            explanation="Potential explanation based on simulated behavior: BCM simulator accepted session transition and replied with positive response.",
            execution_mode="SIMULATION MODE — NO REAL ECU CONNECTION"
        )
        res2 = TestResult(
            test_case_id=tcs[1].id,
            request_sent_hex="10 09",
            expected_response_hex="7F 10 12",
            actual_response_hex="7F 10 12",
            outcome="PASS",
            diff_analysis="None - exact NRC match",
            explanation="Potential explanation based on simulated behavior: Simulator identified unsupported subfunction 0x09 and returned standard NRC 0x12.",
            execution_mode="SIMULATION MODE — NO REAL ECU CONNECTION"
        )
        res3 = TestResult(
            test_case_id=tcs[2].id,
            request_sent_hex="22 F1 90",
            expected_response_hex="62 F1 90 44 45 4D 4F 56 49 4E 31 32 33 34 35 36 37 38 39 30",
            actual_response_hex="62 F1 90 44 45 4D 4F 56 49 4E 31 32 33 34 35 36 37 38 39 30",
            outcome="PASS",
            diff_analysis="None - exact VIN match",
            explanation="Potential explanation based on simulated behavior: Synthetic DID 0xF190 successfully retrieved.",
            execution_mode="SIMULATION MODE — NO REAL ECU CONNECTION"
        )
        session.add_all([res1, res2, res3])
        session.flush()

        # 11. Initial Coverage
        cov = Coverage(
            req_coverage=58.3,
            service_coverage=83.3,
            subfunction_coverage=66.7,
            positive_coverage=71.4,
            negative_coverage=57.1,
            session_coverage=60.0,
            security_coverage=50.0,
            boundary_coverage=33.3,
            gaps_json=json.dumps([
                {
                    "missing_scenario": "Service 0x31 Routine 0x0201 Stop/Results in Default Session",
                    "reason": "Missing negative test verifying NRC 0x7E when routine is stopped without extended session",
                    "evidence": "synthetic_bcm_diag_spec_v1.md Section 7",
                    "suggested_test": "Send 31 02 02 01 in DefaultSession -> Expect 7F 31 7E"
                },
                {
                    "missing_scenario": "Service 0x27 SendKey sequence error test",
                    "reason": "Missing negative test verifying NRC 0x24 when SendKey is called before RequestSeed",
                    "evidence": "synthetic_bcm_diag_spec_v1.md Section 5",
                    "suggested_test": "Send 27 02 12 34 56 78 without prior seed -> Expect 7F 27 24"
                },
                {
                    "missing_scenario": "Service 0x11 ECUReset SoftReset (0x11 0x03)",
                    "reason": "Missing positive test for SoftReset subfunction execution",
                    "evidence": "synthetic_bcm_diag_spec_v1.md Section 3",
                    "suggested_test": "Send 11 03 in DefaultSession -> Expect 51 03"
                }
            ])
        )
        session.add(cov)
        session.flush()

        # 12. Audit Logs
        session.add(AuditLog(
            user="system",
            action="SYSTEM_INITIALIZE",
            entity_type="System",
            entity_id="DiagGenAI",
            details="Database initialized with Synthetic Demonstration Data (Simulation Mode active)"
        ))

        session.commit()
        print("[SUCCESS] DiagGenAI database successfully seeded.")
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
