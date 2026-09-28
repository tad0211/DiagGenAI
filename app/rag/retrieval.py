"""
DiagGenAI - Vector Store & ChromaDB Retrieval Module.
Manages persistent ChromaDB vector store, handles chunk indexing with BGE/E5 embeddings,
and executes metadata-filtered evidence retrieval (STANDARD, OEM, ECU, PROJECT).
"""

import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.rag.embeddings import embedding_engine
from app.rag.ingestion import DocumentChunk

class ChromaDiagnosticStore:
    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        os.makedirs(self.persist_dir, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "UDS Diagnostic Specifications and Requirements"}
        )

    def index_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Embed and upsert document chunks into ChromaDB."""
        if not chunks:
            return 0

        ids = [c.chunk_id for c in chunks]
        texts = [c.content for c in chunks]
        metadatas = [c.metadata for c in chunks]

        # Generate embeddings via BGE/E5 engine
        embeddings = embedding_engine.embed_documents(texts)

        self._collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        return len(chunks)

    def retrieve_evidence(
        self,
        query: str,
        doc_type: Optional[str] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant evidence chunks from ChromaDB.
        Supports metadata filtering by doc_type: STANDARD, OEM, ECU, PROJECT.
        """
        if self._collection.count() == 0:
            return []

        query_emb = embedding_engine.embed_query(query)

        where_filter = None
        if doc_type and doc_type.upper() != "ALL":
            where_filter = {"doc_type": doc_type.upper()}

        results = self._collection.query(
            query_embeddings=[query_emb],
            n_results=min(top_k, self._collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        evidence_list: List[Dict[str, Any]] = []
        if results and results["documents"] and len(results["documents"][0]) > 0:
            for i in range(len(results["documents"][0])):
                doc_text = results["documents"][0][i]
                meta = results["metadatas"][0][i]
                dist = results["distances"][0][i] if "distances" in results else 0.0

                # Compute confidence score from cosine distance
                # Cosine distance range is 0 to 2; similarity = 1 - (dist / 2)
                confidence = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

                evidence_list.append({
                    "content": doc_text,
                    "source_doc": meta.get("source_doc", "Unknown Spec"),
                    "version": meta.get("version", "1.0"),
                    "doc_type": meta.get("doc_type", "ECU"),
                    "section": meta.get("section", "General"),
                    "page": meta.get("page", 1),
                    "confidence": round(confidence, 3),
                    "distance": round(dist, 4)
                })

        return evidence_list

    def get_indexed_count(self) -> int:
        return self._collection.count()

    def clear_index(self):
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "UDS Diagnostic Specifications and Requirements"}
        )

# Global vector store instance
diagnostic_vector_store = ChromaDiagnosticStore()
