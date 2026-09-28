"""
DiagGenAI - Requirement-to-Test Traceability Graph Frontend Module.
End-to-end V-Model traceability: Requirement -> Service -> Test Case -> Execution -> Result.
"""

import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, Any, List

from frontend.ui_components import (
    render_section_header, render_status_pill,
    render_hex_token, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_traceability():
    render_section_header(
        "Requirements Traceability & Lineage",
        "End-to-end verification traceability: Specification Requirement &rarr; UDS Service &rarr; Test Case &rarr; Execution &rarr; Verdict"
    )

    # Fetch Graph Data
    graph_data = {}
    try:
        res = requests.get(f"{API_URL}/api/traceability/graph", timeout=5.0)
        if res.status_code == 200:
            graph_data = res.json()
    except Exception:
        from app.graph.traceability_engine import TraceabilityGraphEngine
        graph_data = TraceabilityGraphEngine().get_topology()

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    stats = graph_data.get("statistics", {})
    node_types = stats.get("node_types", {})

    # V-Model Flow Diagram
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px 18px; margin-bottom: 20px;">
        <div style="font-size: 0.70rem; color: #64748b; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">
            ASPICE V-Model Traceability Architecture
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.82rem; font-weight: 600; color: #0f172a;">
            <div style="text-align: center;">
                <div style="color: #1e3a8a;">Document</div>
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 400;">ISO / BCM Spec</div>
            </div>
            <div style="color: #cbd5e1;">&rarr;</div>
            <div style="text-align: center;">
                <div style="color: #1e3a8a;">Requirement</div>
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 400;">{node_types.get('Requirement', 0)} items</div>
            </div>
            <div style="color: #cbd5e1;">&rarr;</div>
            <div style="text-align: center;">
                <div style="color: #1e3a8a;">UDS Service</div>
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 400;">{node_types.get('Service', 0)} handlers</div>
            </div>
            <div style="color: #cbd5e1;">&rarr;</div>
            <div style="text-align: center;">
                <div style="color: #1e3a8a;">Test Case</div>
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 400;">{node_types.get('TestCase', 0)} tests</div>
            </div>
            <div style="color: #cbd5e1;">&rarr;</div>
            <div style="text-align: center;">
                <div style="color: #166534;">Execution Result</div>
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 400;">PASS / FAIL</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_mat, tab_lin, tab_gap = st.tabs([
        "Traceability Matrix",
        "Lineage Inspector",
        "Orphan & Coverage Gaps"
    ])

    with tab_mat:
        try:
            matrix_data = requests.get(f"{API_URL}/api/traceability/matrix", timeout=4.0).json()
        except Exception:
            from app.graph.traceability_engine import TraceabilityGraphEngine
            matrix_data = TraceabilityGraphEngine().get_matrix()

        if matrix_data:
            df_m = pd.DataFrame(matrix_data)
            st.dataframe(df_m, use_container_width=True, hide_index=True)
            st.caption(f"{len(matrix_data)} verified traceability linkages across specifications.")
        else:
            st.info("No matrix entries found.")

    with tab_lin:
        node_ids = sorted([n.get("id") for n in nodes])
        target_n = st.selectbox("Inspect Entity Lineage", node_ids)

        if target_n:
            try:
                lin_res = requests.get(f"{API_URL}/api/traceability/lineage/{target_n}", timeout=3.0).json()
            except Exception:
                from app.graph.traceability_engine import TraceabilityGraphEngine
                lin_res = TraceabilityGraphEngine().get_lineage(target_n)

            col_u, col_d = st.columns(2)
            with col_u:
                st.markdown(f"**Upstream Predecessors ({lin_res.get('upstream_count', 0)}):**")
                parents = lin_res.get("direct_parents", [])
                if parents:
                    for p in parents: st.markdown(f"- `{p}`")
                else:
                    st.caption("None (Root entity)")
            with col_d:
                st.markdown(f"**Downstream Successors ({lin_res.get('downstream_count', 0)}):**")
                children = lin_res.get("direct_children", [])
                if children:
                    for c in children: st.markdown(f"- `{c}`")
                else:
                    st.caption("None (Leaf entity)")

    with tab_gap:
        try:
            orphans_data = requests.get(f"{API_URL}/api/traceability/orphans", timeout=3.0).json()
        except Exception:
            from app.graph.traceability_engine import TraceabilityGraphEngine
            orphans_data = TraceabilityGraphEngine().get_orphans()

        u_reqs = orphans_data.get("uncovered_requirements", [])
        o_tests = orphans_data.get("orphan_tests", [])

        if not u_reqs and not o_tests:
            st.success("Complete traceability integrity: 100% of requirements map to test cases.")
        else:
            if u_reqs:
                st.markdown("**Uncovered Requirements (No linked test cases):**")
                st.dataframe(pd.DataFrame(u_reqs), use_container_width=True, hide_index=True)
            if o_tests:
                st.markdown("**Orphan Tests (No upstream specification link):**")
                st.dataframe(pd.DataFrame(o_tests), use_container_width=True, hide_index=True)
