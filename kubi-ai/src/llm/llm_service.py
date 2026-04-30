"""Multi-provider LLM service with production-grade resilience."""

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, AsyncGenerator, Optional

import httpx

from .providers import ProviderConfig, get_provider, get_provider_for_model

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0
REQUEST_TIMEOUT = 180.0
CONNECT_TIMEOUT = 10.0


class LLMError(Exception):
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class LLMService:

    def __init__(
        self,
        provider: str = "ollama",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        fast_model: Optional[str] = None,
        reasoning_model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        self.provider_name = provider.lower()
        self._config = get_provider(self.provider_name)
        if self._config is None:
            self._config = ProviderConfig(
                name=provider, base_url=base_url or "http://localhost:8000/v1",
                api_key_env="", api_format="openai", default_model=model or "default",
            )

        self.base_url = (base_url or self._config.base_url).rstrip("/")
        self.api_key = api_key or (
            os.environ.get(self._config.api_key_env, "") if self._config.api_key_env else ""
        )
        self.model = model or self._config.default_model
        self.fast_model = fast_model or self._config.default_fast_model or self.model
        self.reasoning_model = reasoning_model or self._config.default_reasoning_model or self.model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=CONNECT_TIMEOUT),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
                http2=True,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def synthesize(
        self, query: str, contexts: list[str], system_prompt: Optional[str] = None,
        output_schema: Optional[dict[str, Any]] = None, model: Optional[str] = None,
    ) -> str | dict[str, Any]:
        ctx_block = "\n\n---\n\n".join(contexts)

        if output_schema:
            schema_str = json.dumps(output_schema, indent=2)
            system = (
                f"{system_prompt or 'You are a helpful research assistant.'}\n\n"
                "You MUST return your answer as valid JSON matching this schema:\n"
                f"{schema_str}\n\n"
                "Ground each field with source citations where possible. "
                "Return ONLY the JSON object, no markdown fences or explanations."
            )
        else:
            system = system_prompt or (
                "You are a helpful research assistant. Answer the user's question based on the provided sources. "
                "Be concise, accurate, and cite your sources using [Source N] notation. "
                "If the sources don't contain enough information, say so."
            )

        user_msg = f"Question: {query}\n\nSources:\n{ctx_block}"
        target_model = model or (self.reasoning_model if output_schema else self.model)
        response = await self._chat_with_retry(system, user_msg, target_model, self.temperature, self.max_tokens)

        if output_schema:
            return self._parse_structured_output(response, output_schema)
        return response

    async def stream_synthesize(
        self, query: str, contexts: list[str], system_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        ctx_block = "\n\n---\n\n".join(contexts)
        system = system_prompt or (
            "You are a helpful research assistant. Answer the user's question based on the provided sources. "
            "Be concise, accurate, and cite your sources."
        )
        user_msg = f"Question: {query}\n\nSources:\n{ctx_block}"
        target_model = model or self.model
        async for token in self._stream_with_retry(system, user_msg, target_model, self.temperature, self.max_tokens):
            yield token

    async def generate_summary(self, text: str, query: Optional[str] = None, max_chars: int = 2000) -> str:
        prompt = "Summarize the following content"
        if query:
            prompt += f" in relation to the query: '{query}'"
        prompt += f". Be concise and informative. Keep it under {max_chars} characters.\n\nContent:\n{text}"
        return await self._chat_with_retry(
            "You are a content summarization assistant. Be concise and informative.",
            prompt, self.fast_model, 0.2, 512,
        )

    async def generate_highlights(self, text: str, query: str, max_chars: int = 4000) -> list[str]:
        prompt = (
            f'Extract the most relevant excerpts from the following content related to the query: "{query}"\n\n'
            f"Rules:\n- Return ONLY the most relevant passages (3-8 excerpts)\n"
            f"- Each excerpt should be 1-3 sentences\n"
            f"- Total output should be under {max_chars} characters\n"
            f"- Return as a JSON array of strings\n\n"
            f"Content:\n{text[:8000]}\n\n"
            f"Return a JSON array of relevant excerpts:"
        )
        result = await self._chat_with_retry("You are a content extraction assistant.", prompt, self.fast_model, 0.1, 1024)

        try:
            json_match = re.search(r'\[.*?\]', result, re.DOTALL)
            if json_match:
                highlights = json.loads(json_match.group())
                if isinstance(highlights, list):
                    return [str(h) for h in highlights][:10]
        except Exception:
            pass
        return [result[:max_chars]]

    async def _chat_with_retry(self, system: str, user: str, model: str, temperature: float, max_tokens: int) -> str:
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return await self._chat(system, user, model, temperature, max_tokens)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                wait = RETRY_BACKOFF_BASE * (2 ** attempt)
                logger.warning(f"LLM request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. Retrying in {wait}s...")
                await asyncio.sleep(wait)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    last_error = e
                    wait = RETRY_BACKOFF_BASE * (2 ** attempt) * 2
                    logger.warning(f"Rate limited (attempt {attempt + 1}/{MAX_RETRIES}). Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                elif e.response.status_code >= 500:
                    last_error = e
                    wait = RETRY_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"Server error {e.response.status_code} (attempt {attempt + 1}/{MAX_RETRIES}). Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    raise LLMError(f"LLM request failed: {e}", self.provider_name, e.response.status_code)
        raise LLMError(f"LLM request failed after {MAX_RETRIES} retries: {last_error}", self.provider_name)

    async def _stream_with_retry(
        self, system: str, user: str, model: str, temperature: float, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        for attempt in range(MAX_RETRIES):
            try:
                async for token in self._chat_stream(system, user, model, temperature, max_tokens):
                    yield token
                return
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"Stream failed (attempt {attempt + 1}): {e}. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    raise LLMError(f"Stream failed after {MAX_RETRIES} retries: {e}", self.provider_name)

    async def _chat(self, system: str, user: str, model: str, temperature: float, max_tokens: int) -> str:
        fmt = self._config.api_format
        if fmt == "ollama":
            return await self._ollama_chat(system, user, model, temperature, max_tokens)
        if fmt == "anthropic":
            return await self._anthropic_chat(system, user, model, temperature, max_tokens)
        return await self._openai_chat(system, user, model, temperature, max_tokens)

    async def _chat_stream(
        self, system: str, user: str, model: str, temperature: float, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        fmt = self._config.api_format
        if fmt == "ollama":
            async for t in self._ollama_stream(system, user, model, temperature, max_tokens):
                yield t
        elif fmt == "anthropic":
            async for t in self._anthropic_stream(system, user, model, temperature, max_tokens):
                yield t
        else:
            async for t in self._openai_stream(system, user, model, temperature, max_tokens):
                yield t

    def _openai_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "User-Agent": "Kubi/1.0"}
        if self.api_key:
            headers[self._config.auth_header] = f"{self._config.auth_prefix}{self.api_key}"
        return headers

    def _anthropic_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "anthropic-version": "2023-06-01", "User-Agent": "Kubi/1.0"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def _messages(self, system: str, user: str) -> list[dict]:
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    async def _ollama_chat(self, system: str, user: str, model: str, temperature: float, max_tokens: int) -> str:
        client = self._get_client()
        resp = await client.post(
            f"{self.base_url}/api/chat",
            json={"model": model, "messages": self._messages(system, user), "stream": False,
                   "options": {"temperature": temperature, "num_predict": max_tokens}},
        )
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "")

    async def _ollama_stream(
        self, system: str, user: str, model: str, temperature: float, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()
        async with client.stream(
            "POST", f"{self.base_url}/api/chat",
            json={"model": model, "messages": self._messages(system, user), "stream": True,
                   "options": {"temperature": temperature, "num_predict": max_tokens}},
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.strip():
                    try:
                        content = json.loads(line).get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def _openai_chat(self, system: str, user: str, model: str, temperature: float, max_tokens: int) -> str:
        client = self._get_client()
        resp = await client.post(
            f"{self.base_url}/chat/completions", headers=self._openai_headers(),
            json={"model": model, "messages": self._messages(system, user),
                   "temperature": temperature, "max_tokens": max_tokens},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def _openai_stream(
        self, system: str, user: str, model: str, temperature: float, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()
        async with client.stream(
            "POST", f"{self.base_url}/chat/completions", headers=self._openai_headers(),
            json={"model": model, "messages": self._messages(system, user),
                   "temperature": temperature, "max_tokens": max_tokens, "stream": True},
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line.strip() != "data: [DONE]":
                    try:
                        delta = json.loads(line[6:]).get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, IndexError):
                        continue

    async def _anthropic_chat(self, system: str, user: str, model: str, temperature: float, max_tokens: int) -> str:
        client = self._get_client()
        resp = await client.post(
            f"{self.base_url}/messages", headers=self._anthropic_headers(),
            json={"model": model, "max_tokens": max_tokens, "temperature": temperature,
                   "system": system, "messages": [{"role": "user", "content": user}]},
        )
        resp.raise_for_status()
        return "".join(b["text"] for b in resp.json().get("content", []) if b.get("type") == "text")

    async def _anthropic_stream(
        self, system: str, user: str, model: str, temperature: float, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()
        async with client.stream(
            "POST", f"{self.base_url}/messages", headers=self._anthropic_headers(),
            json={"model": model, "max_tokens": max_tokens, "temperature": temperature,
                   "system": system, "messages": [{"role": "user", "content": user}], "stream": True},
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "content_block_delta":
                            text = data.get("delta", {}).get("text", "")
                            if text:
                                yield text
                    except (json.JSONDecodeError, KeyError):
                        continue

    def _parse_structured_output(self, response: str, schema: dict) -> dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {"answer": response}

    def get_config(self) -> dict:
        return {
            "provider": self.provider_name, "base_url": self.base_url,
            "api_format": self._config.api_format, "model": self.model,
            "fast_model": self.fast_model, "reasoning_model": self.reasoning_model,
            "has_api_key": bool(self.api_key), "temperature": self.temperature,
            "max_tokens": self.max_tokens, "max_context": self._config.max_context,
        }
