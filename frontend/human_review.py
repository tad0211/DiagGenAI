"""
DiagGenAI - Human Review & Compliance Audit Module.
Human-in-the-Loop governance workbench for safety-critical automotive diagnostics.
Enforces review and sign-off for all AI-generated test cases and maintains tamper-evident audit logs.
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from app.database.repository import DiagRepository

from frontend.ui_components import (
    render_section_header, render_status_pill,
    render_hex_token, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_human_review():
    render_section_header(
        "Human Review & Compliance Audit",
        "Mandatory engineering verification gate for AI-generated diagnostic tests and complete traceability audit log"
    )

    repo = DiagRepository()
    all_tests = repo.get_test_cases()
    audit_logs = repo.get_audit_logs(limit=150)

    pending_tests = [t for t in all_tests if t.review_status == "PENDING_REVIEW"]
    approved_tests = [t for t in all_tests if t.review_status == "APPROVED"]
    rejected_tests = [t for t in all_tests if t.review_status == "REJECTED"]

    total_count = len(all_tests)
    approval_rate = (len(approved_tests) / total_count * 100) if total_count > 0 else 0

    # Clean Governance Summary Strip
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; padding: 12px 18px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 20px;">
        <div>
            <span style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Total Artifacts</span>
            <div style="font-size: 1.25rem; font-weight: 700; color: #0f172a;">{total_count}</div>
        </div>
        <div style="width: 1px; height: 32px; background: #e2e8f0;"></div>
        <div>
            <span style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Pending Sign-off</span>
            <div style="font-size: 1.25rem; font-weight: 700; color: #92400e;">{len(pending_tests)}</div>
        </div>
        <div style="width: 1px; height: 32px; background: #e2e8f0;"></div>
        <div>
            <span style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Approved Tests</span>
            <div style="font-size: 1.25rem; font-weight: 700; color: #166534;">{len(approved_tests)}</div>
        </div>
        <div style="width: 1px; height: 32px; background: #e2e8f0;"></div>
        <div>
            <span style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Rejected</span>
            <div style="font-size: 1.25rem; font-weight: 700; color: {'#991b1b' if len(rejected_tests)>0 else '#64748b'};">{len(rejected_tests)}</div>
        </div>
        <div style="width: 1px; height: 32px; background: #e2e8f0;"></div>
        <div>
            <span style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Sign-off Rate</span>
            <div style="font-size: 1.25rem; font-weight: 700; color: {'#166534' if approval_rate >= 80 else '#0f172a'};">{approval_rate:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_queue, tab_audit = st.tabs([
        f"Verification Queue ({len(pending_tests)})",
        "Compliance Audit Trail"
    ])

    with tab_queue:
        if not pending_tests:
            st.success("All test cases have been reviewed and approved. Verification queue is clear.")
        else:
            col_q_head, col_q_bulk = st.columns([3, 1])
            with col_q_head:
                st.markdown(f"**Pending Review Queue ({len(pending_tests)} items):**")
            with col_q_bulk:
                if st.button("Approve All Pending", type="primary", use_container_width=True):
                    for pt in pending_tests:
                        repo.update_test_review(pt.test_id, "APPROVED", "lead_engineer", "Bulk sign-off by lead diagnostic engineer")
                    st.success(f"Approved {len(pending_tests)} test cases.")
                    st.rerun()

            for tc in pending_tests:
                with st.expander(f"{tc.test_id} &bull; {tc.service_id_hex} &bull; {tc.test_type} &bull; {tc.objective[:65]}...", expanded=False):
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        st.markdown(f"**Objective:** {tc.objective}")
                        st.markdown(f"**Requirement:** `{tc.requirement_id}` &bull; Session: `{tc.session}` &bull; Security: `{tc.security_state}`")
                        st.markdown(f"**Preconditions:** {tc.preconditions}")
                        st.markdown(f"**Evidence:** `{tc.source_evidence}`")
                    with col_t2:
                        st.markdown(f"**Request (Tx):** {render_hex_token(tc.request_hex)}", unsafe_allow_html=True)
                        st.markdown(f"**Expected (Rx):** {render_hex_token(tc.expected_response_hex)}", unsafe_allow_html=True)
                        st.markdown(f"**Pass Criteria:** {tc.pass_criteria}")
                        st.markdown(f"**Fail Criteria:** {tc.fail_criteria}")

                    st.markdown(f"<div style='font-size:0.78rem; color:#64748b; margin-top:4px;'>Rationale: {tc.generation_rationale}</div>", unsafe_allow_html=True)

                    col_r1, col_r2, col_r3 = st.columns([1, 1, 3])
                    with col_r1:
                        if st.button("Approve", key=f"hq_app_{tc.test_id}", type="primary"):
                            repo.update_test_review(tc.test_id, "APPROVED", "lead_engineer", "Verified against ISO 14229 spec")
                            st.rerun()
                    with col_r2:
                        if st.button("Reject", key=f"hq_rej_{tc.test_id}"):
                            repo.update_test_review(tc.test_id, "REJECTED", "lead_engineer", "Rejected: does not match ECU baseline")
                            st.rerun()
                    with col_r3:
                        reviewer_note = st.text_input("Audit Note", value="Protocol verified against ECU specification", key=f"note_{tc.test_id}")

    with tab_audit:
        st.markdown("**Compliance Audit Trail (Latest Events):**")
        if not audit_logs:
            st.info("No audit logs recorded yet.")
        else:
            log_records = []
            for log in audit_logs:
                log_records.append({
                    "Timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "-",
                    "Action": log.action,
                    "Entity Type": log.entity_type,
                    "Entity ID": log.entity_id,
                    "Details": log.details,
                    "User": log.user_id or "system"
                })
            df_logs = pd.DataFrame(log_records)
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
