"""
DiagGenAI - Diagnostic Test Execution Engine.
Executes UDS test cases against the stateful Mock ECU Simulator.
Performs byte-level difference analysis, root-cause diagnostic explanation,
verdict evaluation (PASS/FAIL), and stores audit-ready TestResult records.
Enforces the mandatory SIMULATION MODE safety barrier.
"""

import time
from typing import Dict, Any, List, Optional
from app.config import settings
from app.database.repository import DiagRepository
from app.database.models import TestCase, TestResult
from app.uds.ecu_simulator import global_ecu_simulator

class TestExecutor:
    __test__ = False
    def __init__(self, repo: Optional[DiagRepository] = None):
        self.repo = repo or DiagRepository()
        self.simulator = global_ecu_simulator

    def execute_test(self, test_case: TestCase) -> Dict[str, Any]:
        """
        Execute a single test case against the Mock ECU Simulator.
        Evaluates pass/fail outcome, diff analysis, and logs test result.
        """
        req_hex = test_case.request_hex.strip()
        exp_hex = test_case.expected_response_hex.strip()

        # Run against simulator using preconditions
        sim_res = self.simulator.process_request(
            request_hex=req_hex,
            session_override=test_case.session,
            security_override=test_case.security_state
        )

        actual_hex = sim_res.response_hex.strip()

        # Compare actual vs expected
        outcome, diff_summary, root_cause = self._evaluate_response(
            req_hex=req_hex,
            expected_hex=exp_hex,
            actual_hex=actual_hex,
            test_type=test_case.test_type,
            sim_explanation=sim_res.explanation
        )

        # Record result in database
        result_record = self.repo.record_test_result({
            "test_case_id": test_case.id,
            "request_sent_hex": req_hex,
            "expected_response_hex": exp_hex,
            "actual_response_hex": actual_hex or "[NO RESPONSE]",
            "outcome": outcome,
            "diff_analysis": diff_summary,
            "explanation": root_cause
        })

        return {
            "result_id": result_record.id,
            "test_id": test_case.test_id,
            "objective": test_case.objective,
            "service_id_hex": test_case.service_id_hex,
            "test_type": test_case.test_type,
            "request_hex": req_hex,
            "expected_response_hex": exp_hex,
            "actual_response_hex": actual_hex or "[NO RESPONSE]",
            "outcome": outcome,
            "diff_analysis": diff_summary,
            "explanation": root_cause,
            "execution_time_ms": sim_res.execution_time_ms,
            "can_trace": sim_res.can_trace,
            "simulation_mode": settings.SAFETY_BANNER
        }

    def execute_suite(
        self,
        review_status: Optional[str] = None,
        service_hex: Optional[str] = None,
        test_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a batch test suite against the Mock ECU Simulator.
        """
        all_tests = self.repo.get_test_cases(review_status=review_status, test_type=test_type)

        if service_hex:
            clean_s = service_hex.upper().strip()
            all_tests = [t for t in all_tests if t.service_id_hex.upper().strip() == clean_s]

        start_time = time.time()
        results = []
        passed_cnt = 0
        failed_cnt = 0

        for tc in all_tests:
            res = self.execute_test(tc)
            if res["outcome"] == "PASS":
                passed_cnt += 1
            else:
                failed_cnt += 1
            results.append(res)

        total_exec = len(all_tests)
        total_time_ms = round((time.time() - start_time) * 1000.0, 1)
        pass_rate = round((passed_cnt / total_exec * 100.0), 1) if total_exec > 0 else 0.0

        self.repo.log_audit(
            action="EXECUTE_SUITE",
            entity_type="TestExecutor",
            entity_id=f"Total={total_exec}",
            details=f"Suite Executed: {passed_cnt} Passed, {failed_cnt} Failed, Pass Rate: {pass_rate:.1f}% ({total_time_ms} ms)"
        )

        return {
            "total_executed": total_exec,
            "passed": passed_cnt,
            "failed": failed_cnt,
            "pass_rate": pass_rate,
            "total_time_ms": total_time_ms,
            "results": results,
            "simulation_mode": settings.SAFETY_BANNER
        }

    def _evaluate_response(
        self,
        req_hex: str,
        expected_hex: str,
        actual_hex: str,
        test_type: str,
        sim_explanation: str
    ) -> tuple:
        """
        Compare byte sequences and produce a granular diff and diagnostic explanation.
        """
        exp_tokens = expected_hex.split()
        act_tokens = actual_hex.split()

        # Handle empty/timeout
        if not act_tokens:
            return (
                "FAIL",
                "TIMEOUT: Expected response frame, but ECU did not transmit any response.",
                "Simulated ECU timeout. Probable cause: Baud rate mismatch, P2 timer expiration, or ECU asleep."
            )

        # Check positive response or NRC prefix matching
        # Positive response SID = Service SID + 0x40
        # Negative response SID = 0x7F
        is_pass = True
        diff_points = []

        # If expected is a prefix or wildcard match
        min_len = min(len(exp_tokens), len(act_tokens))
        for i in range(min_len):
            if exp_tokens[i] == "**" or exp_tokens[i] == "XX":
                continue # Wildcard byte
            if exp_tokens[i].upper() != act_tokens[i].upper():
                is_pass = False
                diff_points.append(f"Byte {i+1}: expected 0x{exp_tokens[i]}, received 0x{act_tokens[i]}")

        # If lengths differ significantly and no wildcards
        if len(act_tokens) < len(exp_tokens):
            is_pass = False
            diff_points.append(f"Frame truncated: expected {len(exp_tokens)} bytes, received {len(act_tokens)} bytes")

        if is_pass:
            outcome = "PASS"
            diff_summary = f"Exact byte match ({len(act_tokens)} bytes verified)."
            root_cause = f"Test passed. Frame conforms with ISO 14229-1 specification. {sim_explanation}"
        else:
            outcome = "FAIL"
            diff_summary = "; ".join(diff_points)
            if act_tokens[0] == "7F":
                nrc_hex = act_tokens[2] if len(act_tokens) >= 3 else "Unknown"
                root_cause = f"Test failed: Received Negative Response (NRC 0x{nrc_hex}). {sim_explanation}"
            else:
                root_cause = f"Test failed: Response bytes mismatched expectations. {sim_explanation}"

        return outcome, diff_summary, root_cause
