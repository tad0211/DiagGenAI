import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.graph.traceability_engine import TraceabilityGraphEngine
from app.database.repository import DiagRepository

client = TestClient(app)

def test_traceability_engine_topology():
    engine = TraceabilityGraphEngine()
    topo = engine.get_topology()

    assert "nodes" in topo
    assert "edges" in topo
    assert len(topo["nodes"]) >= 10
    assert len(topo["edges"]) >= 5

    # Check node types
    types = topo["statistics"]["node_types"]
    assert "Requirement" in types
    assert "Service" in types
    assert "TestCase" in types

def test_traceability_engine_lineage():
    engine = TraceabilityGraphEngine()
    # Test lineage of a known requirement
    lin = engine.get_lineage("REQ-UDS-001")
    assert lin["found"] is True
    assert lin["node_id"] == "REQ-UDS-001"
    assert lin["node_type"] == "Requirement"
    # Should have upstream document
    assert lin["upstream_count"] >= 1
    # Downstream tests
    assert lin["downstream_count"] >= 1

def test_traceability_engine_orphans_and_matrix():
    engine = TraceabilityGraphEngine()
    orphans = engine.get_orphans()
    assert "uncovered_requirements_count" in orphans
    assert "orphan_tests_count" in orphans
    assert "unverified_services_count" in orphans

    matrix = engine.get_matrix()
    assert isinstance(matrix, list)
    assert len(matrix) >= 5
    first_row = matrix[0]
    assert "Requirement ID" in first_row
    assert "Verified By Tests" in first_row
    assert "Status" in first_row

def test_api_traceability_endpoints():
    # 1. Graph
    res_g = client.get("/api/traceability/graph")
    assert res_g.status_code == 200
    data_g = res_g.json()
    assert len(data_g["nodes"]) >= 10

    # 2. Lineage
    res_lin = client.get("/api/traceability/lineage/REQ-UDS-001")
    assert res_lin.status_code == 200
    data_lin = res_lin.json()
    assert data_lin["node_id"] == "REQ-UDS-001"

    # 3. Orphans
    res_orp = client.get("/api/traceability/orphans")
    assert res_orp.status_code == 200
    assert "uncovered_requirements_count" in res_orp.json()

    # 4. Matrix
    res_mat = client.get("/api/traceability/matrix")
    assert res_mat.status_code == 200
    assert len(res_mat.json()) >= 5
