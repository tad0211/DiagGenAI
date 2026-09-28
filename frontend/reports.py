"""
DiagGenAI - Engineering Validation Reports Frontend Module.
Generates, previews, and exports comprehensive formal ISO 14229-1 verification reports
in Markdown, standalone printable HTML, and JSON summary formats.
"""

import streamlit as st
import requests
import json
import streamlit.components.v1 as components

from frontend.ui_components import (
    render_section_header, render_status_pill, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_reports():
    render_section_header(
        "Diagnostic Engineering Validation Reports",
        "Formal ISO 14229-1 verification reports, ASPICE traceability documentation, and HIL sign-off archives"
    )

    c1, c2, c3 = st.columns([1.5, 1.5, 1])
    with c1:
        st.selectbox("Target ECU System", ["BCM-Demo-ECU (Body Control Module)"], key="rep_ecu")
    with c2:
        st.selectbox("Verification Release", ["Release 1.0.0 (Candidate Final)"], key="rep_rel")
    with c3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        generate_btn = st.button("Generate Report", type="primary", use_container_width=True)

    if generate_btn or "last_report_md" not in st.session_state:
        try:
            res_md = requests.get(f"{API_URL}/api/reports/engineering", timeout=5.0)
            if res_md.status_code == 200:
                st.session_state["last_report_md"] = res_md.text
            res_html = requests.get(f"{API_URL}/api/reports/html", timeout=5.0)
            if res_html.status_code == 200:
                st.session_state["last_report_html"] = res_html.text
            res_sum = requests.get(f"{API_URL}/api/reports/summary", timeout=5.0)
            if res_sum.status_code == 200:
                st.session_state["last_report_json"] = json.dumps(res_sum.json(), indent=2)
        except Exception as e:
            st.error(f"Report generation error: {e}")

    if "last_report_md" in st.session_state:
        rep_md = st.session_state["last_report_md"]
        rep_html = st.session_state.get("last_report_html", "")
        rep_json = st.session_state.get("last_report_json", "{}")

        # Download Buttons Toolbar
        col_d1, col_d2, col_d3, col_sp = st.columns([1.5, 1.5, 1.5, 2.5])
        with col_d1:
            st.download_button(
                label="Download Markdown (.md)",
                data=rep_md,
                file_name="DiagGenAI_Engineering_Report.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col_d2:
            st.download_button(
                label="Download HTML Print (.html)",
                data=rep_html,
                file_name="DiagGenAI_Engineering_Report.html",
                mime="text/html",
                use_container_width=True
            )
        with col_d3:
            st.download_button(
                label="Download Metrics (.json)",
                data=rep_json,
                file_name="DiagGenAI_Summary.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        tab_view_md, tab_view_html, tab_view_json = st.tabs([
            "Markdown Report",
            "Printable HTML View",
            "JSON Metrics"
        ])

        with tab_view_md:
            st.markdown(rep_md)

        with tab_view_html:
            components.html(rep_html, height=700, scrolling=True)

        with tab_view_json:
            st.json(json.loads(rep_json))
