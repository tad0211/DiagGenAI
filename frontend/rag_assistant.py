import streamlit as st
import requests

from frontend.ui_components import (
    render_section_header, render_status_pill, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_rag_assistant():
    render_section_header(
        "Diagnostic Knowledge Assistant",
        "Semantic query engine grounded in indexed diagnostic specifications and ISO 14229 standards"
    )

    col_q1, col_q2 = st.columns([3, 1])
    with col_q1:
        preset_q = st.selectbox(
            "Reference Query Templates",
            [
                "-- Select a standard query or enter custom question below --",
                "What subfunctions are supported for service 0x10?",
                "What is the key algorithm for Security Access Level 1?",
                "What DIDs can be read using service 0x22?",
                "What are the prerequisites for WriteDataByIdentifier (0x2E)?",
                "What are the preconditions for RoutineControl (0x31) 0x0201?",
                "How do I calibrate the panoramic sunroof motor?"
            ]
        )
    with col_q2:
        doc_scope = st.selectbox("Specification Scope", ["All Scopes", "ECU", "STANDARD", "OEM", "PROJECT"])

    default_text = preset_q if not preset_q.startswith("--") else ""
    user_query = st.text_input(
        "Ask a diagnostic requirement or protocol question:",
        value=default_text,
        placeholder="e.g. What subfunctions are supported for service 0x10?"
    )

    if st.button("Query Knowledge Base", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a question or select a reference template.")
            return

        payload = {
            "query": user_query.strip(),
            "doc_type": None if doc_scope == "All Scopes" else doc_scope,
            "top_k": 4
        }

        with st.spinner("Retrieving specifications and synthesizing verified answer..."):
            try:
                res = requests.post(f"{API_URL}/api/rag/query", json=payload, timeout=10.0)
                if res.status_code == 200:
                    ans_data = res.json()
                    is_fallback = "Insufficient evidence" in ans_data["answer"]

                    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

                    if is_fallback:
                        st.markdown(f"""
                        <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 4px; padding: 14px 16px; margin-bottom: 16px;">
                            <div style="font-size: 0.72rem; color: #92400e; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                                Safety Notice &bull; Grounded Fallback
                            </div>
                            <div style="font-size: 0.95rem; font-weight: 600; color: #92400e; margin-top: 4px;">
                                {ans_data['answer']}
                            </div>
                            <div style="font-size: 0.80rem; color: #475569; margin-top: 6px;">
                                {ans_data.get('evidence', '')}
                            </div>
                            <div style="font-size: 0.75rem; color: #64748b; margin-top: 6px;">
                                Scope Note: {ans_data.get('limitations', '')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        conf_pct = ans_data.get("confidence", 0.95) * 100
                        st.markdown(f"""
                        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px; margin-bottom: 16px;">
                            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                                <span style="font-size: 0.72rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">
                                    Answer
                                </span>
                                <span style="font-size: 0.72rem; color: #64748b;">Confidence: <b>{conf_pct:.0f}%</b></span>
                            </div>
                            <div style="font-size: 0.92rem; color: #0f172a; line-height: 1.6;">
                                {ans_data['answer']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Source Evidence Box
                        st.markdown("""
                        <div style="font-size: 0.82rem; font-weight: 600; color: #0f172a; margin-bottom: 6px;">
                            Source Evidence
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown(f"""
                        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 12px 14px; margin-bottom: 14px;">
                            <div style="display: flex; gap: 20px; font-size: 0.76rem; color: #64748b; margin-bottom: 6px;">
                                <div><b>Document:</b> {ans_data.get('source_document')}</div>
                                <div><b>Section:</b> {ans_data.get('section')}</div>
                            </div>
                            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.80rem; color: #1e293b; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 3px; padding: 8px 10px; line-height: 1.5;">
                                {ans_data.get('evidence')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Traceability Flow
                        st.markdown("""
                        <div style="font-size: 0.82rem; font-weight: 600; color: #0f172a; margin-bottom: 6px;">
                            Verification Lineage
                        </div>
                        <div style="font-size: 0.76rem; color: #64748b; margin-bottom: 8px;">
                            Query Input &rarr; Vector Retrieval (ChromaDB) &rarr; Grounded Synthesized Verdict
                        </div>
                        """, unsafe_allow_html=True)

                        chunks = ans_data.get("retrieved_chunks", [])
                        if chunks:
                            with st.expander(f"Inspect Retrieved Evidence Fragments ({len(chunks)})", expanded=False):
                                for idx, c in enumerate(chunks):
                                    st.markdown(f"**Fragment {idx+1} &bull; {c.get('source_doc')} ({c.get('section')}):**")
                                    st.code(c.get("content", ""), language="text")

                else:
                    st.error("Failed to query knowledge assistant service.")
            except Exception as e:
                st.error(f"Error querying assistant: {e}")
