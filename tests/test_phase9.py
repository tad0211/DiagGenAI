import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.analysis.change_impact import ChangeImpactEngine
from app.database.repository import DiagRepository

client = TestClient(app)

def test_change_impact_engine_analysis():
    engine = ChangeImpactEngine()
    impact = engine.analyze_change_impact(base_version="1.0", target_version="1.1")

    assert impact["base_version"] == "1.0"
    assert impact["target_version"] == "1.1"
    assert impact["overall_impact_level"] in ["CRITICAL", "MAJOR"]

    # Verify added, removed, modified categories
    assert len(impact["added_features"]) >= 2
    assert len(impact["removed_features"]) >= 1
    assert len(impact["modified_parameters"]) >= 1
    assert len(impact["modified_prerequisites"]) >= 1

    # Verify impacted tests detected
    assert "impacted_tests" in impact
    assert "recommended_regression_suite" in impact
    assert "new_tests_needed" in impact
    assert len(impact["new_tests_needed"]) >= 3

def test_apply_impact_flags():
    repo = DiagRepository()
    engine = ChangeImpactEngine()

    # Create dummy test
    dummy = repo.add_test_case({
        "test_id": "TC-CI-UNIT-01",
        "objective": "Change impact unit test case",
        "service_id_hex": "0x2E",
        "request_hex": "2E 01 05 01 01 00 AA",
        "expected_response_hex": "6E 01 05",
        "pass_criteria": "Positive response",
        "fail_criteria": "NRC",
        "test_type": "POSITIVE",
        "review_status": "APPROVED"
    })

    res = engine.apply_impact_flags(["TC-CI-UNIT-01"])
    assert res["status"] == "success"
    assert res["updated_count"] == 1

    updated_tc = repo.get_test_case_by_id("TC-CI-UNIT-01")
    assert updated_tc.review_status == "REQUIRES_RETEST"

    # Cleanup
    repo.delete_test_case("TC-CI-UNIT-01")

def test_test_suite_intelligence():
    engine = ChangeImpactEngine()
    intel = engine.get_test_suite_intelligence()

    assert "total_test_cases" in intel
    assert "unique_signatures" in intel
    assert "duplicates_detected" in intel
    assert "suite_health_score" in intel
    assert intel["suite_health_score"] >= 80.0
    assert "recommendations" in intel
    assert len(intel["recommendations"]) >= 1

def test_api_change_impact_endpoints():
    # 1. Analyze
    res_an = client.post("/api/change-impact/analyze", json={"base_version": "1.0", "target_version": "1.1"})
    assert res_an.status_code == 200
    data_an = res_an.json()
    assert "overall_impact_level" in data_an
    assert len(data_an["new_tests_needed"]) >= 1

    # 2. Intelligence
    res_int = client.get("/api/change-impact/intelligence")
    assert res_int.status_code == 200
    assert "suite_health_score" in res_int.json()

    # 3. Versions
    res_ver = client.get("/api/change-impact/versions")
    assert res_ver.status_code == 200
    assert len(res_ver.json()["available_versions"]) >= 2
