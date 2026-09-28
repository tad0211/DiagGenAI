"""
DiagGenAI - Automation Template Generator Frontend Module.
Exports validated diagnostic test cases and full test suites directly into:
- Python (python-can + ISO-TP + PyTest)
- Vector CANoe CAPL (.can)
- Generic Automation (YAML / Robot Framework)
- Automotive Verification Matrix (CSV)
"""

import streamlit as st
import requests
import json

from frontend.ui_components import (
    render_section_header, render_status_pill,
    render_hex_token, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_automation():
    render_section_header(
        "Automation Script & Suite Exporter",
        "Export validated diagnostic test cases directly to Vector CANoe (CAPL), Python pyUDS/python-can, Robot Framework, and CSV verification matrices"
    )

    tab_single, tab_suite = st.tabs([
        "Single Test Case Export",
        "Full Test Suite Archive"
    ])

    # Load test cases
    tests = []
    try:
        res = requests.get(f"{API_URL}/api/tests", timeout=3.0)
        if res.status_code == 200:
            tests = res.json()
    except Exception:
        from app.database.repository import DiagRepository
        tests = [t.__dict__ for t in DiagRepository().get_test_cases()]

    if not tests:
        st.warning("No test cases found in repository to generate templates.")
        return

    # ==================== TAB 1: SINGLE TEST EXPORT ====================
    with tab_single:
        col_t1, col_t2 = st.columns([2.5, 1.5])
        with col_t1:
            test_map = {f"{t['test_id']} - {t['objective'][:65]}": t['test_id'] for t in tests}
            selected_label = st.selectbox("Select Diagnostic Test Case", list(test_map.keys()), key="auto_single_tc")
            test_id = test_map[selected_label]
        with col_t2:
            target_fmt = st.selectbox("Toolchain Format", ["PYTHON (python-can / ISO-TP)", "CAPL (Vector CANoe)", "GENERIC (YAML / Robot)", "CSV (Matrix Row)"], key="auto_single_fmt")
            fmt_key = "PYTHON" if "PYTHON" in target_fmt else ("CAPL" if "CAPL" in target_fmt else ("CSV" if "CSV" in target_fmt else "GENERIC"))

        if st.button("Generate Script", type="primary"):
            with st.spinner(f"Synthesizing {fmt_key} automation script for {test_id}..."):
                try:
                    res = requests.post(
                        f"{API_URL}/api/automation/generate",
                        json={"test_id": test_id, "template_type": fmt_key},
                        timeout=5.0
                    )
                    if res.status_code == 200:
                        st.session_state["single_template_output"] = res.json()
                except Exception as e:
                    st.error(f"Generation error: {e}")

        if "single_template_output" in st.session_state and st.session_state["single_template_output"]:
            out = st.session_state["single_template_output"]
            code = out.get("code_content", "")
            fname = out.get("filename", "test.py")
            ttype = out.get("template_type", "PYTHON")

            lang_map = {"PYTHON": "python", "CAPL": "c", "GENERIC": "yaml", "CSV": "text"}
            st.markdown(f"**Generated Script:** `{fname}` ({ttype})")
            st.code(code, language=lang_map.get(ttype, "python"))

            st.download_button(
                label=f"Download {fname}",
                data=code,
                file_name=fname,
                mime="text/plain"
            )

    # ==================== TAB 2: SUITE EXPORT ====================
    with tab_suite:
        col_st1, col_st2, col_st3 = st.columns([1.5, 1.5, 1.5])
        with col_st1:
            suite_scope = st.selectbox("Suite Scope", ["All Test Cases", "Approved Only", "Pending Review Only"], key="suite_scope")
            status_filter = None
            if suite_scope == "Approved Only": status_filter = "APPROVED"
            elif suite_scope == "Pending Review Only": status_filter = "PENDING_REVIEW"
        with col_st2:
            suite_srv = st.selectbox("Target Service", ["All Services", "0x10", "0x11", "0x22", "0x27", "0x2E", "0x31"], key="suite_srv")
            srv_filter = None if suite_srv == "All Services" else suite_srv
        with col_st3:
            suite_fmt = st.selectbox("Export Toolchain", ["PYTHON (PyTest Suite)", "CAPL (Vector CANoe Suite)", "CSV (Full Test Matrix)", "GENERIC (YAML Suite)"], key="suite_fmt")
            suite_fmt_key = "PYTHON" if "PYTHON" in suite_fmt else ("CAPL" if "CAPL" in suite_fmt else ("CSV" if "CSV" in suite_fmt else "GENERIC"))

        if st.button("Generate Suite Archive", type="primary"):
            with st.spinner(f"Compiling consolidated {suite_fmt_key} suite..."):
                try:
                    res = requests.post(
                        f"{API_URL}/api/automation/generate-suite",
                        json={"template_type": suite_fmt_key, "review_status": status_filter, "service_hex": srv_filter},
                        timeout=10.0
                    )
                    if res.status_code == 200:
                        st.session_state["suite_template_output"] = res.json()
                        st.toast("Consolidated test suite compiled.")
                    else:
                        st.error(f"Failed: {res.text}")
                except Exception as e:
                    st.error(f"Generation error: {e}")

        if "suite_template_output" in st.session_state and st.session_state["suite_template_output"]:
            s_out = st.session_state["suite_template_output"]
            s_code = s_out.get("code_content", "")
            s_fname = s_out.get("filename", "suite.py")
            s_ttype = s_out.get("template_type", "PYTHON")

            st.markdown(f"**Consolidated Archive:** `{s_fname}`")
            s_lang = "python" if s_ttype == "PYTHON" else ("c" if s_ttype == "CAPL" else ("yaml" if s_ttype == "GENERIC" else "text"))
            st.code(s_code[:3000] + ("\n... [Truncated preview for display] ..." if len(s_code) > 3000 else ""), language=s_lang)

            st.download_button(
                label=f"Download {s_fname}",
                data=s_code,
                file_name=s_fname,
                mime="text/plain"
            )
