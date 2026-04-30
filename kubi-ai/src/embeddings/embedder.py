"""Embedding service using Sentence Transformers."""

import asyncio
import logging

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)

    async def embed(self, text: str) -> list[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension
        self._load_model()
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: self._model.encode(text, normalize_embeddings=True)
        )
        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        self._load_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False),
        )
        return [e.tolist() for e in embeddings]

    async def similarity(self, text1: str, text2: str) -> float:
        emb1 = await self.embed(text1)
        emb2 = await self.embed(text2)
        a, b = np.array(emb1), np.array(emb2)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)
