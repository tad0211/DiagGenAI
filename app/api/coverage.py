import json
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.database.repository import DiagRepository
from app.testing.coverage_analyzer import CoverageAnalyzer

router = APIRouter(prefix="/api/coverage", tags=["Coverage"])

class CoverageResponse(BaseModel):
    req_coverage: float
    service_coverage: float
    subfunction_coverage: float
    positive_coverage: float
    negative_coverage: float
    session_coverage: float
    security_coverage: float
    boundary_coverage: float
    gaps: List[Dict[str, Any]] = []
    service_matrix: Optional[List[Dict[str, Any]]] = None
    total_requirements: Optional[int] = None
    covered_requirements: Optional[int] = None
    total_services: Optional[int] = None
    covered_services: Optional[int] = None
    total_subfunctions: Optional[int] = None
    covered_subfunctions: Optional[int] = None
    total_test_cases: Optional[int] = None

class GenerateMissingRequest(BaseModel):
    gap_ids: Optional[List[str]] = None

@router.get("", response_model=CoverageResponse)
def get_coverage():
    analyzer = CoverageAnalyzer()
    repo = DiagRepository()
    cov = repo.get_latest_coverage()
    if not cov:
        # compute fresh
        res = analyzer.analyze_coverage(persist=True)
        return CoverageResponse(**res)

    # Return latest snapshot supplemented with dynamic service matrix
    dynamic = analyzer.analyze_coverage(persist=False)
    return CoverageResponse(
        req_coverage=cov.req_coverage,
        service_coverage=cov.service_coverage,
        subfunction_coverage=cov.subfunction_coverage,
        positive_coverage=cov.positive_coverage,
        negative_coverage=cov.negative_coverage,
        session_coverage=cov.session_coverage,
        security_coverage=cov.security_coverage,
        boundary_coverage=cov.boundary_coverage,
        gaps=json.loads(cov.gaps_json or "[]"),
        service_matrix=dynamic.get("service_matrix", []),
        total_requirements=dynamic.get("total_requirements"),
        covered_requirements=dynamic.get("covered_requirements"),
        total_services=dynamic.get("total_services"),
        covered_services=dynamic.get("covered_services"),
        total_subfunctions=dynamic.get("total_subfunctions"),
        covered_subfunctions=dynamic.get("covered_subfunctions"),
        total_test_cases=dynamic.get("total_test_cases")
    )

@router.post("/analyze", response_model=CoverageResponse)
def analyze_coverage_endpoint():
    analyzer = CoverageAnalyzer()
    res = analyzer.analyze_coverage(persist=True)
    return CoverageResponse(**res)

@router.post("/generate-missing")
def generate_missing_tests_endpoint(payload: Optional[GenerateMissingRequest] = None):
    analyzer = CoverageAnalyzer()
    gap_ids = payload.gap_ids if payload else None
    result = analyzer.generate_missing_tests(gap_ids=gap_ids)
    return {
        "status": "success",
        "created_count": result["created_tests_count"],
        "created_tests": result["created_tests"],
        "updated_coverage": result["updated_coverage"]
    }
