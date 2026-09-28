"""
DiagGenAI - Document Ingestion & Context-Aware Chunking Pipeline.
Parses Markdown, Plain Text, and PDF files, extracts sections,
and tags chunks with strict metadata (STANDARD, OEM, ECU, PROJECT).
"""

import os
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from pypdf import PdfReader

class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: Dict[str, Any]

class DiagnosticDocumentIngestor:
    """Ingests automotive diagnostic specifications with context-aware section chunking."""

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 80):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_markdown(self, text: str, doc_name: str, version: str, doc_type: str) -> List[DocumentChunk]:
        """Context-aware chunker splitting on Markdown headers (## Section ...) with section metadata."""
        chunks: List[DocumentChunk] = []
        # Split by section headers (e.g. ## Section 2: ... or # Section ...)
        sections = re.split(r'\n(?=#{1,3}\s+)', text)

        chunk_counter = 0
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue

            # Extract section title from the first header line
            first_line = sec.split('\n')[0].strip('# \t\r')
            section_title = first_line if first_line else "General"

            # If section fits within chunk_size, keep as a single atomic context chunk
            if len(sec) <= self.chunk_size:
                chunk_counter += 1
                chunks.append(DocumentChunk(
                    chunk_id=f"{doc_name}_v{version}_c{chunk_counter}",
                    content=sec,
                    metadata={
                        "source_doc": doc_name,
                        "version": version,
                        "doc_type": doc_type.upper(),
                        "section": section_title,
                        "page": 1,
                        "length": len(sec)
                    }
                ))
            else:
                # Sub-chunk longer sections with overlap while retaining section title header
                start = 0
                while start < len(sec):
                    end = min(start + self.chunk_size, len(sec))
                    sub_text = sec[start:end]
                    # Prepend section context if not the first chunk
                    if start > 0:
                        sub_text = f"[{section_title} - Cont.]\n" + sub_text

                    chunk_counter += 1
                    chunks.append(DocumentChunk(
                        chunk_id=f"{doc_name}_v{version}_c{chunk_counter}",
                        content=sub_text.strip(),
                        metadata={
                            "source_doc": doc_name,
                            "version": version,
                            "doc_type": doc_type.upper(),
                            "section": section_title,
                            "page": 1,
                            "length": len(sub_text)
                        }
                    ))
                    start += (self.chunk_size - self.chunk_overlap)

        return chunks

    def parse_pdf(self, file_path: str, doc_name: str, version: str, doc_type: str) -> List[DocumentChunk]:
        """Extract text from PDF pages and chunk with page metadata."""
        chunks: List[DocumentChunk] = []
        reader = PdfReader(file_path)
        chunk_counter = 0

        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if not text.strip():
                continue

            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                sub_text = text[start:end].strip()
                if sub_text:
                    chunk_counter += 1
                    chunks.append(DocumentChunk(
                        chunk_id=f"{doc_name}_v{version}_p{page_idx+1}_c{chunk_counter}",
                        content=sub_text,
                        metadata={
                            "source_doc": doc_name,
                            "version": version,
                            "doc_type": doc_type.upper(),
                            "section": f"Page {page_idx+1}",
                            "page": page_idx + 1,
                            "length": len(sub_text)
                        }
                    ))
                start += (self.chunk_size - self.chunk_overlap)

        return chunks

    def ingest_file(self, file_path: str, doc_name: str, version: str = "1.0", doc_type: str = "ECU") -> List[DocumentChunk]:
        """Ingest a file from disk based on extension (.md, .txt, .pdf)."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self.parse_pdf(file_path, doc_name, version, doc_type)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self.parse_markdown(content, doc_name, version, doc_type)

    def ingest_raw_text(self, content: str, doc_name: str, version: str = "1.0", doc_type: str = "ECU", section: str = "General") -> List[DocumentChunk]:
        """Ingest raw text or markdown content directly."""
        return self.parse_markdown(content, doc_name, version, doc_type)
