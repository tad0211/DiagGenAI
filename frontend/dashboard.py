import sys
from pathlib import Path

# Ensure project root and frontend directories are always on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = Path(__file__).resolve().parent
for p in [str(BASE_DIR), str(FRONTEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

try:
    from frontend.ui_components import (
        inject_automotive_theme, render_global_header,
        render_section_header, render_status_pill,
        render_coverage_bar, render_can_trace,
        render_hex_token, get_icon
    )
except (ImportError, ModuleNotFoundError):
    from ui_components import (
        inject_automotive_theme, render_global_header,
        render_section_header, render_status_pill,
        render_coverage_bar, render_can_trace,
        render_hex_token, get_icon
    )

# Page Configuration
st.set_page_config(
    page_title="DiagGenAI — Automotive Diagnostic Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Clean Enterprise Styling
inject_automotive_theme()

API_URL = "http://127.0.0.1:8000"

def get_api_data(endpoint: str):
    try:
        res = requests.get(f"{API_URL}{endpoint}", timeout=2.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

# Fetch current ECU telemetry state
ecu_state = get_api_data("/api/simulator/state") or {}
active_session = ecu_state.get("active_session", "DefaultSession")
active_security = ecu_state.get("active_security", "Locked")

# Render Clean Top Header
render_global_header(
    target_ecu="BCM-Demo-ECU",
    active_session=active_session,
    security_state=active_security
)

# Navigation Items
NAVIGATION_ITEMS = [
    "Overview",
    "Knowledge Base",
    "RAG Assistant",
    "UDS Explorer",
    "Request Builder",
    "Protocol Validator",
    "AI Test Generator",
    "Coverage Analyzer",
    "Mock ECU",
    "Test Execution",
    "Traceability",
    "Automation",
    "Change Impact",
    "Human Review",
    "Reports"
]

if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "Overview"

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("""
    <div style="padding: 4px 6px 14px 6px; border-bottom: 1px solid #e2e8f0; margin-bottom: 14px;">
        <div style="font-size: 0.92rem; font-weight: 700; color: #0f172a; letter-spacing: 0.4px;">
            DIAGGENAI
        </div>
        <div style="font-size: 0.72rem; color: #64748b; font-weight: 500; margin-top: 1px;">
            Automotive Diagnostic Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    curr_idx = NAVIGATION_ITEMS.index(st.session_state["active_nav"]) if st.session_state["active_nav"] in NAVIGATION_ITEMS else 0

    module = st.radio(
        "Navigation",
        NAVIGATION_ITEMS,
        index=curr_idx,
        label_visibility="collapsed"
    )
    st.session_state["active_nav"] = module

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    st.divider()

    # Subtle environment indicator in sidebar
    st.markdown("""
    <div style="padding: 8px 6px; font-size: 0.72rem; color: #64748b; line-height: 1.5;">
        <div><b>Target:</b> BCM-Demo-ECU</div>
        <div><b>Environment:</b> Virtual ECU</div>
        <div><b>Transport:</b> ISO-TP / CAN-FD</div>
        <div style="color: #92400e; margin-top: 6px; font-weight: 500;">
            No physical connection
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==================== MODULE: OVERVIEW ====================
if module == "Overview":
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="font-size: 1.30rem; font-weight: 700; color: #0f172a; letter-spacing: -0.2px;">
            Diagnostic Engineering
        </div>
        <div style="font-size: 0.82rem; color: #64748b; margin-top: 2px;">
            BCM-Demo-ECU &bull; Simulation Environment &bull; ISO 14229-1 Compliance Status
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Fetch Platform Metrics
    cov_data = get_api_data("/api/coverage") or {}
    docs = get_api_data("/api/documents") or []
    services = get_api_data("/api/services") or []
    tests = get_api_data("/api/tests") or []

    approved_cnt = sum(1 for t in tests if t.get("review_status") == "APPROVED")
    pending_cnt = sum(1 for t in tests if t.get("review_status") == "PENDING_REVIEW")
    overall_cov = float(cov_data.get("overall_coverage", 58.0))

    # Refined Summary Row (Integrated into page, non-card)
    st.markdown(f"""
    <div class="summary-metric-row">
        <div class="summary-metric-item">
            <span class="summary-metric-label">Specifications</span>
            <span class="summary-metric-value">{len(docs):02d}</span>
            <span class="summary-metric-caption">Indexed documents</span>
        </div>
        <div style="width: 1px; height: 36px; background: #e2e8f0;"></div>
        <div class="summary-metric-item">
            <span class="summary-metric-label">UDS Services</span>
            <span class="summary-metric-value">{len(services):02d}</span>
            <span class="summary-metric-caption">Configured services</span>
        </div>
        <div style="width: 1px; height: 36px; background: #e2e8f0;"></div>
        <div class="summary-metric-item">
            <span class="summary-metric-label">Generated Tests</span>
            <span class="summary-metric-value">{len(tests):02d}</span>
            <span class="summary-metric-caption">Total test cases</span>
        </div>
        <div style="width: 1px; height: 36px; background: #e2e8f0;"></div>
        <div class="summary-metric-item">
            <span class="summary-metric-label">Approval</span>
            <span class="summary-metric-value" style="font-size: 1.15rem; margin-top: 4px;">{approved_cnt:02d} <span style="font-size:0.75rem; color:#64748b; font-weight:400;">approved</span> &bull; {pending_cnt:02d} <span style="font-size:0.75rem; color:#92400e; font-weight:400;">pending</span></span>
            <span class="summary-metric-caption">Human sign-off</span>
        </div>
        <div style="width: 1px; height: 36px; background: #e2e8f0;"></div>
        <div class="summary-metric-item">
            <span class="summary-metric-label">Suite Coverage</span>
            <span class="summary-metric-value" style="color: {'#166534' if overall_cov >= 75 else '#0f172a'};">{overall_cov:.1f}%</span>
            <span class="summary-metric-caption">ISO 14229 benchmark</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_cov, col_trace = st.columns([1.1, 1])

    with col_cov:
        st.markdown("""
        <div style="font-size: 0.88rem; font-weight: 600; color: #0f172a; margin-bottom: 8px;">
            Diagnostic Coverage
        </div>
        """, unsafe_allow_html=True)

        render_coverage_bar("Requirements", float(cov_data.get("req_coverage", 58.3)), "Traceability")
        render_coverage_bar("Services", float(cov_data.get("service_coverage", 100.0)), "Configured")
        render_coverage_bar("Subfunctions", float(cov_data.get("subfunction_coverage", 80.0)), "Subfunctions")
        render_coverage_bar("Positive paths", float(cov_data.get("positive_coverage", 71.4)), "Standard")
        render_coverage_bar("Negative paths", float(cov_data.get("negative_coverage", 57.1)), "NRC Robustness")
        render_coverage_bar("Session", float(cov_data.get("session_coverage", 60.0)), "Transitions")
        render_coverage_bar("Security", float(cov_data.get("security_coverage", 50.0)), "Seed / Key")
        render_coverage_bar("Boundary", float(cov_data.get("boundary_coverage", 33.3)), "Range Limits")

    with col_trace:
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
            <span style="font-size: 0.88rem; font-weight: 600; color: #0f172a;">Virtual CAN Bus Activity</span>
            <span style="font-size: 0.72rem; color: #64748b;">Interface: vcan0 &bull; 500 kbps</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="can-trace-box" style="height: 250px;">
        """ +
        render_can_trace("10:42:01.120", "Tx", "0x7E0", 2, "10 03", "DiagnosticSessionControl (Extended)") +
        render_can_trace("10:42:01.142", "Rx", "0x7E8", 6, "50 03 00 32 01 F4", "PosRsp [P2=50ms, P2*=5000ms]") +
        render_can_trace("10:42:01.215", "Tx", "0x7E0", 3, "22 F1 90", "ReadDataByIdentifier (VIN)") +
        render_can_trace("10:42:01.240", "Rx", "0x7E8", 20, "62 F1 90 44 45 4D ...", "PosRsp [DEMOVIN1234567890]") +
        render_can_trace("10:42:01.350", "Tx", "0x7E0", 2, "10 99", "DiagnosticSessionControl (Invalid SF 0x99)") +
        render_can_trace("10:42:01.365", "Rx", "0x7E8", 3, "7F 10 12", "NegativeResponse [NRC 0x12]") +
        render_can_trace("10:42:01.420", "Tx", "0x7E0", 2, "27 01", "SecurityAccess (RequestSeed Level 1)") +
        render_can_trace("10:42:01.435", "Rx", "0x7E8", 6, "67 01 A1 B2 C3 D4", "PosRsp [Seed: A1 B2 C3 D4]") +
        """
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Recent Test Activity
    st.markdown("""
    <div style="font-size: 0.92rem; font-weight: 600; color: #0f172a; margin-bottom: 8px;">
        Recent Test Activity
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        search_query = st.text_input("Filter test cases", "", placeholder="Search by Test ID, Service, or Objective...", label_visibility="collapsed")
    with f2:
        type_filter = st.selectbox("Type Filter", ["All Types", "POSITIVE", "NEGATIVE", "BOUNDARY"], label_visibility="collapsed")
    with f3:
        status_filter = st.selectbox("Status Filter", ["All Status", "APPROVED", "PENDING_REVIEW", "REJECTED"], label_visibility="collapsed")

    filtered_tests = tests
    if search_query:
        q = search_query.lower()
        filtered_tests = [t for t in filtered_tests if q in t.get("test_id", "").lower() or q in t.get("objective", "").lower() or q in t.get("service_id_hex", "").lower()]
    if type_filter != "All Types":
        filtered_tests = [t for t in filtered_tests if t.get("test_type") == type_filter]
    if status_filter != "All Status":
        filtered_tests = [t for t in filtered_tests if t.get("review_status") == status_filter]

    if filtered_tests:
        # Render clean interactive test table with expander details
        for t in filtered_tests[:12]:
            t_id = t.get("test_id", "")
            t_svc = t.get("service_id_hex", "")
            t_type = t.get("test_type", "")
            t_stat = t.get("review_status", "")
            t_obj = t.get("objective", "")
            t_req = t.get("request_hex", "")
            t_exp = t.get("expected_response_hex", "")

            with st.expander(f"{t_id}  &bull;  {t_svc}  &bull;  {t_type}  &bull;  {t_stat}  &bull;  {t_obj[:65]}...", expanded=False):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.markdown(f"**Test ID:** `{t_id}` &bull; **Type:** `{t_type}`")
                    st.markdown(f"**Objective:** {t_obj}")
                    st.markdown(f"**Preconditions:** {t.get('preconditions', 'DefaultSession, Engine Stopped')}")
                with col_d2:
                    st.markdown(f"**Request (Tx):** {render_hex_token(t_req)}", unsafe_allow_html=True)
                    st.markdown(f"**Expected (Rx):** {render_hex_token(t_exp)}", unsafe_allow_html=True)
                    st.markdown(f"**Status:** {render_status_pill(t_stat)}", unsafe_allow_html=True)

        if len(filtered_tests) > 12:
            st.caption(f"Showing 12 of {len(filtered_tests)} matching test cases.")
    else:
        st.info("No test cases match the active filter criteria.")


# ==================== MODULE ROUTING ====================
elif module == "Knowledge Base":
    from frontend.knowledge_base import render_knowledge_base
    render_knowledge_base()

elif module == "RAG Assistant":
    from frontend.rag_assistant import render_rag_assistant
    render_rag_assistant()

elif module == "UDS Explorer":
    from frontend.uds_explorer import render_uds_explorer
    render_uds_explorer()

elif module == "Request Builder":
    from frontend.request_builder import render_request_builder
    render_request_builder()

elif module == "Protocol Validator":
    from frontend.validator import render_validator
    render_validator()

elif module == "AI Test Generator":
    from frontend.test_generator import render_test_generator
    render_test_generator()

elif module == "Coverage Analyzer":
    from frontend.coverage import render_coverage_analyzer
    render_coverage_analyzer()

elif module == "Mock ECU":
    from frontend.simulator import render_simulator
    render_simulator()

elif module == "Test Execution":
    from frontend.simulator import render_test_execution
    render_test_execution()

elif module == "Traceability":
    from frontend.traceability import render_traceability
    render_traceability()

elif module == "Automation":
    from frontend.automation import render_automation
    render_automation()

elif module == "Change Impact":
    from frontend.change_impact import render_change_impact
    render_change_impact(default_tab_idx=0)

elif module == "Human Review":
    from frontend.human_review import render_human_review
    render_human_review()

elif module == "Reports":
    from frontend.reports import render_reports
    render_reports()
