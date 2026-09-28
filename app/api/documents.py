import os
import json
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from app.database.repository import DiagRepository
from app.rag.ingestion import DiagnosticDocumentIngestor
from app.rag.retrieval import diagnostic_vector_store
from app.rag.seed_vector_store import seed_vector_store

router = APIRouter(prefix="/api/documents", tags=["Documents"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sample_specs"

class DocumentResponse(BaseModel):
    id: int
    name: str
    version: str
    doc_type: str
    upload_date: str
    status: str
    file_path: Optional[str] = None
    section: Optional[str] = None
    metadata: dict = {}

@router.get("", response_model=List[DocumentResponse])
def get_documents(doc_type: Optional[str] = Query(None, description="STANDARD, OEM, ECU, PROJECT")):
    repo = DiagRepository()
    docs = repo.get_documents(doc_type=doc_type)
    return [
        DocumentResponse(
            id=d.id,
            name=d.name,
            version=d.version,
            doc_type=d.doc_type,
            upload_date=d.upload_date.isoformat() if d.upload_date else "",
            status=d.status,
            file_path=d.file_path,
            section=d.section,
            metadata=json.loads(d.metadata_json or "{}")
        )
        for d in docs
    ]

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    version: str = Form("1.0"),
    doc_type: str = Form("ECU"),  # STANDARD, OEM, ECU, PROJECT
    section: str = Form("General")
):
    repo = DiagRepository()
    ingestor = DiagnosticDocumentIngestor()

    doc_name = name or file.filename or "Uploaded_Document"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    target_path = UPLOAD_DIR / file.filename

    # Save file contents to disk
    contents = await file.read()
    with open(target_path, "wb") as f:
        f.write(contents)

    # Ingest and chunk
    chunks = ingestor.ingest_file(
        file_path=str(target_path),
        doc_name=doc_name,
        version=version,
        doc_type=doc_type.upper()
    )

    # Embed and upsert into ChromaDB
    chunks_indexed = diagnostic_vector_store.index_chunks(chunks)

    # Record in SQLite database
    db_doc = repo.add_document(
        name=doc_name,
        version=version,
        doc_type=doc_type.upper(),
        file_path=str(target_path),
        metadata_dict={
            "section": section,
            "filename": file.filename,
            "chunks_count": chunks_indexed
        }
    )

    return {
        "status": "success",
        "message": f"Document '{doc_name}' indexed successfully.",
        "doc_id": db_doc.id,
        "chunks_indexed": chunks_indexed,
        "total_vector_count": diagnostic_vector_store.get_indexed_count()
    }

@router.post("/reindex")
def reindex_all():
    count = seed_vector_store()
    return {"status": "success", "message": f"Re-indexed {count} baseline specification chunks into ChromaDB."}
