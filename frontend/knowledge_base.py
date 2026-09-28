import streamlit as st
import requests
import json
import pandas as pd

from frontend.ui_components import (
    render_section_header, render_status_pill, get_icon
)

API_URL = "http://127.0.0.1:8000"

def render_knowledge_base():
    render_section_header(
        "Diagnostic Specifications",
        "Authorized ISO 14229 standards, OEM baseline requirements, and project engineering documents"
    )

    tab1, tab2 = st.tabs([
        "Specification Registry",
        "Upload Specification"
    ])

    with tab1:
        f1, f2 = st.columns([1, 2])
        with f1:
            doc_filter = st.selectbox("Scope Filter", ["All Categories", "STANDARD", "OEM", "ECU", "PROJECT"])
        with f2:
            search_doc = st.text_input("Search specifications...", placeholder="Search document title or version...")

        params = {}
        if doc_filter != "All Categories":
            params["doc_type"] = doc_filter

        try:
            res = requests.get(f"{API_URL}/api/documents", params=params, timeout=2.0)
            if res.status_code == 200:
                docs = res.json()
                if search_doc.strip():
                    q = search_doc.strip().lower()
                    docs = [d for d in docs if q in d.get("name", "").lower() or q in d.get("version", "").lower()]

                if docs:
                    df = pd.DataFrame(docs)[["name", "version", "doc_type", "status", "file_path", "upload_date"]]
                    df.columns = ["Specification Title", "Version", "Scope", "Index Status", "File Path", "Uploaded"]
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.caption(f"{len(docs)} specification document(s) in local repository.")
                else:
                    st.info("No specifications match the active search or filter.")
            else:
                st.error("Unable to load specifications.")
        except Exception as e:
            st.error(f"API Error: {e}")

    with tab2:
        st.markdown("""
        <div style="font-size: 0.88rem; font-weight: 600; color: #0f172a; margin-bottom: 4px;">
            Ingest Specification Document
        </div>
        <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 14px;">
            Upload Markdown, TXT, or PDF diagnostic specifications to parse requirements and generate semantic embeddings.
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Specification Title", value="OEM BCM Diagnostic Protocol Spec")
            version = st.text_input("Release Version", value="1.0.0")
            doc_type = st.selectbox("Classification", ["ECU", "OEM", "STANDARD", "PROJECT"])
        with c2:
            section = st.text_input("Applicable Sections", value="Section 1-12")
            uploaded_file = st.file_uploader("Specification File", type=["md", "txt", "pdf"])

        if st.button("Index Specification into Knowledge Base", type="primary"):
            if uploaded_file is not None:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                data = {
                    "name": name or uploaded_file.name,
                    "version": version,
                    "doc_type": doc_type,
                    "section": section
                }
                with st.spinner("Processing document and generating vector embeddings..."):
                    try:
                        res = requests.post(f"{API_URL}/api/documents/upload", files=files, data=data, timeout=30.0)
                        if res.status_code == 200:
                            ret = res.json()
                            st.success(f"Indexed '{name}' successfully ({ret['chunks_indexed']} chunks).")
                        else:
                            st.error(f"Upload failed: {res.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Select a file (.md, .txt, or .pdf) to upload.")
