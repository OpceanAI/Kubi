"""DuckDuckGo search backend."""

import logging
from typing import Optional
from urllib.parse import urlparse

from src.models.schemas import SearchResult

logger = logging.getLogger(__name__)


class DuckDuckGoSearcher:

    def __init__(self):
        self._ddgs = None

    def _get_ddgs(self):
        if self._ddgs is None:
            from duckduckgo_search import DDGS
            self._ddgs = DDGS()
        return self._ddgs

    async def search(
        self,
        query: str,
        num_results: int = 10,
        region: str = "wt-wt",
        safesearch: str = "moderate",
        time_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        ddgs = self._get_ddgs()
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            raw_results = await loop.run_in_executor(
                None,
                lambda: ddgs.text(
                    query=query, region=region, safesearch=safesearch,
                    timelimit=time_filter, max_results=num_results,
                ),
            )
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("href", ""),
                snippet=item.get("body", ""),
                domain=urlparse(item.get("href", "")).netloc,
                score=0.5,
            )
            for item in raw_results
        ]

    async def close(self):
        if self._ddgs:
            try:
                if hasattr(self._ddgs, 'close'):
                    self._ddgs.close()
            except Exception:
                pass
            self._ddgs = None
