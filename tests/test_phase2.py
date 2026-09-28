import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.rag.ingestion import DiagnosticDocumentIngestor
from app.rag.embeddings import embedding_engine
from app.rag.retrieval import diagnostic_vector_store
from app.rag.chains import diagnostic_rag_pipeline

client = TestClient(app)

def test_document_ingestion_chunking():
    ingestor = DiagnosticDocumentIngestor(chunk_size=300, chunk_overlap=30)
    sample_text = """# Diagnostic Specification Header
## Section 1: Overview
This is a test diagnostic document for BCM ECU testing.
## Section 2: Services
Service 0x22 ReadDataByIdentifier is supported for DID 0xF190.
"""
    chunks = ingestor.ingest_raw_text(sample_text, doc_name="TestSpec", version="1.0", doc_type="ECU")
    assert len(chunks) >= 2
    assert any("Section 2: Services" in c.metadata["section"] for c in chunks)
    assert all(c.metadata["doc_type"] == "ECU" for c in chunks)

def test_embeddings_generation():
    texts = ["DiagnosticSessionControl 0x10", "SecurityAccess seed key 0x27"]
    vectors = embedding_engine.embed_documents(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    # Query embedding
    q_vec = embedding_engine.embed_query("Read VIN DID 0xF190")
    assert len(q_vec) == 384

def test_chroma_vector_store_retrieval():
    # Verify vector store has indexed chunks from sample specs
    count = diagnostic_vector_store.get_indexed_count()
    assert count > 0

    # Retrieve with metadata filter
    results = diagnostic_vector_store.retrieve_evidence("0x27 SecurityAccess", doc_type="ECU", top_k=2)
    assert len(results) > 0
    assert results[0]["doc_type"] == "ECU"
    assert "source_doc" in results[0]
    assert "section" in results[0]

def test_rag_pipeline_valid_query():
    res = diagnostic_rag_pipeline.query("What subfunctions are supported for service 0x10?")
    assert "Service 0x10" in res.answer
    assert "0x01" in res.answer or "DefaultSession" in res.answer
    assert res.source_document != "N/A"
    assert "Section 2" in res.section
    assert len(res.evidence) > 0
    assert res.confidence > 0.5

def test_rag_pipeline_insufficient_evidence():
    # Ask a question unrelated to the indexed BCM specification
    res = diagnostic_rag_pipeline.query("How do I calibrate the radar cruise control sensor?")
    assert res.answer == "Insufficient evidence in the indexed project knowledge."
    assert res.confidence == 0.0

def test_rag_query_endpoint():
    # Test valid question via API
    res = client.post("/api/rag/query", json={
        "query": "What DIDs are supported for service 0x22?",
        "doc_type": "ALL",
        "top_k": 3
    })
    assert res.status_code == 200
    data = res.json()
    assert "0xF190" in data["answer"] or "DID" in data["answer"]
    assert "Synthetic BCM" in data["source_document"]
    assert len(data["retrieved_chunks"]) > 0

def test_rag_query_endpoint_missing_evidence():
    # Test out-of-domain question via API
    res = client.post("/api/rag/query", json={
        "query": "What is the procedure for replacing the panoramic sunroof glass?",
        "doc_type": "ALL"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["answer"] == "Insufficient evidence in the indexed project knowledge."
