"""Find similar service using Qdrant vector search."""

import logging
from typing import Optional
from urllib.parse import urlparse

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from src.models.schemas import SearchResult, SimilarResponse

logger = logging.getLogger(__name__)

COLLECTION_WEB_PAGES = "web_pages"
COLLECTION_CACHED_RESULTS = "cached_results"
COLLECTION_DOCUMENTS = "documents"


class SimilarService:

    def __init__(self, embedder, qdrant_host: str = "qdrant", qdrant_port: int = 6333, dimension: int = 384):
        self.embedder = embedder
        self.dimension = dimension
        self._client: Optional[QdrantClient] = None
        self._host = qdrant_host
        self._port = qdrant_port

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(host=self._host, port=self._port, timeout=10)
        return self._client

    async def init_collections(self):
        client = self._get_client()
        existing = [c.name for c in client.get_collections().collections]
        for name in [COLLECTION_WEB_PAGES, COLLECTION_CACHED_RESULTS, COLLECTION_DOCUMENTS]:
            if name not in existing:
                client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection: {name}")

    async def store_results(self, results: list[SearchResult], embeddings: list[list[float]], collection: str = COLLECTION_CACHED_RESULTS):
        client = self._get_client()
        points = [
            PointStruct(
                id=abs(hash(r.url)) % (2**63),
                vector=emb,
                payload={"url": r.url, "title": r.title, "snippet": r.snippet,
                         "domain": r.domain, "published_date": r.published_date or "",
                         "author": r.author or "", "score": r.score},
            )
            for r, emb in zip(results, embeddings)
        ]
        if points:
            client.upsert(collection_name=collection, points=points)

    async def find_similar(
        self, url: str, query: Optional[str] = None,
        num_results: int = 10, include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
    ) -> SimilarResponse:
        client = self._get_client()
        embedding = await self.embedder.embed(query or url)

        conditions = [
            FieldCondition(key="domain", match=MatchValue(value=d))
            for d in (include_domains or [])
        ]
        query_filter = Filter(must=conditions) if conditions else None

        all_results = []
        for collection_name in [COLLECTION_CACHED_RESULTS, COLLECTION_WEB_PAGES]:
            try:
                hits = client.search(
                    collection_name=collection_name, query_vector=embedding,
                    limit=num_results, query_filter=query_filter, score_threshold=0.3,
                )
                for hit in hits:
                    payload = hit.payload or {}
                    if payload.get("url") == url:
                        continue
                    hit_domain = urlparse(payload.get("url", "")).netloc
                    if exclude_domains and any(d in hit_domain for d in exclude_domains):
                        continue
                    all_results.append(SearchResult(
                        title=payload.get("title", ""), url=payload.get("url", ""),
                        snippet=payload.get("snippet", ""), domain=hit_domain,
                        published_date=payload.get("published_date"),
                        author=payload.get("author"), score=hit.score,
                    ))
            except Exception as e:
                logger.warning(f"Search in {collection_name} failed: {e}")

        seen = set()
        unique = []
        for r in all_results:
            if r.url not in seen:
                seen.add(r.url)
                unique.append(r)

        unique.sort(key=lambda x: x.score, reverse=True)
        return SimilarResponse(results=unique[:num_results], source_url=url, total=len(unique[:num_results]))

    async def close(self):
        if self._client:
            self._client.close()
            self._client = None
