from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Body
from pydantic import BaseModel, Field
from app.rag.chains import diagnostic_rag_pipeline, RAGAnswerResponse
from app.database.repository import DiagRepository

router = APIRouter(prefix="/api/rag", tags=["RAG Assistant"])

class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language diagnostic question")
    doc_type: Optional[str] = Field(None, description="Metadata filter: ALL, STANDARD, OEM, ECU, PROJECT")
    top_k: int = Field(4, description="Maximum number of evidence chunks to retrieve")

@router.post("/query", response_model=RAGAnswerResponse)
def query_rag_assistant(request: RAGQueryRequest):
    repo = DiagRepository()
    response = diagnostic_rag_pipeline.query(
        question=request.query,
        doc_type=request.doc_type,
        top_k=request.top_k
    )

    repo.log_audit(
        action="RAG_QUERY",
        entity_type="KnowledgeAssistant",
        entity_id=request.doc_type or "ALL",
        details=f"Query: '{request.query[:50]}' | Citations: {response.source_document} ({response.section})"
    )

    return response
