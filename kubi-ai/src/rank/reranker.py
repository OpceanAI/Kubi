"""Cross-encoder reranker."""

import asyncio
import logging

from src.models.schemas import SearchResult

logger = logging.getLogger(__name__)


class Reranker:

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading reranker model: {self.model_name}")
            self._model = CrossEncoder(self.model_name)

    async def rerank(self, query: str, results: list[SearchResult], top_k: int = 10) -> list[SearchResult]:
        if not results:
            return []

        self._load_model()
        pairs = [(query, f"{r.title} {r.snippet}") for r in results]

        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(None, lambda: self._model.predict(pairs))

        scored = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
        for result, score in scored[:top_k]:
            result.score = float(score)

        return [r for r, _ in scored[:top_k]]
