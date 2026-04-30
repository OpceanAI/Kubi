"""Query expansion using LLM with production-grade resilience."""

import asyncio
import json
import logging
import os
import re
from typing import Optional

import httpx

from src.llm.providers import get_provider, get_provider_for_model

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 1.0


class QueryExpander:

    def __init__(
        self, llm_provider: str = "ollama", llm_base_url: Optional[str] = None,
        llm_api_key: Optional[str] = None, llm_model: Optional[str] = None,
        llm_temperature: float = 0.7,
    ):
        self.provider_name = llm_provider.lower()
        self._config = get_provider(self.provider_name)
        if self._config is None:
            self._config = get_provider_for_model(llm_model) if llm_model else get_provider("ollama")

        self.base_url = (llm_base_url or self._config.base_url).rstrip("/")
        self.api_key = llm_api_key or (
            os.environ.get(self._config.api_key_env, "") if self._config.api_key_env else ""
        )
        self.model = llm_model or self._config.default_fast_model or self._config.default_model
        self.temperature = llm_temperature
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=5.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def expand(self, query: str, num_variations: int = 5) -> list[str]:
        prompt = (
            f"You are a search query expansion engine. Given the user's query, generate {num_variations} "
            "alternative search queries that would help find comprehensive information on the topic.\n\n"
            "Rules:\n- Each query should be a different angle or aspect of the original query\n"
            "- Keep queries concise and search-engine friendly\n"
            "- Include the original query in the output\n"
            "- Return ONLY a JSON array of strings, nothing else\n\n"
            f'User query: "{query}"\n\n'
            f"Return a JSON array of {num_variations} search queries (include the original):"
        )

        for attempt in range(MAX_RETRIES):
            try:
                result = await self._call_llm(prompt)
                return self._parse_queries(result, query, num_variations)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF * (2 ** attempt)
                    logger.warning(f"Query expansion failed (attempt {attempt + 1}): {e}. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Query expansion failed after {MAX_RETRIES} retries: {e}")
                    return [query]
            except Exception as e:
                logger.error(f"Query expansion failed: {e}")
                return [query]
        return [query]

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "User-Agent": "Kubi/1.0"}
        if self.api_key:
            headers[self._config.auth_header] = f"{self._config.auth_prefix}{self.api_key}"
        return headers

    async def _call_llm(self, prompt: str) -> str:
        fmt = self._config.api_format
        if fmt == "ollama":
            return await self._call_ollama(prompt)
        if fmt == "anthropic":
            return await self._call_anthropic(prompt)
        return await self._call_openai_compatible(prompt)

    async def _call_ollama(self, prompt: str) -> str:
        client = self._get_client()
        resp = await client.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "stream": False,
                   "options": {"temperature": self.temperature}},
        )
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "")

    async def _call_openai_compatible(self, prompt: str) -> str:
        client = self._get_client()
        resp = await client.post(
            f"{self.base_url}/chat/completions", headers=self._headers(),
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}],
                   "temperature": self.temperature, "max_tokens": 512},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def _call_anthropic(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json", "anthropic-version": "2023-06-01", "User-Agent": "Kubi/1.0"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        client = self._get_client()
        resp = await client.post(
            f"{self.base_url}/messages", headers=headers,
            json={"model": self.model, "max_tokens": 512, "temperature": self.temperature,
                   "messages": [{"role": "user", "content": prompt}]},
        )
        resp.raise_for_status()
        return "".join(b["text"] for b in resp.json().get("content", []) if b.get("type") == "text")

    def _parse_queries(self, llm_output: str, original: str, num: int) -> list[str]:
        json_match = re.search(r'\[.*?\]', llm_output, re.DOTALL)
        if json_match:
            try:
                queries = json.loads(json_match.group())
                if isinstance(queries, list):
                    queries = [q.strip().strip('"') for q in queries if isinstance(q, str) and q.strip()]
                    if original not in queries:
                        queries.insert(0, original)
                    return queries[:num]
            except json.JSONDecodeError:
                pass

        lines = [l.strip().lstrip("0123456789.-) ").strip('"') for l in llm_output.strip().split("\n") if l.strip()]
        queries = [l for l in lines if 3 < len(l) < 200]
        if original not in queries:
            queries.insert(0, original)
        return queries[:num]
