import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.testing.generator import generate_diagnostic_tests, TestCaseDefinition
from app.database.repository import DiagRepository

client = TestClient(app)

MANDATORY_17_FIELDS = [
    "test_id", "objective", "requirement_id", "service_id_hex", "subfunction_hex",
    "preconditions", "session", "security_state", "request_hex", "expected_response_hex",
    "pass_criteria", "fail_criteria", "test_type", "source_evidence",
    "generation_rationale", "confidence", "review_status"
]

def test_direct_generator_dimensions_and_fields():
    """Verify that generate_diagnostic_tests generates all 6 dimensions with 17 mandatory fields starting in PENDING_REVIEW."""
    tests = generate_diagnostic_tests(
        prompt="Generate full test suite for DiagnosticSessionControl 0x10",
        target_service_hex="0x10",
        requested_types=["POSITIVE", "NEGATIVE", "BOUNDARY", "SESSION", "SECURITY", "INVALID_PARAM"],
        persist=False
    )
    assert len(tests) >= 5
    generated_types = {t.test_type for t in tests}
    assert "POSITIVE" in generated_types
    assert "NEGATIVE" in generated_types

    for t in tests:
        t_dict = t.model_dump()
        for field in MANDATORY_17_FIELDS:
            assert field in t_dict, f"Missing mandatory field '{field}' in test case {t.test_id}"
        # Mandatory Human Review Rule: All AI tests must start in PENDING_REVIEW
        assert t.review_status == "PENDING_REVIEW"
        assert t.confidence >= 0.8
        assert len(t.source_evidence) > 0
        assert len(t.request_hex) > 0
        assert len(t.expected_response_hex) > 0

def test_api_generate_tests_endpoint():
    """Test POST /api/tests/generate endpoint returns 200 and valid schema."""
    payload = {
        "prompt": "Generate complete verification test cases for ReadDataByIdentifier 0x22",
        "target_service_hex": "0x22",
        "requested_types": ["POSITIVE", "NEGATIVE", "SESSION", "SECURITY"],
        "persist": True
    }
    res = client.post("/api/tests/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    first = data[0]
    for field in MANDATORY_17_FIELDS:
        assert field in first, f"Missing '{field}' in generated test response"
    assert first["review_status"] == "PENDING_REVIEW"

def test_api_list_tests_with_filters():
    """Test GET /api/tests with filtering by review_status and test_type."""
    res = client.get("/api/tests")
    assert res.status_code == 200
    all_tests = res.json()
    assert len(all_tests) > 0

    # Filter by PENDING_REVIEW
    res_pending = client.get("/api/tests?review_status=PENDING_REVIEW")
    assert res_pending.status_code == 200
    pending_tests = res_pending.json()
    assert all(t["review_status"] == "PENDING_REVIEW" for t in pending_tests)

    # Filter by POSITIVE
    res_pos = client.get("/api/tests?test_type=POSITIVE")
    assert res_pos.status_code == 200
    pos_tests = res_pos.json()
    assert all(t["test_type"] == "POSITIVE" for t in pos_tests)

def test_api_get_single_test():
    """Test GET /api/tests/{test_id} retrieves correct test case."""
    # List to get existing ID
    res = client.get("/api/tests")
    all_tests = res.json()
    target_id = all_tests[0]["test_id"]

    res_single = client.get(f"/api/tests/{target_id}")
    assert res_single.status_code == 200
    data = res_single.json()
    assert data["test_id"] == target_id

def test_api_update_and_review_workflow():
    """Test PUT /api/tests/{test_id} edit and POST /api/tests/{test_id}/review approval flow."""
    repo = DiagRepository()
    dummy = repo.add_test_case({
        "test_id": "TC-PH4-UNIT-01",
        "objective": "Initial objective for phase 4 test",
        "service_id_hex": "0x22",
        "request_hex": "22 F1 90",
        "expected_response_hex": "62 F1 90 44 45 4D",
        "pass_criteria": "Positive response with VIN",
        "fail_criteria": "NRC received",
        "test_type": "POSITIVE",
        "source_evidence": "synthetic_bcm_diag_spec_v1_1.md",
        "review_status": "PENDING_REVIEW"
    })

    # 1. Update test case details
    update_payload = {
        "objective": "Updated objective with engineering review",
        "pass_criteria": "Positive response matching VIN bytes exactly"
    }
    res_update = client.put(f"/api/tests/{dummy.test_id}", json=update_payload)
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["objective"] == "Updated objective with engineering review"
    assert updated_data["version"] >= 2

    # 2. Human review sign-off: Approve
    review_payload = {
        "reviewer": "senior_diagnostics_lead",
        "decision": "APPROVED",
        "comment": "Protocol requirements verified against specification"
    }
    res_rev = client.post(f"/api/tests/{dummy.test_id}/review", json=review_payload)
    assert res_rev.status_code == 200

    # 3. Check updated review status
    res_check = client.get(f"/api/tests/{dummy.test_id}")
    assert res_check.status_code == 200
    assert res_check.json()["review_status"] == "APPROVED"

    # 4. Clean up / delete test case
    res_del = client.delete(f"/api/tests/{dummy.test_id}")
    assert res_del.status_code == 200

    # Verify deleted
    res_del_check = client.get(f"/api/tests/{dummy.test_id}")
    assert res_del_check.status_code == 404
