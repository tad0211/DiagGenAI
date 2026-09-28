"""
DiagGenAI - AI Test Generator Frontend Module.
Two-stage test synthesis:
- Step 1: Define test objective and target specification
- Step 2: Select test dimensions (Positive, Negative, Boundary, Session, Security)
Provides clean repository browsing, inline test details, and human sign-off workflow.
"""

import streamlit as st
import requests
import json
import pandas as pd
from typing import List, Dict, Any

from frontend.ui_components import (
    render_section_header, render_status_pill,
    render_hex_token, get_icon
)

API_URL = "http://127.0.0.1:8000"

PRESET_PROMPTS = [
    "Verify DiagnosticSessionControl (0x10) transitions between Default and Extended sessions",
    "Verify ReadDataByIdentifier (0x22) for VIN DID 0xF190 and unsupported DID rejection",
    "Verify SecurityAccess (0x27) seed request and key exchange sequence",
    "Verify WriteDataByIdentifier (0x2E) parameter boundaries and security prerequisites",
    "Verify RoutineControl (0x31) self-test routine execution and result query",
    "Verify ECUReset (0x11) hard reset and soft reset execution"
]

def render_test_generator():
    render_section_header(
        "Diagnostic Test Suite Synthesis",
        "Two-stage test generator grounded in ISO 14229-1 requirements. AI-synthesized tests require human verification before release."
    )

    tab_gen, tab_repo = st.tabs([
        "Test Generator",
        "Test Suite Repository"
    ])

    # ==================== TAB 1: TWO-STAGE GENERATOR ====================
    with tab_gen:
        # Step 1: Define Objective
        st.markdown("""
        <div style="font-size: 0.82rem; font-weight: 600; color: #1e3a8a; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
            Step 1: Define Test Objective & Specification Scope
        </div>
        """, unsafe_allow_html=True)

        col_p1, col_p2 = st.columns([3, 1])
        with col_p1:
            template_choice = st.selectbox(
                "Standard Requirement Template",
                ["-- Custom Objective --"] + PRESET_PROMPTS
            )
        with col_p2:
            target_service = st.selectbox(
                "Target Service",
                ["Auto-Detect", "0x10 (DiagnosticSessionControl)", "0x11 (ECUReset)", "0x22 (ReadDataByIdentifier)", "0x27 (SecurityAccess)", "0x2E (WriteDataByIdentifier)", "0x31 (RoutineControl)"]
            )

        default_text = template_choice if template_choice != "-- Custom Objective --" else ""
        user_prompt = st.text_input(
            "Test Objective / Requirement Description",
            value=default_text,
            placeholder="e.g. Verify service 0x22 ReadDataByIdentifier with VIN 0xF190 and rejection of invalid DID 0x9999"
        )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Step 2: Select Test Dimensions
        st.markdown("""
        <div style="font-size: 0.82rem; font-weight: 600; color: #1e3a8a; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
            Step 2: Select Test Dimensions
        </div>
        """, unsafe_allow_html=True)

        d_cols = st.columns(6)
        with d_cols[0]: gen_pos = st.checkbox("Positive Path", value=True)
        with d_cols[1]: gen_neg = st.checkbox("Negative (NRC)", value=True)
        with d_cols[2]: gen_bnd = st.checkbox("Boundary / Range", value=True)
        with d_cols[3]: gen_ses = st.checkbox("Session State", value=True)
        with d_cols[4]: gen_sec = st.checkbox("Security Access", value=True)
        with d_cols[5]: gen_inv = st.checkbox("Invalid Payload", value=False)

        requested_types = []
        if gen_pos: requested_types.append("POSITIVE")
        if gen_neg: requested_types.append("NEGATIVE")
        if gen_bnd: requested_types.append("BOUNDARY")
        if gen_ses: requested_types.append("SESSION")
        if gen_sec: requested_types.append("SECURITY")
        if gen_inv: requested_types.append("INVALID_PARAM")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        if st.button("Generate Test Suite", type="primary"):
            if not user_prompt.strip() and target_service == "Auto-Detect":
                st.warning("Please specify a test objective or target service.")
            elif not requested_types:
                st.warning("Please select at least one test dimension.")
            else:
                service_hex = None
                if target_service != "Auto-Detect":
                    service_hex = target_service.split(" ")[0].strip()

                with st.spinner("Synthesizing test cases from specification evidence..."):
                    try:
                        res = requests.post(
                            f"{API_URL}/api/tests/generate",
                            json={
                                "prompt": user_prompt or target_service,
                                "target_service_hex": service_hex,
                                "requested_types": requested_types,
                                "persist": True
                            },
                            timeout=15.0
                        )
                        if res.status_code == 200:
                            st.session_state["last_generated"] = res.json()
                            st.toast(f"Synthesized {len(res.json())} test cases.")
                    except Exception:
                        from app.testing.generator import generate_diagnostic_tests
                        objs = generate_diagnostic_tests(
                            prompt=user_prompt or target_service,
                            target_service_hex=service_hex,
                            requested_types=requested_types,
                            persist=True
                        )
                        st.session_state["last_generated"] = [t.dict() for t in objs]
                        st.toast(f"Synthesized {len(objs)} test cases (direct engine).")

        # Display newly generated tests
        if "last_generated" in st.session_state and st.session_state["last_generated"]:
            last_tcs = st.session_state["last_generated"]
            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="font-size: 0.88rem; font-weight: 600; color: #0f172a; margin-bottom: 6px;">
                Synthesized Tests ({len(last_tcs)} test cases &bull; Pending Verification)
            </div>
            """, unsafe_allow_html=True)

            for tc in last_tcs:
                _render_test_row_with_details(tc, prefix="gen")

    # ==================== TAB 2: TEST REPOSITORY ====================
    with tab_repo:
        tests_data = []
        try:
            res = requests.get(f"{API_URL}/api/tests", timeout=5.0)
            if res.status_code == 200:
                tests_data = res.json()
        except Exception:
            from app.database.repository import DiagRepository
            tests_data = [t.__dict__ for t in DiagRepository().get_test_cases()]

        col_f1, col_f2, col_f3, col_exp = st.columns([1.5, 1.2, 2.5, 1.5])
        with col_f1:
            status_f = st.selectbox("Status", ["All Status", "PENDING_REVIEW", "APPROVED", "REJECTED"], key="repo_st")
        with col_f2:
            type_f = st.selectbox("Dimension", ["All Dimensions", "POSITIVE", "NEGATIVE", "BOUNDARY", "SESSION", "SECURITY"], key="repo_ty")
        with col_f3:
            search_f = st.text_input("Search tests...", placeholder="Test ID, Service, or Objective...", key="repo_sq")
        with col_exp:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if tests_data:
                st.download_button(
                    label="Export CSV",
                    data=pd.DataFrame(tests_data).to_csv(index=False),
                    file_name="diagnostic_test_suite.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        filtered = tests_data
        if status_f != "All Status":
            filtered = [t for t in filtered if t.get("review_status") == status_f]
        if type_f != "All Dimensions":
            filtered = [t for t in filtered if t.get("test_type") == type_f]
        if search_f.strip():
            sq = search_f.strip().lower()
            filtered = [t for t in filtered if sq in str(t.get("test_id", "")).lower() or sq in str(t.get("objective", "")).lower() or sq in str(t.get("service_id_hex", "")).lower()]

        st.caption(f"Showing {len(filtered)} of {len(tests_data)} test cases:")

        for tc in filtered:
            _render_test_row_with_details(tc, prefix="rep")

def _render_test_row_with_details(tc: Dict[str, Any], prefix: str = "tc"):
    t_id = tc.get("test_id", "")
    t_svc = tc.get("service_id_hex", "")
    t_type = tc.get("test_type", "")
    t_stat = tc.get("review_status", "PENDING_REVIEW")
    t_obj = tc.get("objective", "")
    t_req = tc.get("request_hex", "")
    t_exp = tc.get("expected_response_hex", "")
    t_prec = tc.get("preconditions", "")
    t_evid = tc.get("source_evidence", "")
    t_pass = tc.get("pass_criteria", "")
    t_fail = tc.get("fail_criteria", "")

    card_key = f"{prefix}_{t_id}"

    with st.expander(f"{t_id}  &bull;  {t_svc}  &bull;  {t_type}  &bull;  {t_stat}  &bull;  {t_obj[:65]}...", expanded=False):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown(f"**Objective:** {t_obj}")
            st.markdown(f"**Preconditions:** {t_prec} &bull; Session: `{tc.get('session')}` &bull; Security: `{tc.get('security_state')}`")
            st.markdown(f"**Source Evidence:** `{t_evid}`")
        with col_c2:
            st.markdown(f"**Request (Tx):** {render_hex_token(t_req)}", unsafe_allow_html=True)
            st.markdown(f"**Expected (Rx):** {render_hex_token(t_exp)}", unsafe_allow_html=True)
            st.markdown(f"**Status:** {render_status_pill(t_stat)}", unsafe_allow_html=True)

        st.markdown(f"<div style='font-size:0.78rem; color:#64748b;'>Pass: {t_pass} &bull; Fail: {t_fail}</div>", unsafe_allow_html=True)

        col_act1, col_act2, col_act3 = st.columns([1, 1, 3])
        with col_act1:
            if t_stat != "APPROVED":
                if st.button("Approve", key=f"app_{card_key}", type="primary"):
                    _save_review(t_id, "APPROVED")
                    st.rerun()
            else:
                st.button("Approved", key=f"app_{card_key}", disabled=True)
        with col_act2:
            if t_stat != "REJECTED":
                if st.button("Reject", key=f"rej_{card_key}"):
                    _save_review(t_id, "REJECTED")
                    st.rerun()
            else:
                st.button("Rejected", key=f"rej_{card_key}", disabled=True)
        with col_act3:
            with st.popover("Edit Test"):
                new_obj = st.text_input("Objective", value=t_obj, key=f"ed_o_{card_key}")
                new_req = st.text_input("Request Hex", value=t_req, key=f"ed_r_{card_key}")
                new_exp = st.text_input("Expected Response", value=t_exp, key=f"ed_e_{card_key}")
                if st.button("Save Changes", key=f"ed_s_{card_key}", type="primary"):
                    _update_test_case(t_id, {"objective": new_obj, "request_hex": new_req, "expected_response_hex": new_exp, "review_status": "APPROVED"})
                    st.rerun()

def _save_review(test_id: str, decision: str):
    try:
        requests.post(
            f"{API_URL}/api/tests/{test_id}/review",
            json={"reviewer": "engineer", "decision": decision, "comment": "Review sign-off"},
            timeout=3.0
        )
    except Exception:
        from app.database.repository import DiagRepository
        DiagRepository().update_test_review(test_id=test_id, decision=decision, reviewer="engineer", comment="Review sign-off")

def _update_test_case(test_id: str, data: dict):
    try:
        requests.put(f"{API_URL}/api/tests/{test_id}", json=data, timeout=3.0)
    except Exception:
        from app.database.repository import DiagRepository
        DiagRepository().update_test_case(test_id=test_id, test_data=data)
