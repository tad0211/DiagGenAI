import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.repository import DiagRepository

client = TestClient(app)

def test_generate_single_python_template():
    repo = DiagRepository()
    all_tests = repo.get_test_cases()
    assert len(all_tests) > 0
    tc = all_tests[0]

    res = client.post("/api/automation/generate", json={"test_id": tc.test_id, "template_type": "PYTHON"})
    assert res.status_code == 200
    data = res.json()
    assert data["test_id"] == tc.test_id
    assert data["template_type"] == "PYTHON"
    assert "class Test_" in data["code_content"]
    assert "can.interface.Bus" in data["code_content"]
    assert tc.request_hex.replace(" ", "") in data["code_content"]
    assert "SIMULATION MODE" in data["code_content"]

def test_generate_single_capl_template():
    repo = DiagRepository()
    tc = repo.get_test_cases()[0]

    res = client.post("/api/automation/generate", json={"test_id": tc.test_id, "template_type": "CAPL"})
    assert res.status_code == 200
    data = res.json()
    assert data["template_type"] == "CAPL"
    assert "testcase TC_" in data["code_content"]
    assert "diagSendRequest" in data["code_content"]
    assert "TestWaitForDiagResponse" in data["code_content"]

def test_generate_single_generic_and_csv_templates():
    repo = DiagRepository()
    tc = repo.get_test_cases()[0]

    # Generic YAML
    res_gen = client.post("/api/automation/generate", json={"test_id": tc.test_id, "template_type": "GENERIC"})
    assert res_gen.status_code == 200
    assert "TRANSMIT_DIAGNOSTIC_FRAME" in res_gen.json()["code_content"]

    # CSV
    res_csv = client.post("/api/automation/generate", json={"test_id": tc.test_id, "template_type": "CSV"})
    assert res_csv.status_code == 200
    assert tc.test_id in res_csv.json()["code_content"]

def test_generate_suite_python_and_csv():
    # Python PyTest Suite
    res_py = client.post("/api/automation/generate-suite", json={"template_type": "PYTHON", "service_hex": "0x10"})
    assert res_py.status_code == 200
    data_py = res_py.json()
    assert "TestDiagnosticSuite" in data_py["code_content"]
    assert "def test_" in data_py["code_content"]

    # CSV Matrix
    res_csv = client.post("/api/automation/generate-suite", json={"template_type": "CSV"})
    assert res_csv.status_code == 200
    data_csv = res_csv.json()
    assert "Test ID,Test Type,Service" in data_csv["code_content"]
