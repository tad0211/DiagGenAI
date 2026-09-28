import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.repository import SessionLocal, DiagRepository, init_db
from app.database.seed_data import seed_database
from app.database.models import Service, Requirement, TestCase, Document
from app.uds.request_builder import build_uds_request
from app.uds.models import UDSRequestBuildInput
from app.uds.validator import validate_uds_request

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()
    seed_database()

def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "SIMULATION MODE" in data["mode"]
    assert data["db"] == "sqlite"

def test_info_endpoint():
    res = client.get("/api/info")
    assert res.status_code == 200
    data = res.json()
    assert data["app_name"] == "DiagGenAI"
    assert data["vector_db"] == "ChromaDB"

def test_database_seeded_data():
    session = SessionLocal()
    try:
        service_count = session.query(Service).count()
        assert service_count >= 6  # 0x10, 0x11, 0x22, 0x27, 0x2E, 0x31

        req_count = session.query(Requirement).count()
        assert req_count >= 10

        test_count = session.query(TestCase).count()
        assert test_count >= 6

        doc_count = session.query(Document).count()
        assert doc_count >= 2
    finally:
        session.close()

def test_request_builder():
    build_input = UDSRequestBuildInput(
        service_id_hex="0x22",
        did_hex="0xF190",
        session="DefaultSession",
        security_state="Locked"
    )
    result = build_uds_request(build_input)
    assert result.request_hex == "22 F1 90"
    assert "62 F1 90" in result.expected_response
    assert "DefaultSession" in result.preconditions

def test_deterministic_validator_valid():
    # Valid Read VIN
    res = validate_uds_request("22 F1 90", active_session="DefaultSession", active_security="Locked")
    assert res.status.value == "VALID"
    assert len(res.issues) == 0

def test_deterministic_validator_unsupported_service():
    # Service 0x99 is not in ISO 14229 or spec
    res = validate_uds_request("99 01", active_session="DefaultSession", active_security="Locked")
    assert res.status.value == "INVALID"
    assert res.expected_nrc == "0x11 (ServiceNotSupported)"
    assert any(i.rule in ["RULE_SID_ISO_SUPPORT", "ISO_14229_SERVICE_SUPPORT"] for i in res.issues)

def test_deterministic_validator_session_prerequisite():
    # Write DID (0x2E) in DefaultSession should require review / session switch
    res = validate_uds_request("2E 01 05 01 01 00 AA", active_session="DefaultSession", active_security="Locked")
    assert res.status.value in ["INVALID", "REQUIRES REVIEW"]
    assert any("SESSION" in i.rule for i in res.issues)

def test_mock_ecu_simulation():
    # 1. Read VIN
    res = client.post("/api/simulator/send", json={"request_hex": "22 F1 90", "active_session": "DefaultSession"})
    assert res.status_code == 200
    data = res.json()
    assert data["response_type"] == "POSITIVE"
    assert "62 F1 90" in data["response_hex"]

    # 2. Unsupported Subfunction on 0x10 -> NRC 0x12
    res2 = client.post("/api/simulator/send", json={"request_hex": "10 99", "active_session": "DefaultSession"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["response_type"] == "NEGATIVE"
    assert data2["response_hex"] == "7F 10 12"

    # 3. Fault Injection: Timeout
    res3 = client.post("/api/simulator/send", json={"request_hex": "22 F1 90", "inject_fault": "TIMEOUT"})
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["response_type"] == "TIMEOUT"

def test_coverage_and_reports_endpoints():
    cov_res = client.get("/api/coverage")
    assert cov_res.status_code == 200
    cov = cov_res.json()
    assert cov["service_coverage"] > 0

    rep_res = client.get("/api/reports/engineering")
    assert rep_res.status_code == 200
    assert "DiagGenAI" in rep_res.text
    assert "SIMULATION MODE" in rep_res.text
