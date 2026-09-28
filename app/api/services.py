from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database.repository import DiagRepository

router = APIRouter(prefix="/api/services", tags=["UDS Services"])

class SubfunctionModel(BaseModel):
    id: int
    subfunction_hex: str
    name: str
    description: Optional[str] = None
    session_prereq: str
    security_prereq: str

class ParameterModel(BaseModel):
    id: int
    param_name: str
    did_hex: Optional[str] = None
    byte_position: int
    length_bytes: int
    data_type: str
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    description: Optional[str] = None

class ServiceDetailModel(BaseModel):
    id: int
    service_id_hex: str
    name: str
    description: Optional[str] = None
    standard_ref: str
    session_prereq: str
    security_prereq: str
    positive_response_sid_hex: Optional[str] = None
    subfunctions: List[SubfunctionModel] = []
    parameters: List[ParameterModel] = []

@router.get("", response_model=List[ServiceDetailModel])
def list_services():
    repo = DiagRepository()
    services = repo.get_services()
    result = []
    for s in services:
        result.append(
            ServiceDetailModel(
                id=s.id,
                service_id_hex=s.service_id_hex,
                name=s.name,
                description=s.description,
                standard_ref=s.standard_ref,
                session_prereq=s.session_prereq,
                security_prereq=s.security_prereq,
                positive_response_sid_hex=s.positive_response_sid_hex,
                subfunctions=[
                    SubfunctionModel(
                        id=sf.id,
                        subfunction_hex=sf.subfunction_hex,
                        name=sf.name,
                        description=sf.description,
                        session_prereq=sf.session_prereq,
                        security_prereq=sf.security_prereq
                    )
                    for sf in s.subfunctions
                ],
                parameters=[
                    ParameterModel(
                        id=p.id,
                        param_name=p.param_name,
                        did_hex=p.did_hex,
                        byte_position=p.byte_position,
                        length_bytes=p.length_bytes,
                        data_type=p.data_type,
                        min_value=p.min_value,
                        max_value=p.max_value,
                        description=p.description
                    )
                    for p in s.parameters
                ]
            )
        )
    return result

@router.get("/{service_hex}/coverage")
def get_service_coverage(service_hex: str):
    repo = DiagRepository()
    clean_hex = service_hex.strip().upper()
    if not clean_hex.startswith("0X"):
        clean_hex = "0X" + clean_hex

    s = repo.get_service_by_hex(clean_hex)
    if not s:
        raise HTTPException(status_code=404, detail=f"Service {service_hex} not found")

    all_tests = repo.get_test_cases()
    service_tests = [t for t in all_tests if t.service_id_hex.upper() == clean_hex]

    pos_tests = sum(1 for t in service_tests if t.test_type == "POSITIVE")
    neg_tests = sum(1 for t in service_tests if t.test_type == "NEGATIVE")
    bnd_tests = sum(1 for t in service_tests if t.test_type == "BOUNDARY")
    sec_tests = sum(1 for t in service_tests if t.test_type == "SECURITY")
    approved = sum(1 for t in service_tests if t.review_status == "APPROVED")

    return {
        "service_hex": clean_hex,
        "name": s.name,
        "total_tests": len(service_tests),
        "positive_tests": pos_tests,
        "negative_tests": neg_tests,
        "boundary_tests": bnd_tests,
        "security_tests": sec_tests,
        "approved_tests": approved,
        "test_cases": [
            {
                "test_id": t.test_id,
                "objective": t.objective,
                "test_type": t.test_type,
                "review_status": t.review_status,
                "request_hex": t.request_hex,
                "expected_response_hex": t.expected_response_hex
            }
            for t in service_tests
        ]
    }

@router.get("/{service_hex}", response_model=ServiceDetailModel)
def get_service_by_hex(service_hex: str):
    repo = DiagRepository()
    s = repo.get_service_by_hex(service_hex)
    if not s:
        raise HTTPException(status_code=404, detail=f"UDS Service {service_hex} not found")
    return ServiceDetailModel(
        id=s.id,
        service_id_hex=s.service_id_hex,
        name=s.name,
        description=s.description,
        standard_ref=s.standard_ref,
        session_prereq=s.session_prereq,
        security_prereq=s.security_prereq,
        positive_response_sid_hex=s.positive_response_sid_hex,
        subfunctions=[
            SubfunctionModel(
                id=sf.id,
                subfunction_hex=sf.subfunction_hex,
                name=sf.name,
                description=sf.description,
                session_prereq=sf.session_prereq,
                security_prereq=sf.security_prereq
            )
            for sf in s.subfunctions
        ],
        parameters=[
            ParameterModel(
                id=p.id,
                param_name=p.param_name,
                did_hex=p.did_hex,
                byte_position=p.byte_position,
                length_bytes=p.length_bytes,
                data_type=p.data_type,
                min_value=p.min_value,
                max_value=p.max_value,
                description=p.description
            )
            for p in s.parameters
        ]
    )
