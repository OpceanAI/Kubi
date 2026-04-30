"""SearXNG meta-search engine with production-grade resilience."""

import asyncio
import logging
from typing import Optional
from urllib.parse import urljoin

import httpx

from src.models.schemas import SearchResult

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
REQUEST_TIMEOUT = 15.0


class SearXNGSearcher:

    def __init__(self, base_url: str, engines: str = "google,bing,duckduckgo"):
        self.base_url = base_url.rstrip("/")
        self.engines = [e.strip() for e in engines.split(",") if e.strip()]
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=5.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def search(
        self, query: str, num_results: int = 10,
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
        categories: Optional[str] = None,
    ) -> list[SearchResult]:
        client = self._get_client()

        params: dict[str, str | int] = {"q": query, "format": "json", "pageno": 1}
        if categories:
            params["categories"] = categories
        if self.engines:
            params["engines"] = ",".join(self.engines)

        search_query = query
        if include_domains:
            search_query = f"{query} ({' OR '.join(f'site:{d}' for d in include_domains)})"
        if exclude_domains:
            search_query = f"{search_query} {' '.join(f'-site:{d}' for d in exclude_domains)}"
        params["q"] = search_query

        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.get(urljoin(self.base_url + "/", "search"), params=params)
                resp.raise_for_status()
                data = resp.json()
                return [
                    SearchResult(
                        title=item.get("title", ""), url=item.get("url", ""),
                        snippet=item.get("content", ""), published_date=item.get("publishedDate"),
                        author=item.get("author"),
                        domain=item.get("parsed_url", ["", ""])[1] if item.get("parsed_url") else "",
                        score=item.get("score", 0.0), image=item.get("thumbnail"),
                        favicon=item.get("favicon"),
                    )
                    for item in data.get("results", [])[:num_results]
                ]
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"SearXNG request failed (attempt {attempt + 1}): {e}. Retrying...")
                    await asyncio.sleep(0.5)
                else:
                    logger.error(f"SearXNG request failed after {MAX_RETRIES} retries: {e}")
                    return []
            except Exception as e:
                logger.error(f"SearXNG request failed: {e}")
                return []
        return []
