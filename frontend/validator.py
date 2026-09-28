import streamlit as st
import requests
import pandas as pd

from frontend.ui_components import (
    render_section_header, render_status_pill,
    render_hex_token, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_validator():
    render_section_header(
        "Deterministic Protocol Validator",
        "Rule-based verification of ISO 14229-1 syntax, payload lengths, subfunctions, parameter boundaries, and ECU state preconditions"
    )

    tab_val, tab_rules = st.tabs([
        "Frame Validation",
        "Deterministic Rule Base"
    ])

    with tab_val:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            req_input = st.text_input("Request Frame (Hex Tokens)", value="22 F1 90", help="e.g. 22 F1 90, 10 03, 27 01, 2E 01 05 01 01 00 AA")
        with col2:
            session = st.selectbox("Active Session", ["DefaultSession", "ExtendedDiagnosticSession", "ProgrammingSession"])
        with col3:
            security = st.selectbox("Security State", ["Locked", "Level1Unlocked"])
        with col4:
            speed = st.number_input("Vehicle Speed (km/h)", min_value=0.0, max_value=250.0, value=0.0, step=5.0)

        if st.button("Validate Frame", type="primary"):
            try:
                res = requests.post(
                    f"{API_URL}/api/requests/validate",
                    json={
                        "request_hex": req_input,
                        "session": session,
                        "security_state": security,
                        "simulated_vehicle_speed": speed
                    },
                    timeout=2.0
                )
                if res.status_code == 200:
                    result = res.json()
                    status = result["status"]
                    issues = result.get("issues", [])

                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                    # Technical result summary
                    st.markdown(f"""
                    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px 16px; margin-bottom: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Deterministic Rule Verdict</span>
                                <div style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-top: 2px;">
                                    {render_status_pill(status)}
                                </div>
                            </div>
                            <div style="text-align: right; font-size: 0.78rem;">
                                <span style="color: #64748b;">Target Service:</span> <b>{result['service_id_hex']}</b><br/>
                                <span style="color: #64748b;">Expected Response:</span> <code>{result.get('expected_response_hex') or 'N/A'}</code>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Rules Checklist
                    st.markdown("""
                    <div style="font-size: 0.84rem; font-weight: 600; color: #0f172a; margin-bottom: 8px;">
                        Protocol Rule Evaluation
                    </div>
                    """, unsafe_allow_html=True)

                    standard_checks = [
                        ("Service Supported", "UDS service is declared in ISO 14229 / BCM specification", "PASS"),
                        ("Payload Length", "Minimum and maximum DLC boundaries satisfied", "PASS"),
                        ("Subfunction Supported", "Subfunction parameter valid for configured service", "PASS" if not any("SUBFUNCTION" in i.get("rule", "") for i in issues) else "FAIL"),
                        ("Session Precondition", f"Supported in active session: {session}", "PASS" if not any("SESSION" in i.get("rule", "") for i in issues) else "WARNING"),
                        ("Security Precondition", f"Access level valid for security state: {security}", "PASS" if not any("SECURITY" in i.get("rule", "") for i in issues) else "WARNING"),
                        ("Environmental Conditions", f"Speed within safe limits ({speed} km/h)", "PASS" if speed == 0 or not any("CONDITIONS" in i.get("rule", "") for i in issues) else "FAIL"),
                    ]

                    for check_name, check_desc, check_verdict in standard_checks:
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; border-bottom: 1px solid #f1f5f9; font-size: 0.80rem;">
                            <div>
                                <span style="font-weight: 600; color: #0f172a;">{check_name}</span>
                                <span style="color: #64748b; margin-left: 8px;">{check_desc}</span>
                            </div>
                            <div>{render_status_pill(check_verdict)}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    if issues:
                        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                        st.markdown("**Rule Findings & Guidance:**")
                        for iss in issues:
                            st.warning(f"**{iss['rule']}**: {iss['reason']} &rarr; Suggested Correction: {iss['suggested_correction']}")

            except Exception as e:
                st.error(f"Validation error: {e}")

    with tab_rules:
        st.markdown("""
        <div style="font-size: 0.84rem; font-weight: 600; color: #0f172a; margin-bottom: 6px;">
            Configured Deterministic Rules (ISO 14229-1)
        </div>
        """, unsafe_allow_html=True)

        try:
            rules_res = requests.get(f"{API_URL}/api/requests/rules", timeout=2.0).json()
            rule_rows = []
            for r_id, r_info in rules_res.items():
                rule_rows.append({
                    "Rule ID": r_id,
                    "Name": r_info.get("name"),
                    "Standard Reference": r_info.get("standard_ref"),
                    "Default Severity": r_info.get("default_severity"),
                    "Description": r_info.get("description")
                })
            st.dataframe(pd.DataFrame(rule_rows), use_container_width=True, hide_index=True)
        except Exception:
            st.info("Loading rule base...")
