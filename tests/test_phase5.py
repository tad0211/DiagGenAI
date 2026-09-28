import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.testing.coverage_analyzer import CoverageAnalyzer
from app.database.repository import DiagRepository

client = TestClient(app)

MANDATORY_17_FIELDS = [
    "test_id", "objective", "requirement_id", "service_id_hex", "subfunction_hex",
    "preconditions", "session", "security_state", "request_hex", "expected_response_hex",
    "pass_criteria", "fail_criteria", "test_type", "source_evidence",
    "generation_rationale", "confidence", "review_status"
]

def test_coverage_analyzer_metrics_calculation():
    """Verify CoverageAnalyzer computes all 8 coverage dimensions with valid percentage ranges."""
    analyzer = CoverageAnalyzer()
    metrics = analyzer.analyze_coverage(persist=False)

    for dim in [
        "req_coverage", "service_coverage", "subfunction_coverage",
        "positive_coverage", "negative_coverage", "session_coverage",
        "security_coverage", "boundary_coverage"
    ]:
        assert dim in metrics, f"Missing metric dimension: {dim}"
        val = metrics[dim]
        assert isinstance(val, (int, float))
        assert 0.0 <= val <= 100.0, f"Dimension {dim} value {val} out of range 0-100"

    # Verify service matrix structure
    assert "service_matrix" in metrics
    matrix = metrics["service_matrix"]
    assert len(matrix) >= 5
    first_srv = matrix[0]
    assert "service_hex" in first_srv
    assert "subfunctions_total" in first_srv
    assert "health_score" in first_srv

def test_gap_detection_structure():
    """Verify that detected coverage gaps provide actionable protocol details and suggested frames."""
    analyzer = CoverageAnalyzer()
    metrics = analyzer.analyze_coverage(persist=False)
    gaps = metrics.get("gaps", [])

    if gaps:
        gap = gaps[0]
        assert "gap_id" in gap
        assert "service_id_hex" in gap
        assert "missing_scenario" in gap
        assert "reason" in gap
        assert "suggested_test" in gap
        assert "severity" in gap
        assert gap["severity"] in ["HIGH", "MEDIUM", "LOW"]
        assert "suggested_test_data" in gap
        assert "objective" in gap["suggested_test_data"]

def test_generate_missing_tests_closes_gaps():
    """Verify that generating missing tests creates 17-field test cases in PENDING_REVIEW and closes gaps."""
    analyzer = CoverageAnalyzer()
    initial_metrics = analyzer.analyze_coverage(persist=False)
    initial_gaps = initial_metrics.get("gaps", [])

    if initial_gaps:
        target_gap = initial_gaps[0]
        res = analyzer.generate_missing_tests(gap_ids=[target_gap["gap_id"]])

        assert res["created_tests_count"] == 1
        created = res["created_tests"][0]

        for field in MANDATORY_17_FIELDS:
            assert field in created, f"Missing field '{field}' in gap-generated test case"

        # Mandatory Safety: Must start in PENDING_REVIEW
        assert created["review_status"] == "PENDING_REVIEW"

        # Check updated coverage
        updated_cov = res["updated_coverage"]
        assert updated_cov["total_test_cases"] > initial_metrics["total_test_cases"]

def test_api_get_coverage():
    """Test GET /api/coverage endpoint."""
    res = client.get("/api/coverage")
    assert res.status_code == 200
    data = res.json()
    assert "req_coverage" in data
    assert "service_coverage" in data
    assert "subfunction_coverage" in data
    assert "gaps" in data
    assert isinstance(data["gaps"], list)

def test_api_analyze_coverage():
    """Test POST /api/coverage/analyze endpoint."""
    res = client.post("/api/coverage/analyze")
    assert res.status_code == 200
    data = res.json()
    assert data["req_coverage"] >= 0.0
    assert len(data.get("service_matrix", [])) > 0

def test_api_generate_missing_tests():
    """Test POST /api/coverage/generate-missing endpoint."""
    res = client.post("/api/coverage/generate-missing", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "created_count" in data
    assert "updated_coverage" in data
