import streamlit as st
import requests
import pandas as pd

from frontend.ui_components import (
    render_section_header, render_status_pill,
    render_hex_token, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_uds_explorer():
    render_section_header(
        "UDS Service Specification Browser",
        "ISO 14229-1 standard definitions, subfunctions, Data Identifiers (DIDs), prerequisites, and linked tests"
    )

    try:
        res = requests.get(f"{API_URL}/api/services", timeout=2.0)
        services = res.json() if res.status_code == 200 else []
    except Exception:
        services = []

    if not services:
        st.warning("No services available from backend API.")
        return

    # Two-Column Technical Specification Browser
    col_left, col_right = st.columns([1, 2.5])

    with col_left:
        st.markdown("""
        <div style="font-size: 0.82rem; font-weight: 600; color: #0f172a; margin-bottom: 6px;">
            Services Catalog
        </div>
        """, unsafe_allow_html=True)

        service_labels = [f"{s['service_id_hex']}  {s['name']}" for s in services]
        selected_idx = st.radio(
            "Services",
            range(len(service_labels)),
            format_func=lambda i: service_labels[i],
            label_visibility="collapsed"
        )
        s = services[selected_idx]

    with col_right:
        # Fetch live coverage for this specific service
        cov_info = {}
        try:
            cov_res = requests.get(f"{API_URL}/api/services/{s['service_id_hex']}/coverage", timeout=2.0)
            if cov_res.status_code == 200:
                cov_info = cov_res.json()
        except Exception:
            pass

        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #1e3a8a;">
                        {s['service_id_hex']}
                    </span>
                    <span style="font-size: 1.05rem; font-weight: 600; color: #0f172a; margin-left: 8px;">
                        {s['name']}
                    </span>
                </div>
                <div style="font-size: 0.76rem; color: #64748b;">
                    Standard: <b>{s['standard_ref']}</b>
                </div>
            </div>
            <div style="font-size: 0.84rem; color: #334155; margin-top: 8px; line-height: 1.5;">
                {s['description']}
            </div>
            <div style="display: flex; gap: 24px; margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9; font-size: 0.78rem;">
                <div><span style="color:#64748b;">Required Session:</span> <b>{s['session_prereq']}</b></div>
                <div><span style="color:#64748b;">Required Security:</span> <b>{s['security_prereq']}</b></div>
                <div><span style="color:#64748b;">Positive Response SID:</span> <code style="font-size:0.78rem;">{s.get('positive_response_sid_hex') or 'N/A'}</code></div>
                <div><span style="color:#64748b;">Tests:</span> <b>{cov_info.get('total_tests', 0)}</b> ({cov_info.get('approved_tests', 0)} approved)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_sf, tab_did, tab_tests = st.tabs([
            "Subfunctions",
            "Parameters & DIDs",
            "Linked Test Cases"
        ])

        with tab_sf:
            if s["subfunctions"]:
                df_sf = pd.DataFrame(s["subfunctions"])[["subfunction_hex", "name", "session_prereq", "security_prereq", "description"]]
                df_sf.columns = ["Subfunction", "Name", "Session", "Security", "Description"]
                st.dataframe(df_sf, use_container_width=True, hide_index=True)
            else:
                st.info("No subfunctions defined for this service (direct parameter/DID access).")

        with tab_did:
            if s["parameters"]:
                df_params = pd.DataFrame(s["parameters"])[["param_name", "did_hex", "length_bytes", "data_type", "min_value", "max_value", "description"]]
                df_params.columns = ["Parameter", "DID", "Length (Bytes)", "Type", "Min", "Max", "Description"]
                st.dataframe(df_params, use_container_width=True, hide_index=True)
            else:
                st.info("No specific parameters or DIDs configured for this service.")

        with tab_tests:
            test_cases = cov_info.get("test_cases", [])
            if test_cases:
                st.caption(f"{len(test_cases)} test cases configured for Service {s['service_id_hex']}:")
                df_tc = pd.DataFrame(test_cases)[["test_id", "test_type", "review_status", "request_hex", "expected_response_hex", "objective"]]
                df_tc.columns = ["Test ID", "Type", "Status", "Request (Tx)", "Expected (Rx)", "Objective"]
                st.dataframe(df_tc, use_container_width=True, hide_index=True)
            else:
                st.info("No test cases currently linked to this service.")
