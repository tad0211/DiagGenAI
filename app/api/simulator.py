from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.config import settings
from app.database.repository import DiagRepository
from app.uds.ecu_simulator import global_ecu_simulator
from app.testing.executor import TestExecutor

router = APIRouter(prefix="/api/simulator", tags=["Mock ECU Simulator"])

class SimulationRequest(BaseModel):
    request_hex: str
    active_session: Optional[str] = None
    active_security: Optional[str] = None
    inject_fault: Optional[str] = None  # None, "TIMEOUT", "NRC_22_CONDITIONS", "GARBAGE_RESPONSE"

class SimulationResponse(BaseModel):
    request_hex: str
    response_hex: str
    response_type: str  # POSITIVE, NEGATIVE, TIMEOUT, UNEXPECTED
    execution_time_ms: float
    simulation_state: dict
    explanation: str
    can_trace: Optional[dict] = None
    safety_banner: str = settings.SAFETY_BANNER

class EnvironmentalRequest(BaseModel):
    vehicle_speed_kmh: Optional[float] = None
    battery_voltage_v: Optional[float] = None

class ExecuteTestRequest(BaseModel):
    test_id: str

class ExecuteSuiteRequest(BaseModel):
    review_status: Optional[str] = None
    service_hex: Optional[str] = None
    test_type: Optional[str] = None

class TestResultResponse(BaseModel):
    id: int
    test_case_id: int
    execution_timestamp: str
    request_sent_hex: str
    expected_response_hex: str
    actual_response_hex: str
    outcome: str
    diff_analysis: Optional[str] = None
    explanation: Optional[str] = None
    execution_mode: str

@router.post("/send", response_model=SimulationResponse)
def send_to_mock_ecu(sim_req: SimulationRequest):
    sim_res = global_ecu_simulator.process_request(
        request_hex=sim_req.request_hex,
        session_override=sim_req.active_session,
        security_override=sim_req.active_security,
        inject_fault=sim_req.inject_fault
    )
    repo = DiagRepository()
    repo.log_audit(
        action="MOCK_ECU_EXEC",
        entity_type="Simulator",
        entity_id=sim_req.request_hex,
        details=f"Response: {sim_res.response_hex} ({sim_res.response_type})"
    )
    return SimulationResponse(
        request_hex=sim_res.request_hex,
        response_hex=sim_res.response_hex,
        response_type=sim_res.response_type,
        execution_time_ms=sim_res.execution_time_ms,
        simulation_state={"session": sim_res.session_after, "security": sim_res.security_after},
        explanation=sim_res.explanation,
        can_trace=sim_res.can_trace
    )

@router.get("/state")
def get_ecu_state():
    return global_ecu_simulator.get_state()

@router.post("/reset")
def reset_ecu_state():
    global_ecu_simulator.reset()
    return {"status": "success", "message": "Simulated ECU reset to factory defaults (DefaultSession, Locked, 0 km/h)."}

@router.post("/environmental")
def set_environmental_conditions(req: EnvironmentalRequest):
    global_ecu_simulator.set_environmental(
        speed_kmh=req.vehicle_speed_kmh,
        voltage_v=req.battery_voltage_v
    )
    return {
        "status": "success",
        "speed_kmh": global_ecu_simulator.vehicle_speed_kmh,
        "voltage_v": global_ecu_simulator.battery_voltage_v
    }

@router.post("/execute-test")
def execute_single_test(req: ExecuteTestRequest):
    repo = DiagRepository()
    tc = repo.get_test_case_by_id(req.test_id)
    if not tc:
        raise HTTPException(status_code=404, detail=f"Test case {req.test_id} not found")

    executor = TestExecutor(repo=repo)
    result = executor.execute_test(tc)
    return result

@router.post("/execute-suite")
def execute_test_suite(req: Optional[ExecuteSuiteRequest] = None):
    executor = TestExecutor()
    status = req.review_status if req else None
    srv = req.service_hex if req else None
    ttype = req.test_type if req else None
    summary = executor.execute_suite(review_status=status, service_hex=srv, test_type=ttype)
    return summary

@router.get("/results", response_model=List[TestResultResponse])
def get_execution_results(limit: int = Query(50)):
    repo = DiagRepository()
    results = repo.get_test_results(limit=limit)
    return [
        TestResultResponse(
            id=r.id,
            test_case_id=r.test_case_id,
            execution_timestamp=r.execution_timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.execution_timestamp else "",
            request_sent_hex=r.request_sent_hex,
            expected_response_hex=r.expected_response_hex,
            actual_response_hex=r.actual_response_hex,
            outcome=r.outcome,
            diff_analysis=r.diff_analysis,
            explanation=r.explanation,
            execution_mode=r.execution_mode
        )
        for r in results
    ]
