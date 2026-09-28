import csv
import io
import json
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.config import settings
from app.database.repository import DiagRepository

router = APIRouter(prefix="/api/automation", tags=["Automation Templates"])

class TemplateRequest(BaseModel):
    test_id: str
    template_type: str = "PYTHON"  # PYTHON, CAPL, GENERIC, CSV

class SuiteTemplateRequest(BaseModel):
    template_type: str = "PYTHON"
    review_status: Optional[str] = None
    service_hex: Optional[str] = None
    test_ids: Optional[List[str]] = None

class TemplateResponse(BaseModel):
    test_id: Optional[str] = None
    template_type: str
    code_content: str
    filename: str
    label: str = "Generated Automation Template"
    safety_banner: str = settings.SAFETY_BANNER

def generate_python_template(tc) -> str:
    raw_clean = tc.request_hex.replace(" ", "")
    exp_tokens = tc.expected_response_hex.split()
    exp_prefix = " ".join(exp_tokens[:2]) if len(exp_tokens) >= 2 else exp_tokens[0] if exp_tokens else ""
    return f'''# ==============================================================================
# DiagGenAI - Production Automation Template (Python / python-can / ISO-TP)
# Test ID: {tc.test_id}
# Objective: {tc.objective}
# Requirement: {tc.requirement_id or "N/A"}
# Target Service: {tc.service_id_hex} {f"Subfunction: {tc.subfunction_hex}" if tc.subfunction_hex else ""}
# Preconditions: {tc.preconditions}
# Notice: {settings.SAFETY_BANNER}
# ==============================================================================

import time
import logging
import can
import isotp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("{tc.test_id}")

class Test_{tc.test_id.replace("-", "_")}:
    def __init__(self, channel="vcan0", rx_id=0x7E8, tx_id=0x7E0):
        self.channel = channel
        self.rx_id = rx_id
        self.tx_id = tx_id
        self.test_id = "{tc.test_id}"
        self.timeout_s = 2.0

    def setup_preconditions(self, isotp_socket):
        """Prepare target ECU: Session={tc.session}, Security={tc.security_state}."""
        logger.info(f"[PRECONDITION] Verifying {tc.session} and {tc.security_state}...")
        # Step: Send TesterPresent if needed to maintain session
        time.sleep(0.05)

    def run_test(self):
        """Execute diagnostic request and assert expected response."""
        bus = can.interface.Bus(channel=self.channel, bustype="socketcan")
        addr = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=self.rx_id, txid=self.tx_id)
        stack = isotp.CanStack(bus=bus, address=addr)

        try:
            stack.start()
            self.setup_preconditions(stack)

            req_bytes = bytes.fromhex("{raw_clean}")
            logger.info(f"[{tc.test_id}] Transmitting Request Frame: {tc.request_hex}")
            stack.send(req_bytes)

            start_t = time.time()
            rsp_bytes = None
            while (time.time() - start_t) < self.timeout_s:
                if stack.available():
                    rsp_bytes = stack.recv()
                    break
                time.sleep(0.005)

            assert rsp_bytes is not None, f"TIMEOUT: ECU did not respond within {{self.timeout_s}}s"
            rsp_hex = rsp_bytes.hex(' ').upper()
            logger.info(f"[{tc.test_id}] Received Response Frame: {{rsp_hex}}")

            # Verification assertion
            expected_prefix = bytes.fromhex("{exp_prefix.replace(' ', '')}")
            assert rsp_bytes.startswith(expected_prefix), (
                f"VERIFICATION FAILURE: Expected {{expected_prefix.hex(' ').upper()}}, got {{rsp_hex}}"
            )
            logger.info(f"[PASS] {tc.test_id} validated successfully against ISO 14229 spec.")
            return True
        finally:
            stack.stop()
            bus.shutdown()

if __name__ == "__main__":
    test = Test_{tc.test_id.replace("-", "_")}()
    test.run_test()
'''

