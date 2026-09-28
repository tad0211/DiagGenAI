from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from app.analysis.change_impact import ChangeImpactEngine

router = APIRouter(prefix="/api/change-impact", tags=["Specification Change Impact"])

class AnalyzeImpactRequest(BaseModel):
    base_version: str = "1.0"
    target_version: str = "1.1"

class ApplyFlagsRequest(BaseModel):
    test_ids: List[str]

@router.post("/analyze")
def analyze_change_impact_endpoint(payload: Optional[AnalyzeImpactRequest] = None):
    base_ver = payload.base_version if payload else "1.0"
    target_ver = payload.target_version if payload else "1.1"
    engine = ChangeImpactEngine()
    return engine.analyze_change_impact(base_version=base_ver, target_version=target_ver)

@router.post("/apply-flags")
def apply_flags_endpoint(payload: ApplyFlagsRequest):
    engine = ChangeImpactEngine()
    return engine.apply_impact_flags(payload.test_ids)

@router.get("/intelligence")
def get_intelligence_endpoint():
    engine = ChangeImpactEngine()
    return engine.get_test_suite_intelligence()

@router.get("/versions")
def get_available_versions():
    return {
        "available_versions": [
            {"version": "1.0", "doc_name": "synthetic_bcm_diag_spec_v1.md", "status": "BASE_RELEASE"},
            {"version": "1.1", "doc_name": "synthetic_bcm_diag_spec_v1_1.md", "status": "UPDATE_RELEASE"}
        ]
    }
