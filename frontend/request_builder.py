import streamlit as st
import requests

from frontend.ui_components import (
    render_section_header, render_status_pill,
    render_hex_token, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_request_builder():
    render_section_header(
        "Request Builder & Parameter Configurator",
        "Assemble ISO 14229-1 diagnostic frames, configure target preconditions, and validate frame structure"
    )

    col_cfg, col_prev = st.columns([1.2, 1])

    with col_cfg:
        st.markdown("""
        <div style="font-size: 0.84rem; font-weight: 600; color: #0f172a; margin-bottom: 8px;">
            Request Configuration
        </div>
        """, unsafe_allow_html=True)

        service_hex = st.selectbox(
            "Service",
            [
                "0x10 (DiagnosticSessionControl)",
                "0x11 (ECUReset)",
                "0x22 (ReadDataByIdentifier)",
                "0x27 (SecurityAccess)",
                "0x2E (WriteDataByIdentifier)",
                "0x31 (RoutineControl)"
            ]
        )
        sid = service_hex.split()[0]

        subfunc = None
        did = None
        params = None

        if sid == "0x10":
            sf_choice = st.selectbox("Subfunction (Session Type)", ["0x01 (DefaultSession)", "0x02 (ProgrammingSession)", "0x03 (ExtendedDiagnosticSession)"])
            pure_sf = int(sf_choice.split()[0], 16)
            suppress_bit = st.checkbox("Suppress positive response indication bit (0x80)", value=False)
            subfunc = f"0x{(pure_sf | 0x80):02X}" if suppress_bit else f"0x{pure_sf:02X}"

        elif sid == "0x11":
            subfunc = st.selectbox("Reset Type", ["0x01 (HardReset)", "0x03 (SoftReset)"]).split()[0]

        elif sid == "0x22":
            did = st.selectbox("Data Identifier (DID)", ["0xF190 (VIN)", "0x0100 (EngineSpeed)", "0x0200 (VehicleSpeed)", "0x0300 (BatteryVoltage)"]).split()[0]

        elif sid == "0x27":
            subfunc = st.selectbox("Security Step", ["0x01 (RequestSeed_L1)", "0x02 (SendKey_L1)"]).split()[0]
            if subfunc == "0x02":
                st.caption("Key algorithm: Seed XOR 0x55AA55AA")
                params = st.text_input("Key Payload (Hex)", value="6F D1 49 35")

        elif sid == "0x2E":
            did = "0x0105"
            st.caption("DID 0x0105 VariantCoding parameters:")
            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                r_byte = st.selectbox("Region", ["0x01 (NA)", "0x02 (EU)", "0x03 (ASIA)"]).split()[0]
            with c_p2:
                l_byte = st.selectbox("Lighting", ["0x00 (Halogen)", "0x01 (LED)"]).split()[0]
            with c_p3:
                t_byte = st.selectbox("Trailer", ["0x00 (Disabled)", "0x01 (Enabled)"]).split()[0]
            params = f"{r_byte[2:]} {l_byte[2:]} {t_byte[2:]} AA"

        elif sid == "0x31":
            subfunc = st.selectbox("Routine Control Type", ["0x01 (StartRoutine)", "0x03 (RequestRoutineResults)"]).split()[0]
            did = "0x0201"

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 0.80rem; font-weight: 600; color: #475569; margin-bottom: 4px;">
            Target ECU Preconditions
        </div>
        """, unsafe_allow_html=True)

        c_s1, c_s2 = st.columns(2)
        with c_s1:
            session = st.selectbox("Required Session", ["DefaultSession", "ExtendedDiagnosticSession", "ProgrammingSession"])
        with c_s2:
            security = st.selectbox("Required Security", ["Locked", "Level1Unlocked"])

        sim_speed = st.number_input("Simulated Vehicle Speed (km/h)", min_value=0.0, max_value=250.0, value=0.0, step=1.0)

    # State assembly
    payload = {
        "service_id_hex": sid,
        "subfunction_hex": subfunc,
        "did_hex": did,
        "parameters_hex": params,
        "session": session,
        "security_state": security
    }

    try:
        build_res = requests.post(f"{API_URL}/api/requests/build", json=payload, timeout=2.0).json()
        req_hex = build_res.get("request_hex", "")
        exp_rsp = build_res.get("expected_response", "")

        with col_prev:
            st.markdown("""
            <div style="font-size: 0.84rem; font-weight: 600; color: #0f172a; margin-bottom: 8px;">
                Request Preview
            </div>
            """, unsafe_allow_html=True)

            # Monospace frame display
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; margin-bottom: 14px;">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">UDS CAN Frame (Tx)</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.35rem; font-weight: 700; color: #1e3a8a; margin: 4px 0 8px 0;">
                    {req_hex}
                </div>
                <div style="font-size: 0.76rem; color: #64748b;">
                    Payload: {len(req_hex.replace(' ',''))//2} bytes &bull; Expected Response: <code style="color:#166534;">{exp_rsp}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Validation checklist
            v_res = requests.post(
                f"{API_URL}/api/requests/validate",
                json={
                    "request_hex": req_hex,
                    "session": session,
                    "security_state": security,
                    "simulated_vehicle_speed": sim_speed
                },
                timeout=2.0
            ).json()

            status = v_res.get("status", "VALID")
            issues = v_res.get("issues", [])

            is_valid = (status == "VALID")
            badge_html = render_status_pill(status)

            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 14px; margin-bottom: 14px; font-size: 0.80rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #0f172a;">Static Verification</span>
                    {badge_html}
                </div>
                <div style="color: {'#166534' if is_valid else '#92400e'}; display: flex; flex-direction: column; gap: 4px; font-size: 0.78rem;">
                    <div>&bull; Service {sid} recognized in specification</div>
                    <div>&bull; Payload length ({len(req_hex.replace(' ',''))//2} bytes) matches definition</div>
                    <div>&bull; Precondition check: {session}, {security}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("Generate Test Case", type="primary", use_container_width=True):
                    test_obj = f"Verify {service_hex.split()[1]} with frame {req_hex}"
                    gen_res = requests.post(
                        f"{API_URL}/api/requests/generate-test",
                        json={
                            "request_hex": req_hex,
                            "service_id_hex": sid,
                            "subfunction_hex": subfunc,
                            "session": session,
                            "security_state": security,
                            "expected_response_hex": exp_rsp,
                            "objective": test_obj,
                            "requirement_id": "REQ-UDS-001",
                            "test_type": "POSITIVE" if "NRC" not in exp_rsp else "NEGATIVE"
                        },
                        timeout=2.0
                    ).json()
                    st.success(f"Generated test case {gen_res.get('test_id')} (Pending Review)")

            with col_b2:
                with st.popover("Protocol Flow", use_container_width=True):
                    st.markdown("**Sequence Flow:**")
                    seq_code = f"""sequenceDiagram
    autonumber
    actor Tester as Diagnostic Tester
    participant ECU as BCM-Demo-ECU
    Note over Tester,ECU: Precondition: {session}, {security}
    Tester->>ECU: UDS Request: {req_hex}
    alt Nominal Execution
        ECU-->>Tester: Positive Response: {exp_rsp}
    else Error / Prerequisite Violation
        ECU-->>Tester: Negative Response: 7F {sid.replace('0x','')} [NRC]
    end
"""
                    st.code(seq_code, language="mermaid")

    except Exception as e:
        st.error(f"Configuration error: {e}")