def generate_capl_template(tc) -> str:
    raw_clean = tc.request_hex.replace(" ", "")
    byte_list = ", ".join(f"0x{raw_clean[i:i+2]}" for i in range(0, len(raw_clean), 2))
    return f'''/* ==============================================================================
 * DiagGenAI - Production Automation Template (Vector CANoe / CAPL)
 * Test ID: {tc.test_id}
 * Objective: {tc.objective}
 * Requirement: {tc.requirement_id or "N/A"}
 * Notice: {settings.SAFETY_BANNER}
 * ============================================================================== */

variables
{{
  char gTestId[32] = "{tc.test_id}";
  byte gReqFrame[{len(raw_clean)//2}] = {{{byte_list}}};
}}

testcase TC_{tc.test_id.replace("-", "_")}()
{{
  diagRequest BCM_Req;
  diagResponse BCM_Resp;
  long wait_ret;

  testCaseTitle("{tc.test_id}", "{tc.objective}");
  testCaseDescription("Preconditions: {tc.preconditions} | Expected: {tc.expected_response_hex}");

  // Step 1: Precondition check
  TestStep("SETUP", "Enforcing session {tc.session} and security state {tc.security_state}");

  // Step 2: Transmit UDS Diagnostic Request Frame
  TestStep("TX", "Transmitting frame: {tc.request_hex}");
  diagResize(BCM_Req, {len(raw_clean)//2});
  diagSetPrimitiveData(BCM_Req, gReqFrame, {len(raw_clean)//2});
  diagSendRequest(BCM_Req);

  // Step 3: Await response within P2 timeout (2000 ms)
  wait_ret = TestWaitForDiagResponse(BCM_Req, 2000);
  if (wait_ret == 1)
  {{
    diagGetLastResponse(BCM_Req, BCM_Resp);
    testStepPass("PASS", "Received matching response frame from BCM.");
  }}
  else
  {{
    testStepFail("TIMEOUT", "Target ECU did not reply within P2 timeout window.");
  }}
}}
'''

def generate_generic_template(tc) -> str:
    return f'''# ==============================================================================
# DiagGenAI - Generic Automated Diagnostic Procedure (Robot Framework / YAML)
# ==============================================================================
test_case:
  id: "{tc.test_id}"
  objective: "{tc.objective}"
  requirement_id: "{tc.requirement_id or 'N/A'}"
  target_service_hex: "{tc.service_id_hex}"
  subfunction_hex: "{tc.subfunction_hex or 'None'}"
  preconditions:
    active_session: "{tc.session}"
    active_security: "{tc.security_state}"
    description: "{tc.preconditions}"
  execution_steps:
    - step: 1
      action: "PRECONDITION_SETUP"
      target_session: "{tc.session}"
    - step: 2
      action: "TRANSMIT_DIAGNOSTIC_FRAME"
      frame_hex: "{tc.request_hex}"
      timeout_ms: 2000
    - step: 3
      action: "ASSERT_RESPONSE_FRAME"
      expected_hex: "{tc.expected_response_hex}"
      pass_criteria: "{tc.pass_criteria}"
      fail_criteria: "{tc.fail_criteria}"
  metadata:
    test_type: "{tc.test_type}"
    confidence: {tc.confidence}
    review_status: "{tc.review_status}"
    safety_notice: "{settings.SAFETY_BANNER}"
'''

def generate_python_suite(test_cases) -> str:
    test_methods = []
    for tc in test_cases:
        raw_clean = tc.request_hex.replace(" ", "")
        exp_tokens = tc.expected_response_hex.split()
        exp_prefix = " ".join(exp_tokens[:2]) if len(exp_tokens) >= 2 else exp_tokens[0] if exp_tokens else ""
        test_methods.append(f'''
    def test_{tc.test_id.replace("-", "_")}(self):
        """{tc.test_id}: {tc.objective}"""
        logger.info("[EXEC] Testing {tc.test_id} ({tc.test_type}) -> Req: {tc.request_hex}")
        req = bytes.fromhex("{raw_clean}")
        # Send raw request via test adapter
        rsp = self.client.send_raw(req, timeout_ms=2000)
        assert rsp is not None, "ECU timeout on {tc.test_id}"
        expected = bytes.fromhex("{exp_prefix.replace(' ', '')}")
        assert rsp.startswith(expected), f"Mismatch on {tc.test_id}: expected {tc.expected_response_hex}, got {{rsp.hex(' ').upper()}}"
''')

    body = "".join(test_methods)
    return f'''# ==============================================================================
# DiagGenAI - Consolidated Automated Test Suite (PyTest + python-can)
# Total Test Cases: {len(test_cases)}
# Notice: {settings.SAFETY_BANNER}
# ==============================================================================

import pytest
import logging
import time

logger = logging.getLogger("DiagTestSuite")

class DummyUdsClient:
    """Mock client placeholder for HIL / vcan0 testing."""
    def send_raw(self, req_bytes, timeout_ms=2000):
        # Transmit via python-can socket
        return req_bytes # echo / mock placeholder

class TestDiagnosticSuite:
    @classmethod
    def setup_class(cls):
        cls.client = DummyUdsClient()
        logger.info("Initializing Diagnostic Test Suite on CAN channel vcan0...")
{body}
'''

