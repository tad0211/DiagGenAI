"""
DiagGenAI - Verification Coverage Analyzer Frontend Module.
Multi-dimensional coverage metrics, specification gap detection,
and targeted test synthesis to close identified verification gaps.
"""

import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, Any, List

from frontend.ui_components import (
    render_section_header, render_status_pill,
    render_coverage_bar, render_hex_token, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_coverage_analyzer():
    render_section_header(
        "Verification Coverage Analyzer",
        "Multi-dimensional specification coverage tracking and automated gap identification"
    )

    # Action Toolbar
    col_a1, col_a2, col_sp = st.columns([1.2, 1.8, 3])
    with col_a1:
        if st.button("Re-Analyze Coverage", type="secondary"):
            try:
                requests.post(f"{API_URL}/api/coverage/analyze", timeout=10.0)
            except Exception:
                from app.testing.coverage_analyzer import CoverageAnalyzer
                CoverageAnalyzer().analyze_coverage(persist=True)
            st.rerun()
    with col_a2:
        if st.button("Generate All Missing Tests", type="primary"):
            try:
                res = requests.post(f"{API_URL}/api/coverage/generate-missing", json={}, timeout=15.0)
                st.success(f"Generated {res.json().get('created_count', 0)} missing tests.")
                st.rerun()
            except Exception:
                from app.testing.coverage_analyzer import CoverageAnalyzer
                res = CoverageAnalyzer().generate_missing_tests()
                st.success(f"Generated {res.get('created_tests_count', 0)} missing tests.")
                st.rerun()

    # Fetch Coverage Data
    cov_data = {}
    try:
        res = requests.get(f"{API_URL}/api/coverage", timeout=5.0)
        if res.status_code == 200:
            cov_data = res.json()
    except Exception:
        from app.testing.coverage_analyzer import CoverageAnalyzer
        cov_data = CoverageAnalyzer().analyze_coverage(persist=False)

    gaps = cov_data.get("gaps", [])
    matrix = cov_data.get("service_matrix", [])

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Clean Coverage Overview
    st.markdown("""
    <div style="font-size: 0.88rem; font-weight: 600; color: #0f172a; margin-bottom: 8px;">
        Coverage Dimensions (ISO 14229-1)
    </div>
    """, unsafe_allow_html=True)

    col_cov1, col_cov2 = st.columns(2)
    with col_cov1:
        render_coverage_bar("Requirements", float(cov_data.get("req_coverage", 58.3)), "Spec REQ Traceability")
        render_coverage_bar("Services", float(cov_data.get("service_coverage", 100.0)), "Configured SIDs")
        render_coverage_bar("Subfunctions", float(cov_data.get("subfunction_coverage", 80.0)), "Exercised")
        render_coverage_bar("Positive paths", float(cov_data.get("positive_coverage", 71.4)), "Standard Responses")
    with col_cov2:
        render_coverage_bar("Negative (NRC)", float(cov_data.get("negative_coverage", 57.1)), "Fault Injection")
        render_coverage_bar("Session transitions", float(cov_data.get("session_coverage", 60.0)), "State Switching")
        render_coverage_bar("Security access", float(cov_data.get("security_coverage", 50.0)), "Seed / Key Challenge")
        render_coverage_bar("Boundary testing", float(cov_data.get("boundary_coverage", 33.3)), "Min / Max Limits")

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    tab_gaps, tab_matrix = st.tabs([
        f"Coverage Gaps ({len(gaps)})",
        "Service Verification Matrix"
    ])

    with tab_gaps:
        if not gaps:
            st.success("All protocol paths, subfunctions, and requirements are covered.")
        else:
            st.markdown(f"**Identified Protocol Gaps ({len(gaps)} Scenarios Uncovered):**")

            for idx, gap in enumerate(gaps):
                gap_id = gap.get("gap_id", f"GAP-{idx+1:03d}")
                scenario = gap.get("missing_scenario", "")
                reason = gap.get("reason", "")
                evidence = gap.get("evidence", "ISO 14229-1")
                suggested = gap.get("suggested_test", "")
                srv = gap.get("service_id_hex", "")

                with st.expander(f"{gap_id} &bull; {srv} &bull; {scenario}", expanded=False):
                    st.markdown(f"**Rationale:** {reason}")
                    st.markdown(f"**Specification Evidence:** `{evidence}`")
                    st.markdown(f"**Recommended Frame:** {render_hex_token(suggested)}", unsafe_allow_html=True)

                    if st.button(f"Generate Test for {gap_id}", key=f"gap_btn_{gap_id}", type="primary"):
                        try:
                            requests.post(f"{API_URL}/api/coverage/generate-missing", json={"gap_ids": [gap_id]}, timeout=8.0)
                        except Exception:
                            from app.testing.coverage_analyzer import CoverageAnalyzer
                            CoverageAnalyzer().generate_missing_tests(gap_ids=[gap_id])
                        st.success(f"Test case generated for {gap_id} (Pending Review).")
                        st.rerun()

    with tab_matrix:
        if matrix:
            formatted = []
            for item in matrix:
                formatted.append({
                    "Service": item.get("service_hex"),
                    "Name": item.get("name"),
                    "Subfunctions": f"{item.get('subfunctions_covered', 0)} / {item.get('subfunctions_total', 0)}",
                    "Positive": "Covered" if item.get("has_positive") else "Missing",
                    "Negative": "Covered" if item.get("has_negative") else "Missing",
                    "Security": "Covered" if item.get("has_security") else "N/A",
                    "Boundary": "Covered" if item.get("has_boundary") else "N/A",
                    "Score": f"{item.get('health_score', 0.0):.0f}%"
                })
            st.dataframe(pd.DataFrame(formatted), use_container_width=True, hide_index=True)
        else:
            st.info("Service matrix data not loaded.")
