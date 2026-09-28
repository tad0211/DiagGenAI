from fastapi import APIRouter, Query, Body, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.uds.models import (
    UDSRequestBuildInput, UDSRequestBuildOutput,
    ValidationResult
)
from app.uds.request_builder import build_uds_request
from app.uds.validator import validate_uds_request
from app.uds.rules import VALIDATION_RULES_REGISTRY
from app.database.repository import DiagRepository

router = APIRouter(prefix="/api/requests", tags=["UDS Requests"])

class GenerateTestFromRequestInput(BaseModel):
    request_hex: str
    service_id_hex: str
    subfunction_hex: Optional[str] = None
    session: str = "DefaultSession"
    security_state: str = "Locked"
    expected_response_hex: str
    objective: str
    requirement_id: Optional[str] = "REQ-UDS-001"
    test_type: str = "POSITIVE"

@router.post("/build", response_model=UDSRequestBuildOutput)
def build_request(input_data: UDSRequestBuildInput):
    repo = DiagRepository()
    output = build_uds_request(input_data)
    repo.log_audit("BUILD_REQUEST", "UDSRequest", output.request_hex, f"Built request for SID {input_data.service_id_hex}")
    return output

@router.post("/validate", response_model=ValidationResult)
def validate_request(
    request_hex: str = Body(..., embed=True),
    session: str = Body("DefaultSession", embed=True),
    security_state: str = Body("Locked", embed=True),
    simulated_vehicle_speed: float = Body(0.0, embed=True)
):
    repo = DiagRepository()
    result = validate_uds_request(
        request_hex,
        active_session=session,
        active_security=security_state,
        simulated_vehicle_speed=simulated_vehicle_speed
    )
    repo.log_audit("VALIDATE_REQUEST", "UDSRequest", request_hex, f"Validation status: {result.status.value}")
    return result

@router.get("/rules", response_model=Dict[str, Any])
def get_validation_rules():
    return VALIDATION_RULES_REGISTRY

@router.post("/generate-test")
def create_test_from_request(input_data: GenerateTestFromRequestInput):
    repo = DiagRepository()
    existing_tests = repo.get_test_cases()
    next_id_num = len(existing_tests) + 1
    new_test_id = f"TC-UDS-{next_id_num:03d}"

    test_data = {
        "test_id": new_test_id,
        "objective": input_data.objective,
        "requirement_id": input_data.requirement_id,
        "service_id_hex": input_data.service_id_hex,
        "subfunction_hex": input_data.subfunction_hex,
        "preconditions": f"Active Session: {input_data.session}, Security: {input_data.security_state}",
        "session": input_data.session,
        "security_state": input_data.security_state,
        "request_hex": input_data.request_hex,
        "expected_response_hex": input_data.expected_response_hex,
        "pass_criteria": f"ECU returns response starting with {input_data.expected_response_hex.split()[0]}",
        "fail_criteria": "NRC received or unexpected response",
        "test_type": input_data.test_type,
        "source_evidence": "Generated from Request Builder via Deterministic Validation",
        "generation_rationale": "Automated test case generated from engineering request frame builder",
        "confidence": 0.95,
        "review_status": "PENDING_REVIEW"
    }

    created = repo.add_test_case(test_data)
    repo.add_traceability_link("Service", input_data.service_id_hex, "TestCase", created.test_id, "VERIFIED_BY")

    return {
        "status": "success",
        "message": f"Test Case {created.test_id} successfully generated and added to review queue.",
        "test_id": created.test_id,
        "review_status": created.review_status
    }
