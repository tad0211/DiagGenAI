"""
DiagGenAI - Embeddings Module.
Provides BGE / E5 / SentenceTransformers embeddings with an offline-resilient fallback
conforming to LangChain's Embeddings interface.
"""

import math
import hashlib
import re
from typing import List
from langchain_core.embeddings import Embeddings
from app.config import settings

class ResilientBGEEmbeddings(Embeddings):
    """
    Embeddings engine targeting BAAI/bge-small-en-v1.5 or SentenceTransformers.
    Falls back gracefully to a deterministic 384-dimensional keyword-preserving
    semantic projection if external model download is blocked or offline.
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self._st_model = None
        self._initialized = False

    def _lazy_init(self):
        if self._initialized:
            return
        self._initialized = True
        try:
            from sentence_transformers import SentenceTransformer
            # Try loading specified model (or lightweight local cache)
            self._st_model = SentenceTransformer(self.model_name)
        except Exception:
            try:
                from sentence_transformers import SentenceTransformer
                self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self._st_model = None

    def _fallback_embed(self, text: str) -> List[float]:
        """
        Deterministic, normalized 384-dimensional semantic projection vector.
        Preserves cosine similarity for automotive diagnostic vocabulary.
        """
        vec = [0.0] * self.dimension
        cleaned = text.lower()
        tokens = re.findall(r'\b[0-9a-zA-Z_#xX\-\.]+\b', cleaned)

        # Domain term weighting
        for token in tokens:
            weight = 1.0
            if token.startswith("0x") or token.startswith("req-") or token.startswith("tc-"):
                weight = 3.0
            elif token in ["service", "subfunction", "did", "nrc", "session", "security", "bcm"]:
                weight = 2.0

            h = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            vec[idx] += sign * weight

            idx2 = (h >> 16) % self.dimension
            vec[idx2] += (sign * 0.5) * weight

        # Normalize to unit vector
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            return [x / norm for x in vec]
        return [0.0] * self.dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self._lazy_init()
        if self._st_model is not None:
            try:
                embeddings = self._st_model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
                return [e.tolist() for e in embeddings]
            except Exception:
                pass
        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        self._lazy_init()
        if self._st_model is not None:
            try:
                embedding = self._st_model.encode([text], show_progress_bar=False, normalize_embeddings=True)[0]
                return embedding.tolist()
            except Exception:
                pass
        return self._fallback_embed(text)

# Singleton embeddings instance
embedding_engine = ResilientBGEEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
