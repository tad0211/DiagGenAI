"""
DiagGenAI - Mock ECU Simulator & Test Execution Frontend Modules.
Clean, mature engineering simulator and automated test execution suite.
"""

import streamlit as st
import requests
import datetime
import json
import pandas as pd
from typing import Dict, Any, List

from frontend.ui_components import (
    render_section_header, render_status_pill,
    render_can_trace, render_hex_token, get_icon
)

API_URL = "http://127.0.0.1:8000"

PRESET_FRAMES = [
    ("Extended Session (0x10 0x03)", "10 03"),
    ("Read VIN DID (0x22 0xF190)", "22 F1 90"),
    ("Read Battery Voltage (0x22 0x0300)", "22 03 00"),
    ("Security Access Seed (0x27 0x01)", "27 01"),
    ("Routine Control SelfTest (0x31 0x01 0x0201)", "31 01 02 01"),
    ("ECU Hard Reset (0x11 0x01)", "11 01")
]

# ==================== MODULE 1: MOCK ECU SIMULATOR ====================
def render_simulator():
    render_section_header(
        "Mock ECU Simulation Workbench",
        "Stateful ISO 14229-1 Diagnostic Server (BCM-Demo-ECU) with active session management, seed/key security, and environmental controls"
    )

    # Fetch current ECU State
    ecu_state = {}
    try:
        res = requests.get(f"{API_URL}/api/simulator/state", timeout=2.0)
        if res.status_code == 200:
            ecu_state = res.json()
    except Exception:
        from app.uds.ecu_simulator import global_ecu_simulator
        ecu_state = global_ecu_simulator.get_state()

    active_sess = ecu_state.get("active_session", "DefaultSession")
    active_sec = ecu_state.get("active_security", "Locked")
    speed = ecu_state.get("vehicle_speed_kmh", 0.0)
    voltage = ecu_state.get("battery_voltage_v", 12.5)

    # Clean Instrument Panel (Non-card, subtle row)
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: baseline; padding: 12px 16px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 20px;">
        <div>
            <div style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Active Session</div>
            <div style="font-size: 1.05rem; font-weight: 600; color: #0f172a; margin-top: 2px;">{active_sess}</div>
        </div>
        <div style="width: 1px; height: 30px; background: #e2e8f0;"></div>
        <div>
            <div style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Security State</div>
            <div style="font-size: 1.05rem; font-weight: 600; color: {'#166534' if 'Unlocked' in active_sec else '#92400e'}; margin-top: 2px;">{active_sec}</div>
        </div>
        <div style="width: 1px; height: 30px; background: #e2e8f0;"></div>
        <div>
            <div style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Vehicle Speed</div>
            <div style="font-size: 1.05rem; font-weight: 600; font-family: 'JetBrains Mono', monospace; color: #0f172a; margin-top: 2px;">{speed:.1f} km/h</div>
        </div>
        <div style="width: 1px; height: 30px; background: #e2e8f0;"></div>
        <div>
            <div style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Battery Voltage</div>
            <div style="font-size: 1.05rem; font-weight: 600; font-family: 'JetBrains Mono', monospace; color: #0f172a; margin-top: 2px;">{voltage:.2f} V</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_tx, col_env = st.columns([1.5, 1])

    with col_tx:
        st.markdown("""
        <div style="font-size: 0.84rem; font-weight: 600; color: #0f172a; margin-bottom: 6px;">
            Transmit Diagnostic Request
        </div>
        """, unsafe_allow_html=True)

        preset_choice = st.selectbox(
            "Diagnostic Preset",
            ["-- Manual Entry --"] + [p[0] for p in PRESET_FRAMES]
        )

        preset_val = "10 03"
        for label, val in PRESET_FRAMES:
            if label == preset_choice:
                preset_val = val
                break

        req_hex = st.text_input("Request Frame (Hex Bytes)", value=preset_val)

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fault_mode = st.selectbox(
                "Fault Injection Mode",
                [
                    "None (Nominal Execution)",
                    "TIMEOUT (P2 Timer Expiry)",
                    "NRC_22_CONDITIONS (Speed > 0 violation)",
                    "GARBAGE_RESPONSE (Bus Corruption)"
                ]
            )
            fault_key = None if fault_mode.startswith("None") else fault_mode.split()[0]
        with col_f2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            send_btn = st.button("Transmit Frame", type="primary", use_container_width=True)

    with col_env:
        st.markdown("""
        <div style="font-size: 0.84rem; font-weight: 600; color: #0f172a; margin-bottom: 6px;">
            Environmental Controls
        </div>
        """, unsafe_allow_html=True)

        new_speed = st.slider("Vehicle Speed (km/h)", 0.0, 140.0, float(speed), step=5.0)
        new_voltage = st.slider("Battery Voltage (V)", 9.0, 16.0, float(voltage), step=0.1)

        c_e1, c_e2 = st.columns(2)
        with c_e1:
            if st.button("Apply Conditions", use_container_width=True):
                try:
                    requests.post(f"{API_URL}/api/simulator/environmental", json={"vehicle_speed_kmh": new_speed, "battery_voltage_v": new_voltage})
                except Exception:
                    from app.uds.ecu_simulator import global_ecu_simulator
                    global_ecu_simulator.set_environmental(speed_kmh=new_speed, voltage_v=new_voltage)
                st.rerun()
        with c_e2:
            if st.button("Reset ECU State", use_container_width=True):
                try:
                    requests.post(f"{API_URL}/api/simulator/reset")
                except Exception:
                    from app.uds.ecu_simulator import global_ecu_simulator
                    global_ecu_simulator.reset()
                st.rerun()

    if send_btn:
        with st.spinner("Transmitting frame on virtual CAN bus..."):
            try:
                res = requests.post(f"{API_URL}/api/simulator/send", json={"request_hex": req_hex, "inject_fault": fault_key}, timeout=5.0)
                sim_res = res.json()
            except Exception:
                from app.uds.ecu_simulator import global_ecu_simulator
                sim_res = global_ecu_simulator.process_request(request_hex=req_hex, inject_fault=fault_key).dict()

            st.session_state["last_sim_trace"] = sim_res

    # Render Simulation Result & CAN Trace
    if "last_sim_trace" in st.session_state and st.session_state["last_sim_trace"]:
        sim_data = st.session_state["last_sim_trace"]
        now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:12]
        rx_hex = sim_data.get("response_hex", "")
        rtype = sim_data.get("response_type", "POSITIVE")
        req_h = sim_data.get("request_hex", "")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div>
                    <span style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">ECU Response</span>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: {'#166534' if rtype=='POSITIVE' else '#991b1b'}; margin-top: 2px;">
                        {rx_hex or '[NO RESPONSE / TIMEOUT]'}
                    </div>
                </div>
                <div style="font-size: 0.76rem; color: #64748b;">
                    Verdict: {render_status_pill(rtype)} &bull; Latency: <b>{sim_data.get('execution_time_ms', 0):.1f} ms</b>
                </div>
            </div>
            <div style="font-size: 0.80rem; color: #475569; margin-top: 6px;">
                {sim_data.get('explanation', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="can-trace-box" style="height: 130px;">
        """ +
        render_can_trace(now_str, "Tx", "0x7E0", len(req_h.replace(' ',''))//2, req_h, "Tester Request") +
        render_can_trace(now_str, "Rx", "0x7E8", len(rx_hex.replace(' ',''))//2 if rx_hex else 0, rx_hex or "[NO DATA]", f"{rtype} Response") +
        """
        </div>
        """, unsafe_allow_html=True)


# ==================== MODULE 2: TEST EXECUTION ====================
def render_test_execution():
    render_section_header(
        "Automated Test Execution Runner",
        "Execute test suites against the simulated BCM-Demo-ECU with pass/fail verdict evaluation and difference analysis"
    )

    tab_run, tab_single, tab_hist = st.tabs([
        "Suite Execution",
        "Single Test Run",
        "Execution History"
    ])

    with tab_run:
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            exec_scope = st.selectbox(
                "Execution Target",
                [
                    "APPROVED_ONLY (Production Ready - Approved by Lead)",
                    "ALL_TESTS (Full Repository Suite)",
                    "POSITIVE_ONLY (Nominal Execution Only)",
                    "NEGATIVE_ONLY (Robustness & Fault Injection Only)"
                ]
            )
            scope_key = exec_scope.split()[0]
        with col_s2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            run_btn = st.button("Execute Suite", type="primary", use_container_width=True)

        if run_btn:
            with st.spinner("Executing test suite against Mock ECU via ISO-TP..."):
                try:
                    res = requests.post(f"{API_URL}/api/simulator/run-suite", json={"scope": scope_key}, timeout=25.0)
                    st.session_state["last_suite_summary"] = res.json()
                except Exception:
                    from app.testing.executor import TestExecutor
                    st.session_state["last_suite_summary"] = TestExecutor().execute_suite(scope=scope_key)

        if "last_suite_summary" in st.session_state:
            summary = st.session_state["last_suite_summary"]
            tot = summary.get("total_executed", 0)
            pas = summary.get("passed", 0)
            fai = summary.get("failed", 0)
            pass_rate = (pas / tot * 100) if tot > 0 else 0

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 12px 16px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; margin: 16px 0;">
                <div><span style="font-size:0.70rem; color:#64748b;">TOTAL EXECUTED:</span> <b>{tot}</b></div>
                <div><span style="font-size:0.70rem; color:#64748b;">PASSED:</span> <b style="color:#166534;">{pas}</b></div>
                <div><span style="font-size:0.70rem; color:#64748b;">FAILED:</span> <b style="color:{'#991b1b' if fai > 0 else '#64748b'};">{fai}</b></div>
                <div><span style="font-size:0.70rem; color:#64748b;">PASS RATE:</span> <b>{pass_rate:.1f}%</b></div>
            </div>
            """, unsafe_allow_html=True)

            results = summary.get("results", [])
            for r in results:
                outcome = r.get("outcome", "PASS")
                tid = r.get("test_id", "")
                req_hex = r.get("request_sent_hex", "")
                act_hex = r.get("actual_response_hex", "")
                exp_hex = r.get("expected_response_hex", "")
                diff = r.get("diff_analysis", "")
                expl = r.get("explanation", "")

                with st.expander(f"{tid} &bull; {outcome} &bull; Tx: {req_hex} &rarr; Rx: {act_hex}", expanded=(outcome=="FAIL")):
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        st.markdown(f"**Request (Tx):** `{req_hex}`")
                        st.markdown(f"**Expected (Rx):** `{exp_hex}`")
                        st.markdown(f"**Actual (Rx):** `{act_hex}`")
                    with col_r2:
                        st.markdown(f"**Verdict:** {render_status_pill(outcome)}", unsafe_allow_html=True)
                        st.markdown(f"**Difference Analysis:** {diff}")
                        st.markdown(f"**Root Cause:** *{expl}*")

    with tab_single:
        all_tcs = []
        try:
            res = requests.get(f"{API_URL}/api/tests", timeout=5.0)
            if res.status_code == 200:
                all_tcs = res.json()
        except Exception:
            from app.database.repository import DiagRepository
            all_tcs = [t.__dict__ for t in DiagRepository().get_test_cases()]

        if all_tcs:
            tc_options = [f"{t['test_id']} - {t['objective'][:65]}" for t in all_tcs]
            selected_idx = st.selectbox("Select Test Case", range(len(tc_options)), format_func=lambda i: tc_options[i])
            chosen_tc = all_tcs[selected_idx]

            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 14px; margin-bottom: 12px; font-size: 0.80rem;">
                <div><b>Objective:</b> {chosen_tc['objective']}</div>
                <div style="margin-top: 4px;"><b>Request (Tx):</b> <code>{chosen_tc['request_hex']}</code> &bull; <b>Expected (Rx):</b> <code>{chosen_tc['expected_response_hex']}</code></div>
                <div style="margin-top: 4px; color: #64748b;">Preconditions: {chosen_tc['preconditions']} &bull; Session: {chosen_tc['session']} &bull; Security: {chosen_tc['security_state']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Execute Test", type="primary"):
                try:
                    res = requests.post(f"{API_URL}/api/simulator/execute-test", json={"test_id": chosen_tc["test_id"]}, timeout=5.0)
                    s_res = res.json()
                except Exception:
                    from app.testing.executor import TestExecutor
                    from app.database.repository import DiagRepository
                    tc_obj = DiagRepository().get_test_case_by_id(chosen_tc["test_id"])
                    s_res = TestExecutor().execute_test(tc_obj)

                out = s_res.get("outcome", "PASS")
                st.markdown(f"**Execution Outcome:** {render_status_pill(out)} &bull; Actual: `{s_res.get('actual_response_hex')}`", unsafe_allow_html=True)
                st.caption(f"Analysis: {s_res.get('diff_analysis')} — {s_res.get('explanation')}")

    with tab_hist:
        history_records = []
        try:
            res = requests.get(f"{API_URL}/api/simulator/results?limit=50", timeout=5.0)
            if res.status_code == 200:
                history_records = res.json()
        except Exception:
            from app.database.repository import DiagRepository
            history_records = [r.__dict__ for r in DiagRepository().get_test_results(limit=50)]

        if history_records:
            df_hist = pd.DataFrame(history_records)[["execution_timestamp", "outcome", "request_sent_hex", "expected_response_hex", "actual_response_hex", "diff_analysis"]]
            df_hist.columns = ["Timestamp", "Verdict", "Request (Tx)", "Expected (Rx)", "Actual (Rx)", "Difference Analysis"]
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("No execution records found.")

def render_can_trace_monitor():
    render_section_header("CAN Trace Protocol Monitor", "Virtual CAN bus frame stream (vcan0)")
    st.markdown("""
    <div class="can-trace-box" style="height: 380px;">
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
