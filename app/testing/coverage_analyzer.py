"""
DiagGenAI - Coverage Analyzer & Gap Detection Engine.
Dynamically inspects specification requirements, UDS services, subfunctions, and test cases
to compute multi-dimensional coverage metrics and detect actionable verification gaps.
Enables one-click generation of missing tests to close protocol coverage gaps.
"""

import json
from typing import Dict, Any, List, Optional
from sqlalchemy import func
from app.database.repository import DiagRepository
from app.database.models import Service, Subfunction, Requirement, TestCase, Coverage

class CoverageAnalyzer:
    def __init__(self, repo: Optional[DiagRepository] = None):
        self.repo = repo or DiagRepository()

    def analyze_coverage(self, persist: bool = True) -> Dict[str, Any]:
        """
        Dynamically calculate multi-dimensional coverage across all database entities:
        - Requirements coverage
        - Service coverage
        - Subfunction coverage
        - Positive test coverage
        - Negative test coverage
        - Session transition coverage
        - Security access coverage
        - Boundary test coverage
        Detects concrete coverage gaps and optionally persists a snapshot.
        """
        services = self.repo.get_services()
        requirements = self.repo.get_requirements()
        test_cases = self.repo.get_test_cases()

        total_reqs = len(requirements)
        total_services = len(services)
        all_subfunctions = []
        for s in services:
            all_subfunctions.extend(s.subfunctions)
        total_subfunctions = len(all_subfunctions)

        # 1. Requirement Coverage
        tested_req_ids = {tc.requirement_id for tc in test_cases if tc.requirement_id}
        req_covered_count = sum(1 for r in requirements if r.req_id in tested_req_ids)
        req_coverage = (req_covered_count / total_reqs * 100.0) if total_reqs > 0 else 100.0

        # 2. Service Coverage
        tested_service_hexes = {tc.service_id_hex.upper().strip() for tc in test_cases if tc.service_id_hex}
        # Normalize
        norm_tested_services = set()
        for h in tested_service_hexes:
            norm = h if h.startswith("0X") else f"0X{h}"
            norm_tested_services.add(norm)

        srv_covered_count = 0
        for s in services:
            s_hex = s.service_id_hex.upper().strip()
            if not s_hex.startswith("0X"):
                s_hex = f"0X{s_hex}"
            if s_hex in norm_tested_services:
                srv_covered_count += 1
        service_coverage = (srv_covered_count / total_services * 100.0) if total_services > 0 else 100.0

        # 3. Subfunction Coverage
        tested_subfunction_keys = set()
        for tc in test_cases:
            if tc.subfunction_hex and tc.service_id_hex:
                s_hex = tc.service_id_hex.upper().strip()
                norm_s = s_hex if s_hex.startswith("0X") else f"0X{s_hex}"
                sf_hex = tc.subfunction_hex.upper().strip()
                norm_sf = sf_hex if sf_hex.startswith("0X") else f"0X{sf_hex}"
                tested_subfunction_keys.add(f"{norm_s}_{norm_sf}")

        subfunction_covered_count = 0
        for s in services:
            s_hex = s.service_id_hex.upper().strip()
            norm_s = s_hex if s_hex.startswith("0X") else f"0X{s_hex}"
            for sf in s.subfunctions:
                sf_hex = sf.subfunction_hex.upper().strip()
                norm_sf = sf_hex if sf_hex.startswith("0X") else f"0X{sf_hex}"
                if f"{norm_s}_{norm_sf}" in tested_subfunction_keys:
                    subfunction_covered_count += 1
        subfunction_coverage = (subfunction_covered_count / total_subfunctions * 100.0) if total_subfunctions > 0 else 100.0

        # 4. Dimension-specific Coverage
        services_with_positive = set()
        services_with_negative = set()
        services_with_session = set()
        services_with_security = set()
        services_with_boundary = set()

        for tc in test_cases:
            s_hex = tc.service_id_hex.upper().strip()
            norm_s = s_hex if s_hex.startswith("0X") else f"0X{s_hex}"
            t_type = tc.test_type.upper()
            if t_type == "POSITIVE":
                services_with_positive.add(norm_s)
            elif t_type in ["NEGATIVE", "INVALID_PARAM"]:
                services_with_negative.add(norm_s)
            elif t_type == "SESSION":
                services_with_session.add(norm_s)
            elif t_type == "SECURITY":
                services_with_security.add(norm_s)
            elif t_type == "BOUNDARY":
                services_with_boundary.add(norm_s)

        positive_coverage = (len(services_with_positive) / total_services * 100.0) if total_services > 0 else 100.0
        negative_coverage = (len(services_with_negative) / total_services * 100.0) if total_services > 0 else 100.0

        # Services that involve session transitions (0x10, 0x11, 0x22, 0x2E, 0x31)
        session_relevant = {"0X10", "0X11", "0X22", "0X2E", "0X31"}
        ses_relevant_count = len(session_relevant.intersection({s.service_id_hex.upper() for s in services})) or 1
        session_coverage = min(100.0, (len(services_with_session.intersection(session_relevant)) / ses_relevant_count * 100.0))

        # Services that involve security access (0x27, 0x2E, 0x31)
        security_relevant = {"0X27", "0X2E", "0X31"}
        sec_relevant_count = len(security_relevant.intersection({s.service_id_hex.upper() for s in services})) or 1
        security_coverage = min(100.0, (len(services_with_security.intersection(security_relevant)) / sec_relevant_count * 100.0))

        # Boundary coverage across parameterized services (0x22, 0x2E, 0x31)
        boundary_relevant = {"0X22", "0X2E", "0X31"}
        bnd_relevant_count = len(boundary_relevant.intersection({s.service_id_hex.upper() for s in services})) or 1
        boundary_coverage = min(100.0, (len(services_with_boundary.intersection(boundary_relevant)) / bnd_relevant_count * 100.0))

        # 5. Detect Concrete Gaps
        gaps = self._detect_gaps(services, requirements, test_cases, tested_subfunction_keys, tested_req_ids)

        metrics = {
            "req_coverage": round(req_coverage, 1),
            "service_coverage": round(service_coverage, 1),
            "subfunction_coverage": round(subfunction_coverage, 1),
            "positive_coverage": round(positive_coverage, 1),
            "negative_coverage": round(negative_coverage, 1),
            "session_coverage": round(session_coverage, 1),
            "security_coverage": round(security_coverage, 1),
            "boundary_coverage": round(boundary_coverage, 1),
            "gaps": gaps,
            "total_requirements": total_reqs,
            "covered_requirements": req_covered_count,
            "total_services": total_services,
            "covered_services": srv_covered_count,
            "total_subfunctions": total_subfunctions,
            "covered_subfunctions": subfunction_covered_count,
            "total_test_cases": len(test_cases)
        }

        # 6. Service-by-Service Matrix
        service_matrix = []
        for s in services:
            s_hex = s.service_id_hex.upper().strip()
            norm_s = s_hex if s_hex.startswith("0X") else f"0X{s_hex}"
            s_sfs = s.subfunctions
            s_sfs_count = len(s_sfs)
            s_sfs_covered = sum(1 for sf in s_sfs if f"{norm_s}_{sf.subfunction_hex.upper().strip() if sf.subfunction_hex.upper().startswith('0X') else '0X'+sf.subfunction_hex.upper().strip()}" in tested_subfunction_keys)

            has_pos = norm_s in services_with_positive
            has_neg = norm_s in services_with_negative
            has_sec = norm_s in services_with_security
            has_bnd = norm_s in services_with_boundary

            # Compute service health score
            score_components = [1 if has_pos else 0, 1 if has_neg else 0]
            if s_sfs_count > 0:
                score_components.append(s_sfs_covered / s_sfs_count)
            if norm_s in security_relevant:
                score_components.append(1 if has_sec else 0)
            if norm_s in boundary_relevant:
                score_components.append(1 if has_bnd else 0)

            health_score = round(sum(score_components) / len(score_components) * 100.0, 1)

            service_matrix.append({
                "service_hex": s.service_id_hex,
                "name": s.name,
                "standard": getattr(s, "standard_ref", "ISO 14229-1"),
                "subfunctions_total": s_sfs_count,
                "subfunctions_covered": s_sfs_covered,
                "has_positive": has_pos,
                "has_negative": has_neg,
                "has_security": has_sec,
                "has_boundary": has_bnd,
                "health_score": health_score
            })

        metrics["service_matrix"] = service_matrix

        if persist:
            self.repo.save_coverage(metrics)
            self.repo.log_audit(
                action="ANALYZE_COVERAGE",
                entity_type="CoverageAnalyzer",
                entity_id="Latest",
                details=f"Calculated coverage: Req={req_coverage:.1f}%, Svc={service_coverage:.1f}%, SubFn={subfunction_coverage:.1f}%, Gaps={len(gaps)}"
            )

        return metrics

    def _detect_gaps(
        self,
        services: List[Service],
        requirements: List[Requirement],
        test_cases: List[TestCase],
        tested_subfunction_keys: set,
        tested_req_ids: set
    ) -> List[Dict[str, Any]]:
        """Identify missing protocol paths and uncovered subfunctions/requirements."""
        gaps = []
        gap_idx = 1

        # Check uncovered requirements
        for req in requirements:
            if req.req_id not in tested_req_ids:
                # Find associated service
                srv = next((s for s in services if s.id == req.service_id), None)
                srv_hex = srv.service_id_hex if srv else "0x22"
                gaps.append({
                    "gap_id": f"GAP-{gap_idx:03d}",
                    "service_id_hex": srv_hex,
                    "service_name": srv.name if srv else "Unknown",
                    "missing_scenario": f"Requirement {req.req_id}: {req.title}",
                    "reason": f"No test case verified for requirement: '{req.description}'",
                    "evidence": f"{req.source_doc or 'synthetic_bcm_diag_spec_v1_1.md'} ({req.source_section or 'General'})",
                    "suggested_test": f"Implement test verifying {req.title}",
                    "severity": "HIGH",
                    "test_type": "POSITIVE" if req.category == "Session" or req.category == "Functional" else "NEGATIVE",
                    "suggested_test_data": {
                        "objective": f"Verify {req.title} as specified in {req.req_id}",
                        "requirement_id": req.req_id,
                        "service_id_hex": srv_hex,
                        "preconditions": "ECU initialized in DefaultSession",
                        "session": "DefaultSession",
                        "security_state": "Locked",
                        "request_hex": f"{srv_hex.replace('0x', '').replace('0X', '')} 01",
                        "expected_response_hex": f"{(int(srv_hex, 16)+0x40):02X} 01",
                        "pass_criteria": f"Response confirms requirement {req.req_id}",
                        "fail_criteria": "Requirement criteria not satisfied",
                        "test_type": "POSITIVE" if req.category != "Negative" else "NEGATIVE",
                        "source_evidence": f"{req.source_doc or 'synthetic_bcm_diag_spec_v1_1.md'} ({req.source_section or 'General'})",
                        "generation_rationale": f"Auto-generated to close coverage gap for {req.req_id}"
                    }
                })
                gap_idx += 1

        # Check uncovered subfunctions
        for s in services:
            s_hex = s.service_id_hex.upper().strip()
            norm_s = s_hex if s_hex.startswith("0X") else f"0X{s_hex}"
            for sf in s.subfunctions:
                sf_hex = sf.subfunction_hex.upper().strip()
                norm_sf = sf_hex if sf_hex.startswith("0X") else f"0X{sf_hex}"
                if f"{norm_s}_{norm_sf}" not in tested_subfunction_keys:
                    clean_s = s_hex.replace("0X", "")
                    clean_sf = sf_hex.replace("0X", "")
                    clean_s_int = int(clean_s, 16)
                    resp_sid = f"{(clean_s_int + 0x40):02X}"

                    gaps.append({
                        "gap_id": f"GAP-{gap_idx:03d}",
                        "service_id_hex": s.service_id_hex,
                        "service_name": s.name,
                        "missing_scenario": f"Service {s.service_id_hex} Subfunction {sf.subfunction_hex} ({sf.name})",
                        "reason": f"Missing verification test for subfunction {sf.name} ({sf.subfunction_hex}) under {s.name}.",
                        "evidence": f"synthetic_bcm_diag_spec_v1_1.md Section 3",
                        "suggested_test": f"Send {clean_s} {clean_sf} -> Expect {resp_sid} {clean_sf}",
                        "severity": "HIGH" if s_hex in ["0X10", "0X11", "0X27"] else "MEDIUM",
                        "test_type": "POSITIVE",
                        "suggested_test_data": {
                            "objective": f"Verify Service {s.service_id_hex} Subfunction {sf.subfunction_hex} ({sf.name}) execution",
                            "requirement_id": "REQ-UDS-001",
                            "service_id_hex": s.service_id_hex,
                            "subfunction_hex": sf.subfunction_hex,
                            "preconditions": "ECU in DefaultSession",
                            "session": "DefaultSession",
                            "security_state": "Locked",
                            "request_hex": f"{clean_s} {clean_sf}",
                            "expected_response_hex": f"{resp_sid} {clean_sf}",
                            "pass_criteria": f"Positive response {resp_sid} {clean_sf} received",
                            "fail_criteria": "NRC returned or timeout",
                            "test_type": "POSITIVE",
                            "source_evidence": "synthetic_bcm_diag_spec_v1_1.md Section 3",
                            "generation_rationale": f"Auto-generated test to cover subfunction {sf.name}"
                        }
                    })
                    gap_idx += 1

        # Check negative test coverage per service
        tested_neg_services = {tc.service_id_hex.upper().strip() for tc in test_cases if tc.test_type in ["NEGATIVE", "INVALID_PARAM"]}
        for s in services:
            s_hex = s.service_id_hex.upper().strip()
            norm_s = s_hex if s_hex.startswith("0X") else f"0X{s_hex}"
            if norm_s not in tested_neg_services:
                clean_s = s_hex.replace("0X", "")
                gaps.append({
                    "gap_id": f"GAP-{gap_idx:03d}",
                    "service_id_hex": s.service_id_hex,
                    "service_name": s.name,
                    "missing_scenario": f"Negative NRC rejection test for Service {s.service_id_hex}",
                    "reason": f"Service {s.service_id_hex} ({s.name}) has no negative test cases validating NRC rejection behavior.",
                    "evidence": "ISO 14229-1 Negative Response Handling",
                    "suggested_test": f"Send invalid subfunction/payload {clean_s} FF -> Expect 7F {clean_s} 12/31",
                    "severity": "HIGH",
                    "test_type": "NEGATIVE",
                    "suggested_test_data": {
                        "objective": f"Verify negative response code on invalid request for {s.name}",
                        "requirement_id": "REQ-UDS-003",
                        "service_id_hex": s.service_id_hex,
                        "subfunction_hex": "0xFF",
                        "preconditions": "ECU in DefaultSession",
                        "session": "DefaultSession",
                        "security_state": "Locked",
                        "request_hex": f"{clean_s} FF",
                        "expected_response_hex": f"7F {clean_s} 12",
                        "pass_criteria": f"Negative response 7F {clean_s} with valid NRC",
                        "fail_criteria": "Positive response or unexpected crash",
                        "test_type": "NEGATIVE",
                        "source_evidence": "ISO 14229-1 NRC Handling",
                        "generation_rationale": f"Auto-generated negative test to verify NRC rejection on {s.service_id_hex}"
                    }
                })
                gap_idx += 1

        return gaps

    def generate_missing_tests(self, gap_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Synthesize tests for detected coverage gaps and add them to the test suite in PENDING_REVIEW status.
        Re-analyzes coverage and returns new metrics.
        """
        analysis = self.analyze_coverage(persist=False)
        gaps = analysis.get("gaps", [])

        if gap_ids:
            target_gaps = [g for g in gaps if g["gap_id"] in gap_ids]
        else:
            target_gaps = gaps

        created_tests = []
        existing_tcs = self.repo.get_test_cases()
        base_id_num = len(existing_tcs) + 1

        for idx, gap in enumerate(target_gaps):
            test_data = gap.get("suggested_test_data", {})
            test_id = f"TC-GAP-{base_id_num + idx:03d}"

            new_tc_dict = {
                "test_id": test_id,
                "objective": test_data.get("objective", f"Verify coverage gap {gap['gap_id']}"),
                "requirement_id": test_data.get("requirement_id", "REQ-UDS-001"),
                "service_id_hex": gap.get("service_id_hex", "0x22"),
                "subfunction_hex": test_data.get("subfunction_hex"),
                "preconditions": test_data.get("preconditions", "ECU powered, DefaultSession active"),
                "session": test_data.get("session", "DefaultSession"),
                "security_state": test_data.get("security_state", "Locked"),
                "request_hex": test_data.get("request_hex", "22 01"),
                "expected_response_hex": test_data.get("expected_response_hex", "62 01"),
                "pass_criteria": test_data.get("pass_criteria", "Response matches expected protocol frame"),
                "fail_criteria": test_data.get("fail_criteria", "NRC or timeout"),
                "test_type": test_data.get("test_type", gap.get("test_type", "POSITIVE")),
                "source_evidence": gap.get("evidence", "synthetic_bcm_diag_spec_v1_1.md"),
                "generation_rationale": f"Generated to resolve coverage gap {gap['gap_id']}: {gap.get('reason')}",
                "confidence": 0.95,
                "review_status": "PENDING_REVIEW"
            }

            created_tc = self.repo.add_test_case(new_tc_dict)
            self.repo.add_traceability_link("CoverageGap", gap["gap_id"], "TestCase", test_id, "RESOLVED_BY")
            created_tests.append(new_tc_dict)

        # Log audit
        self.repo.log_audit(
            action="RESOLVE_COVERAGE_GAPS",
            entity_type="CoverageAnalyzer",
            entity_id=f"GapsCount={len(target_gaps)}",
            details=f"Generated {len(created_tests)} test cases to close coverage gaps. Status: PENDING_REVIEW"
        )

        # Fresh coverage re-analysis after closing gaps
        new_metrics = self.analyze_coverage(persist=True)

        return {
            "created_tests_count": len(created_tests),
            "created_tests": created_tests,
            "updated_coverage": new_metrics
        }
