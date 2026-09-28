from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.graph.traceability_engine import TraceabilityGraphEngine

router = APIRouter(prefix="/api/traceability", tags=["Traceability Graph"])

class Node(BaseModel):
    id: str
    label: str
    type: str
    metadata: Optional[Dict[str, Any]] = None

class Edge(BaseModel):
    source: str
    target: str
    relation: str

class GraphResponse(BaseModel):
    engine: str
    nodes: List[Node]
    edges: List[Edge]
    statistics: Dict[str, Any]

class LineageResponse(BaseModel):
    found: bool
    node_id: str
    node_type: Optional[str] = None
    label: Optional[str] = None
    upstream_count: int
    downstream_count: int
    upstream: List[str]
    downstream: List[str]
    direct_parents: List[str]
    direct_children: List[str]

class OrphansResponse(BaseModel):
    uncovered_requirements_count: int
    uncovered_requirements: List[Dict[str, Any]]
    orphan_tests_count: int
    orphan_tests: List[Dict[str, Any]]
    unverified_services_count: int
    unverified_services: List[Dict[str, Any]]

@router.get("/graph", response_model=GraphResponse)
def get_traceability_graph():
    engine = TraceabilityGraphEngine()
    topo = engine.get_topology()
    return GraphResponse(
        engine=topo["engine"],
        nodes=[Node(**n) for n in topo["nodes"]],
        edges=[Edge(**e) for e in topo["edges"]],
        statistics=topo["statistics"]
    )

@router.get("/lineage/{node_id}", response_model=LineageResponse)
def get_node_lineage(node_id: str):
    engine = TraceabilityGraphEngine()
    lin = engine.get_lineage(node_id)
    if not lin["found"]:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found in traceability graph.")
    return LineageResponse(**lin)

@router.get("/orphans", response_model=OrphansResponse)
def get_orphans():
    engine = TraceabilityGraphEngine()
    return engine.get_orphans()

@router.get("/matrix")
def get_traceability_matrix():
    engine = TraceabilityGraphEngine()
    return engine.get_matrix()
