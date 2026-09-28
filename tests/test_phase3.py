import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.uds.validator import validate_uds_request
from app.uds.request_builder import build_uds_request
from app.uds.models import UDSRequestBuildInput

client = TestClient(app)

def test_service_coverage_endpoint():
    res = client.get("/api/services/0x22/coverage")
    assert res.status_code == 200
    data = res.json()
    assert data["service_hex"] == "0X22"
    assert data["name"] == "ReadDataByIdentifier"
    assert data["total_tests"] >= 1
    assert len(data["test_cases"]) >= 1

def test_validation_rules_registry_endpoint():
    res = client.get("/api/requests/rules")
    assert res.status_code == 200
    rules = res.json()
    assert "RULE_SID_ISO_SUPPORT" in rules
    assert "RULE_SESSION_PREREQUISITE" in rules
    assert "RULE_PARAM_RANGE" in rules

def test_request_builder_suppress_bit():
    # 0x10 with suppress positive response bit (0x01 | 0x80 = 0x81)
    inp = UDSRequestBuildInput(
        service_id_hex="0x10",
        subfunction_hex="0x81",
        session="DefaultSession"
    )
    out = build_uds_request(inp)
    assert out.request_hex == "10 81"

def test_validator_parameter_range_violation():
    # 2E 01 05: Byte 1 (Region) = 0x09 (Invalid: allowed are 0x01, 0x02, 0x03)
    res = validate_uds_request(
        "2E 01 05 09 00 00 AA",
        active_session="ExtendedDiagnosticSession",
        active_security="Level1Unlocked"
    )
    assert res.status.value == "INVALID"
    assert any(iss.rule == "RULE_PARAM_RANGE" for iss in res.issues)
    assert "0x31" in (res.expected_nrc or "")

def test_validator_environmental_condition_violation():
    # 10 02 (ProgrammingSession) requested while simulated vehicle speed > 0
    res = validate_uds_request(
        "10 02",
        active_session="ExtendedDiagnosticSession",
        active_security="Level1Unlocked",
        simulated_vehicle_speed=45.0
    )
    assert res.status.value == "INVALID"
    assert any("Vehicle Speed" in iss.reason for iss in res.issues)

def test_validator_prerequisite_review():
    # Write DID in DefaultSession and Locked
    res = validate_uds_request(
        "2E 01 05 01 00 00 AA",
        active_session="DefaultSession",
        active_security="Locked"
    )
    assert res.status.value == "REQUIRES REVIEW"
    assert any(iss.rule == "RULE_SESSION_PREREQUISITE" for iss in res.issues)

def test_generate_test_from_request_builder():
    payload = {
        "request_hex": "10 01",
        "service_id_hex": "0x10",
        "subfunction_hex": "0x01",
        "session": "DefaultSession",
        "security_state": "Locked",
        "expected_response_hex": "50 01 00 32 01 F4",
        "objective": "Verify DefaultSession request from request builder",
        "requirement_id": "REQ-UDS-001",
        "test_type": "POSITIVE"
    }
    res = client.post("/api/requests/generate-test", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "TC-UDS-" in data["test_id"]
    assert data["review_status"] == "PENDING_REVIEW"
