"""Intelligent LLM Router - Auto-selects the best provider based on query, config, and availability."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from .providers import ProviderConfig, get_provider, PROVIDERS

logger = logging.getLogger(__name__)


@dataclass
class ProviderHealth:
    name: str
    available: bool = True
    last_error: Optional[str] = None
    last_error_time: float = 0.0
    consecutive_failures: int = 0
    avg_latency_ms: float = 0.0
    total_requests: int = 0
    total_failures: int = 0

    def record_success(self, latency_ms: float):
        self.total_requests += 1
        self.consecutive_failures = 0
        self.available = True
        self.avg_latency_ms = (self.avg_latency_ms * 0.8) + (latency_ms * 0.2)

    def record_failure(self, error: str):
        self.total_requests += 1
        self.total_failures += 1
        self.consecutive_failures += 1
        self.last_error = error
        self.last_error_time = time.time()
        if self.consecutive_failures >= 3:
            self.available = False

    def reset_if_cooldown(self, cooldown_seconds: int = 60):
        if not self.available and (time.time() - self.last_error_time) > cooldown_seconds:
            self.available = True
            self.consecutive_failures = 0


@dataclass
class Preset:
    name: str
    description: str
    search_type: str = "auto"
    num_results: int = 10
    category: Optional[str] = None
    contents: Optional[dict] = None
    system_prompt: Optional[str] = None
    output_schema: Optional[dict] = None


PRESETS: dict[str, Preset] = {
    "quick-search": Preset(
        name="quick-search",
        description="Fast search with minimal processing",
        search_type="fast",
        num_results=5,
        contents={"highlights": {"maxCharacters": 2000}},
    ),
    "pro-search": Preset(
        name="pro-search",
        description="Comprehensive search with LLM synthesis and citations",
        search_type="deep-lite",
        num_results=10,
        contents={"highlights": {"maxCharacters": 4000}, "summary": True},
        system_prompt="You are a research assistant. Provide comprehensive, well-sourced answers. Cite all sources using [Source N] notation.",
    ),
    "deep-research": Preset(
        name="deep-research",
        description="Exhaustive multi-step research with comprehensive reports",
        search_type="deep-reasoning",
        num_results=20,
        contents={"text": {"maxCharacters": 15000}, "highlights": {"maxCharacters": 4000}, "summary": True, "subpages": 3},
        system_prompt="You are a deep research analyst. Conduct exhaustive research on the topic. Synthesize information from multiple sources into a comprehensive report with sections, citations, and analysis. Structure your report with clear headings.",
    ),
    "company-research": Preset(
        name="company-research",
        description="Research companies with structured output",
        search_type="deep",
        num_results=10,
        category="company",
        contents={"highlights": {"maxCharacters": 4000}},
    ),
    "news-monitoring": Preset(
        name="news-monitoring",
        description="Monitor recent news on a topic",
        search_type="fast",
        num_results=10,
        category="news",
        contents={"highlights": {"maxCharacters": 3000}},
    ),
    "academic-research": Preset(
        name="academic-research",
        description="Search academic papers and research",
        search_type="deep-lite",
        num_results=15,
        category="research paper",
        contents={"highlights": {"maxCharacters": 5000}, "summary": True},
    ),
}


def get_preset(name: str) -> Optional[Preset]:
    return PRESETS.get(name)


def list_presets() -> list[dict]:
    return [{"name": p.name, "description": p.description, "search_type": p.search_type} for p in PRESETS.values()]


class IntelligentRouter:

    def __init__(self):
        self._health: dict[str, ProviderHealth] = {}
        self._configured_providers: list[str] = []
        self._discover_providers()

    def _discover_providers(self):
        for name, config in PROVIDERS.items():
            api_key = os.environ.get(config.api_key_env, "") if config.api_key_env else ""
            has_key = bool(api_key) or name in ("ollama", "local")
            if has_key:
                self._configured_providers.append(name)
                self._health[name] = ProviderHealth(name=name, available=True)
                logger.info(f"Configured provider: {name}")

    def get_configured_providers(self) -> list[str]:
        return self._configured_providers.copy()

    def select_provider(
        self,
        query: str,
        mode: str = "auto",
        preferred_provider: Optional[str] = None,
        fallback_chain: bool = True,
    ) -> tuple[str, list[str]]:
        if preferred_provider and preferred_provider in self._configured_providers:
            if fallback_chain:
                others = [p for p in self._configured_providers if p != preferred_provider]
                return preferred_provider, [preferred_provider] + others
            return preferred_provider, [preferred_provider]

        query_lower = query.lower()

        if any(w in query_lower for w in ["latest", "recent", "today", "news", "current", "2026", "2025"]):
            priority = ["perplexity", "deepseek", "openai", "claude", "groq"]
        elif any(w in query_lower for w in ["code", "programming", "python", "javascript", "api", "debug"]):
            priority = ["deepseek", "openai", "groq", "together", "claude"]
        elif any(w in query_lower for w in ["research", "paper", "study", "academic", "scientific"]):
            priority = ["perplexity", "claude", "openai", "deepseek", "mistral"]
        elif any(w in query_lower for w in ["creative", "write", "story", "poem", "essay"]):
            priority = ["claude", "openai", "kimi", "mistral", "cohere"]
        elif any(w in query_lower for w in ["analyze", "compare", "evaluate", "reasoning", "logic"]):
            priority = ["claude", "openai", "deepseek", "mistral", "perplexity"]
        elif mode in ("deep", "deep-reasoning", "research"):
            priority = ["claude", "openai", "deepseek", "perplexity", "mistral"]
        elif mode == "fast" or mode == "instant":
            priority = ["groq", "deepseek", "mimo", "ollama", "together"]
        else:
            priority = ["openai", "claude", "deepseek", "mistral", "groq", "perplexity", "kimi", "cohere", "together"]

        available = [p for p in self._configured_providers if self._health.get(p, ProviderHealth(name=p)).available]

        selected = [p for p in priority if p in available]
        remaining = [p for p in available if p not in selected]
        chain = selected + remaining

        if not chain:
            return "ollama", ["ollama"]

        return chain[0], chain

    def record_success(self, provider: str, latency_ms: float):
        if provider in self._health:
            self._health[provider].record_success(latency_ms)

    def record_failure(self, provider: str, error: str):
        if provider in self._health:
            self._health[provider].record_failure(error)
            logger.warning(f"Provider {provider} failed: {error} (consecutive: {self._health[provider].consecutive_failures})")

    def get_health_status(self) -> dict[str, dict]:
        return {
            name: {
                "available": h.available,
                "avg_latency_ms": round(h.avg_latency_ms, 1),
                "total_requests": h.total_requests,
                "total_failures": h.total_failures,
                "consecutive_failures": h.consecutive_failures,
                "last_error": h.last_error,
            }
            for name, h in self._health.items()
        }

    def reset_unavailable(self):
        for h in self._health.values():
            h.reset_if_cooldown()


router = IntelligentRouter()
