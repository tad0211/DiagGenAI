from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from app.database.repository import DiagRepository

router = APIRouter(prefix="/api/tests", tags=["Test Cases"])

class TestCaseResponse(BaseModel):
    id: int
    test_id: str
    objective: str
    requirement_id: Optional[str] = None
    service_id_hex: str
    subfunction_hex: Optional[str] = None
    preconditions: str
    session: str
    security_state: str
    request_hex: str
    expected_response_hex: str
    pass_criteria: str
    fail_criteria: str
    test_type: str
    source_evidence: str
    generation_rationale: Optional[str] = None
    confidence: float
    review_status: str
    version: int

class ReviewRequest(BaseModel):
    reviewer: str = "lead_engineer"
    decision: str = "APPROVED"  # APPROVED, REJECTED, EDITED
    comment: str = "Verified protocol parameters against spec"

class GenerateTestRequest(BaseModel):
    prompt: str
    target_service_hex: Optional[str] = None
    requested_types: Optional[List[str]] = None
    persist: bool = True

class UpdateTestCaseRequest(BaseModel):
    objective: Optional[str] = None
    preconditions: Optional[str] = None
    session: Optional[str] = None
    security_state: Optional[str] = None
    request_hex: Optional[str] = None
    expected_response_hex: Optional[str] = None
    pass_criteria: Optional[str] = None
    fail_criteria: Optional[str] = None
    test_type: Optional[str] = None
    review_status: Optional[str] = None

@router.get("", response_model=List[TestCaseResponse])
def list_tests(
    review_status: Optional[str] = Query(None),
    test_type: Optional[str] = Query(None)
):
    repo = DiagRepository()
    tcs = repo.get_test_cases(review_status=review_status, test_type=test_type)
    return [
        TestCaseResponse(
            id=tc.id,
            test_id=tc.test_id,
            objective=tc.objective,
            requirement_id=tc.requirement_id,
            service_id_hex=tc.service_id_hex,
            subfunction_hex=tc.subfunction_hex,
            preconditions=tc.preconditions,
            session=tc.session,
            security_state=tc.security_state,
            request_hex=tc.request_hex,
            expected_response_hex=tc.expected_response_hex,
            pass_criteria=tc.pass_criteria,
            fail_criteria=tc.fail_criteria,
            test_type=tc.test_type,
            source_evidence=tc.source_evidence,
            generation_rationale=tc.generation_rationale,
            confidence=tc.confidence,
            review_status=tc.review_status,
            version=tc.version
        )
        for tc in tcs
    ]

@router.get("/{test_id}", response_model=TestCaseResponse)
def get_test(test_id: str):
    repo = DiagRepository()
    tc = repo.get_test_case_by_id(test_id)
    if not tc:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")
    return TestCaseResponse(
        id=tc.id,
        test_id=tc.test_id,
        objective=tc.objective,
        requirement_id=tc.requirement_id,
        service_id_hex=tc.service_id_hex,
        subfunction_hex=tc.subfunction_hex,
        preconditions=tc.preconditions,
        session=tc.session,
        security_state=tc.security_state,
        request_hex=tc.request_hex,
        expected_response_hex=tc.expected_response_hex,
        pass_criteria=tc.pass_criteria,
        fail_criteria=tc.fail_criteria,
        test_type=tc.test_type,
        source_evidence=tc.source_evidence,
        generation_rationale=tc.generation_rationale,
        confidence=tc.confidence,
        review_status=tc.review_status,
        version=tc.version
    )

@router.post("/{test_id}/review")
def review_test(test_id: str, review: ReviewRequest):
    repo = DiagRepository()
    updated = repo.update_test_review(
        test_id=test_id,
        decision=review.decision,
        reviewer=review.reviewer,
        comment=review.comment
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Test case {test_id} not found")
    return {"status": "success", "message": f"Test case {test_id} status updated to {review.decision}"}

@router.post("/generate", response_model=List[TestCaseResponse])
def generate_tests_endpoint(payload: GenerateTestRequest):
    from app.testing.generator import generate_diagnostic_tests
    generated = generate_diagnostic_tests(
        prompt=payload.prompt,
        target_service_hex=payload.target_service_hex,
        requested_types=payload.requested_types,
        persist=payload.persist
    )
    repo = DiagRepository()
    results = []
    for g in generated:
        db_tc = repo.get_test_case_by_id(g.test_id)
        if db_tc:
            results.append(TestCaseResponse(
                id=db_tc.id,
                test_id=db_tc.test_id,
                objective=db_tc.objective,
                requirement_id=db_tc.requirement_id,
                service_id_hex=db_tc.service_id_hex,
                subfunction_hex=db_tc.subfunction_hex,
                preconditions=db_tc.preconditions,
                session=db_tc.session,
                security_state=db_tc.security_state,
                request_hex=db_tc.request_hex,
                expected_response_hex=db_tc.expected_response_hex,
                pass_criteria=db_tc.pass_criteria,
                fail_criteria=db_tc.fail_criteria,
                test_type=db_tc.test_type,
                source_evidence=db_tc.source_evidence,
                generation_rationale=db_tc.generation_rationale,
                confidence=db_tc.confidence,
                review_status=db_tc.review_status,
                version=db_tc.version
            ))
        else:
            results.append(TestCaseResponse(
                id=0,
                test_id=g.test_id,
                objective=g.objective,
                requirement_id=g.requirement_id,
                service_id_hex=g.service_id_hex,
                subfunction_hex=g.subfunction_hex,
                preconditions=g.preconditions,
                session=g.session,
                security_state=g.security_state,
                request_hex=g.request_hex,
                expected_response_hex=g.expected_response_hex,
                pass_criteria=g.pass_criteria,
                fail_criteria=g.fail_criteria,
                test_type=g.test_type,
                source_evidence=g.source_evidence,
                generation_rationale=g.generation_rationale,
                confidence=g.confidence,
                review_status=g.review_status,
                version=g.version
            ))
    return results

@router.put("/{test_id}", response_model=TestCaseResponse)
def update_test(test_id: str, payload: UpdateTestCaseRequest):
    repo = DiagRepository()
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated = repo.update_test_case(test_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Test case {test_id} not found")
    return TestCaseResponse(
        id=updated.id,
        test_id=updated.test_id,
        objective=updated.objective,
        requirement_id=updated.requirement_id,
        service_id_hex=updated.service_id_hex,
        subfunction_hex=updated.subfunction_hex,
        preconditions=updated.preconditions,
        session=updated.session,
        security_state=updated.security_state,
        request_hex=updated.request_hex,
        expected_response_hex=updated.expected_response_hex,
        pass_criteria=updated.pass_criteria,
        fail_criteria=updated.fail_criteria,
        test_type=updated.test_type,
        source_evidence=updated.source_evidence,
        generation_rationale=updated.generation_rationale,
        confidence=updated.confidence,
        review_status=updated.review_status,
        version=updated.version
    )

@router.delete("/{test_id}")
def delete_test(test_id: str):
    repo = DiagRepository()
    success = repo.delete_test_case(test_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Test case {test_id} not found")
    return {"status": "success", "message": f"Test case {test_id} deleted"}
