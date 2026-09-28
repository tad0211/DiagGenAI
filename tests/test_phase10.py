import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_engineering_markdown_report_endpoint():
    res = client.get("/api/reports/engineering")
    assert res.status_code == 200
    text = res.text

    assert "DiagGenAI - Comprehensive Engineering Validation Report" in text
    assert "SIMULATION MODE — NO REAL ECU CONNECTION" in text
    assert "## 1. Executive Summary" in text
    assert "## 3. Services & Coverage Status" in text
    assert "## 6. Hardware-in-the-Loop (HIL) Transition Checklist" in text

def test_engineering_html_report_endpoint():
    res = client.get("/api/reports/html")
    assert res.status_code == 200
    html = res.text

    assert "<!DOCTYPE html>" in html
    assert "DiagGenAI - Comprehensive Engineering Validation Report" in html
    assert "SIMULATION MODE — NO REAL ECU CONNECTION" in html
    assert "kpi-card" in html
    assert "table" in html

def test_engineering_summary_endpoint():
    res = client.get("/api/reports/summary")
    assert res.status_code == 200
    data = res.json()

    assert "documents_indexed" in data
    assert "uds_services" in data
    assert "total_tests" in data
    assert "coverage" in data
    assert data["total_tests"] >= 1