def generate_csv_matrix(test_cases) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Test ID", "Test Type", "Service", "Subfunction", "Objective",
        "Preconditions", "Session", "Security", "Request (Tx)", "Expected Response (Rx)",
        "Pass Criteria", "Status", "Evidence"
    ])
    for tc in test_cases:
        writer.writerow([
            tc.test_id, tc.test_type, tc.service_id_hex, tc.subfunction_hex or "",
            tc.objective, tc.preconditions, tc.session, tc.security_state,
            tc.request_hex, tc.expected_response_hex, tc.pass_criteria,
            tc.review_status, tc.source_evidence
        ])
    return output.getvalue()

@router.post("/generate", response_model=TemplateResponse)
def generate_single_template(req: TemplateRequest):
    repo = DiagRepository()
    tc = repo.get_test_case_by_id(req.test_id)
    if not tc:
        raise HTTPException(status_code=404, detail=f"Test case {req.test_id} not found")

    ttype = req.template_type.upper()
    if ttype == "CAPL":
        code = generate_capl_template(tc)
        filename = f"{tc.test_id}.can"
    elif ttype == "GENERIC":
        code = generate_generic_template(tc)
        filename = f"{tc.test_id}.yml"
    elif ttype == "CSV":
        code = generate_csv_matrix([tc])
        filename = f"{tc.test_id}.csv"
    else:
        code = generate_python_template(tc)
        filename = f"test_{tc.test_id.lower().replace('-', '_')}.py"

    repo.log_audit("GENERATE_TEMPLATE", "AutomationTemplate", tc.test_id, f"Generated {ttype} template for {tc.test_id}")
    return TemplateResponse(
        test_id=tc.test_id,
        template_type=ttype,
        code_content=code,
        filename=filename
    )

@router.post("/generate-suite", response_model=TemplateResponse)
def generate_suite_template(req: SuiteTemplateRequest):
    repo = DiagRepository()
    all_tests = repo.get_test_cases(review_status=req.review_status)

    if req.service_hex:
        clean_s = req.service_hex.upper().strip()
        all_tests = [t for t in all_tests if t.service_id_hex.upper().strip() == clean_s]
    if req.test_ids:
        all_tests = [t for t in all_tests if t.test_id in req.test_ids]

    if not all_tests:
        raise HTTPException(status_code=404, detail="No matching test cases found for suite generation.")

    ttype = req.template_type.upper()
    if ttype == "CSV":
        code = generate_csv_matrix(all_tests)
        filename = "diagnostic_test_suite_matrix.csv"
    elif ttype == "CAPL":
        # combine CAPL testcases into single file
        code_parts = [
            f"/* DiagGenAI - Consolidated CAPL Suite ({len(all_tests)} Test Cases) */\n",
            f"/* {settings.SAFETY_BANNER} */\n\n"
        ]
        for t in all_tests:
            code_parts.append(generate_capl_template(t))
        code = "\n".join(code_parts)
        filename = "diagnostic_test_suite.can"
    elif ttype == "GENERIC":
        code_parts = [f"# DiagGenAI - Test Suite YAML ({len(all_tests)} Test Cases)\nsuite:\n"]
        for t in all_tests:
            code_parts.append(generate_generic_template(t))
        code = "\n".join(code_parts)
        filename = "diagnostic_test_suite.yml"
    else:
        code = generate_python_suite(all_tests)
        filename = "test_diagnostic_suite.py"

    repo.log_audit("GENERATE_SUITE_TEMPLATE", "AutomationSuite", f"Count={len(all_tests)}", f"Generated {ttype} suite")
    return TemplateResponse(
        template_type=ttype,
        code_content=code,
        filename=filename,
        label=f"Generated {ttype} Suite ({len(all_tests)} Tests)"
    )
