"""
DiagGenAI - Vector Store Auto-Seeder.
Indexes baseline synthetic ECU specifications (v1.0 and v1.1) into ChromaDB
using context-aware markdown chunking and BGE/E5 embeddings.
"""

import os
from pathlib import Path
from app.rag.ingestion import DiagnosticDocumentIngestor
from app.rag.retrieval import diagnostic_vector_store

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def seed_vector_store():
    ingestor = DiagnosticDocumentIngestor(chunk_size=500, chunk_overlap=60)
    spec_v1_path = BASE_DIR / "data" / "sample_specs" / "synthetic_bcm_diag_spec_v1.md"
    spec_v1_1_path = BASE_DIR / "data" / "sample_specs" / "synthetic_bcm_diag_spec_v1_1.md"

    total_indexed = 0

    if spec_v1_path.exists():
        chunks_v1 = ingestor.ingest_file(
            file_path=str(spec_v1_path),
            doc_name="Synthetic BCM Diagnostic Specification v1.0",
            version="1.0",
            doc_type="ECU"
        )
        count_v1 = diagnostic_vector_store.index_chunks(chunks_v1)
        total_indexed += count_v1
        print(f"[INFO] Indexed {count_v1} chunks from {spec_v1_path.name}")

    if spec_v1_1_path.exists():
        chunks_v1_1 = ingestor.ingest_file(
            file_path=str(spec_v1_1_path),
            doc_name="Synthetic BCM Diagnostic Specification v1.1",
            version="1.1",
            doc_type="ECU"
        )
        count_v1_1 = diagnostic_vector_store.index_chunks(chunks_v1_1)
        total_indexed += count_v1_1
        print(f"[INFO] Indexed {count_v1_1} chunks from {spec_v1_1_path.name}")

    print(f"[SUCCESS] ChromaDB vector store ready. Total chunks indexed: {total_indexed}")
    return total_indexed

if __name__ == "__main__":
    seed_vector_store()
