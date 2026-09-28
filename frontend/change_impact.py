"""
DiagGenAI - Specification Change Impact & Test Suite Intelligence Frontend Modules.
Detects specification deltas between document releases, computes impacted test cases,
flags affected tests as REQUIRES_RETEST, and provides test suite optimization insights.
"""

import streamlit as st
import requests
import json
import pandas as pd

from frontend.ui_components import (
    render_section_header, render_status_pill,
    render_hex_token, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_change_impact(default_tab_idx: int = 0):
    render_section_header(
        "Specification Version Change Impact & Intelligence",
        "Automated delta analysis between specification releases (v1.0 vs v1.1) to flag impacted test cases and optimize regression scope"
    )

    tab_impact, tab_intel = st.tabs([
        "Change Impact Analysis",
        "Test Suite Optimization"
    ])

    # ==================== TAB 1: CHANGE IMPACT ====================
    with tab_impact:
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Baseline Specification", ["Synthetic BCM Spec v1.0.0 (synthetic_bcm_diag_spec_v1.md)"], key="ci_v1")
        with col2:
            st.selectbox("Revised Specification", ["Synthetic BCM Spec v1.1.0 (synthetic_bcm_diag_spec_v1_1.md)"], key="ci_v2")

        if st.button("Analyze Specification Delta", type="primary"):
            with st.spinner("Analyzing document deltas and graph traceability impacts..."):
                try:
                    res = requests.post(
                        f"{API_URL}/api/change-impact/analyze",
                        json={"base_version": "1.0", "target_version": "1.1"},
                        timeout=8.0
                    )
                    if res.status_code == 200:
                        st.session_state["last_impact_result"] = res.json()
                except Exception:
                    from app.analysis.change_impact import ChangeImpactEngine
                    st.session_state["last_impact_result"] = ChangeImpactEngine().analyze_change_impact()

        if "last_impact_result" in st.session_state and st.session_state["last_impact_result"]:
            data = st.session_state["last_impact_result"]
            impact_level = data.get("overall_impact_level", "MAJOR")
            impacted_tests = data.get("impacted_tests", [])
            reg_suite = data.get("recommended_regression_suite", [])
            new_tests = data.get("new_tests_needed", [])

            # Impact Summary Strip
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 16px; margin: 16px 0; display: flex; justify-content: space-between; align-items: baseline;">
                <div>
                    <span style="font-size: 0.68rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Overall Impact Level</span>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-top: 2px;">
                        {impact_level}
                    </div>
                </div>
                <div style="text-align: right; font-size: 0.80rem;">
                    <span style="color: #64748b;">Impacted Test Cases:</span> <b>{len(impacted_tests)}</b> &bull; 
                    <span style="color: #64748b;">Regression Scope:</span> <b>{len(reg_suite)} tests</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown("""
                <div style="font-size: 0.82rem; font-weight: 600; color: #166534; margin-bottom: 6px;">
                    Added Specification Features
                </div>
                """, unsafe_allow_html=True)
                for item in data.get("added_features", []):
                    st.markdown(f"- **{item['entity']}**: {item['subfunction'] if 'subfunction' in item else item.get('did')} — *{item['description']}*")

                st.markdown("""
                <div style="font-size: 0.82rem; font-weight: 600; color: #991b1b; margin-top: 10px; margin-bottom: 6px;">
                    Deprecated / Removed Elements
                </div>
                """, unsafe_allow_html=True)
                for item in data.get("removed_features", []):
                    st.markdown(f"- **{item['entity']}**: {item.get('subfunction')} — *{item['description']}*")

            with col_d2:
                st.markdown("""
                <div style="font-size: 0.82rem; font-weight: 600; color: #92400e; margin-bottom: 6px;">
                    Modified Parameters & Prerequisites
                </div>
                """, unsafe_allow_html=True)
                for item in data.get("modified_parameters", []) + data.get("modified_prerequisites", []):
                    st.markdown(f"- **{item['entity']}**: *{item['description']}*")

            # Impacted Tests Table
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.markdown(f"**Impacted Test Cases Requiring Retest ({len(impacted_tests)} items):**")

            if impacted_tests:
                df_imp = pd.DataFrame(impacted_tests)
                st.dataframe(df_imp, use_container_width=True, hide_index=True)

                if st.button("Flag Impacted Tests as REQUIRES_RETEST", type="primary"):
                    target_ids = [t["test_id"] for t in impacted_tests]
                    try:
                        res = requests.post(f"{API_URL}/api/change-impact/apply-flags", json={"test_ids": target_ids}, timeout=3.0)
                        st.success(f"Flagged {len(target_ids)} test cases as REQUIRES_RETEST.")
                        st.rerun()
                    except Exception:
                        from app.analysis.change_impact import ChangeImpactEngine
                        ChangeImpactEngine().apply_impact_flags(target_ids)
                        st.success(f"Flagged {len(target_ids)} test cases as REQUIRES_RETEST.")
                        st.rerun()

            if new_tests:
                with st.expander(f"New Recommended Test Scenarios for Release v1.1 ({len(new_tests)} items)"):
                    for n in new_tests:
                        st.markdown(f"- **{n['scenario']}** (Service `{n['service']}` | Frame: `{n['suggested_frame']}`) — *{n['rationale']}*")

    # ==================== TAB 2: TEST SUITE INTELLIGENCE ====================
    with tab_intel:
        try:
            intel_data = requests.get(f"{API_URL}/api/change-impact/intelligence", timeout=4.0).json()
        except Exception:
            from app.analysis.change_impact import ChangeImpactEngine
            intel_data = ChangeImpactEngine().get_test_suite_intelligence()

        score = intel_data.get("suite_health_score", 95.0)

        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding: 12px 16px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 16px;">
            <div><span style="font-size:0.70rem; color:#64748b;">TOTAL TESTS:</span> <b>{intel_data.get('total_test_cases', 0)}</b></div>
            <div><span style="font-size:0.70rem; color:#64748b;">UNIQUE VECTORS:</span> <b>{intel_data.get('unique_signatures', 0)}</b></div>
            <div><span style="font-size:0.70rem; color:#64748b;">DUPLICATES:</span> <b>{intel_data.get('duplicates_detected', 0)}</b></div>
            <div><span style="font-size:0.70rem; color:#64748b;">SUITE HEALTH:</span> <b style="color:#166534;">{score:.1f}%</b></div>
        </div>
        """, unsafe_allow_html=True)

        col_in1, col_in2 = st.columns(2)
        with col_in1:
            st.markdown("**Test Dimension Distribution:**")
            dist = intel_data.get("type_distribution", {})
            for t_name, t_cnt in dist.items():
                st.markdown(f"- **{t_name}:** {t_cnt} test cases")

        with col_in2:
            st.markdown("**Optimization Recommendations:**")
            recs = intel_data.get("recommendations", [])
            for r in recs:
                st.markdown(f"**[{r['type']}]** *{r['title']}*")
                st.caption(r['description'])
