"""LLM Provider Registry - Latest models as of April 2026."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    api_key_env: str
    auth_header: str = "Authorization"
    auth_prefix: str = "Bearer "
    api_format: str = "openai"
    default_model: str = ""
    default_fast_model: str = ""
    default_reasoning_model: str = ""
    max_context: int = 128000
    supports_streaming: bool = True
    supports_system_prompt: bool = True


PROVIDERS: dict[str, ProviderConfig] = {
    "ollama": ProviderConfig(
        name="ollama",
        base_url="http://ollama:11434",
        api_key_env="",
        api_format="ollama",
        default_model="qwen3:8b",
        default_fast_model="qwen3:1.7b",
        default_reasoning_model="deepseek-r1:7b",
    ),
    "openai": ProviderConfig(
        name="openai",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-5",
        default_fast_model="gpt-5-mini",
        default_reasoning_model="o3-mini",
        max_context=1047576,
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        base_url="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        default_model="deepseek-v4-flash",
        default_fast_model="deepseek-v4-flash",
        default_reasoning_model="deepseek-v4-pro",
        max_context=1000000,
    ),
    "claude": ProviderConfig(
        name="claude",
        base_url="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        auth_header="x-api-key",
        auth_prefix="",
        api_format="anthropic",
        default_model="claude-4-sonnet",
        default_fast_model="claude-4-haiku",
        default_reasoning_model="claude-4-opus",
        max_context=1000000,
    ),
    "kimi": ProviderConfig(
        name="kimi",
        base_url="https://api.moonshot.ai/v1",
        api_key_env="KIMI_API_KEY",
        default_model="kimi-k2",
        default_fast_model="kimi-k2",
        default_reasoning_model="kimi-k2-thinking",
        max_context=131072,
    ),
    "mimo": ProviderConfig(
        name="mimo",
        base_url="https://api.xiaomimimo.com/v1",
        api_key_env="MIMO_API_KEY",
        default_model="mimo-v2.5",
        default_fast_model="mimo-v2-flash",
        default_reasoning_model="mimo-v2.5-pro",
        max_context=131072,
    ),
    "groq": ProviderConfig(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        default_model="llama-3.3-70b-versatile",
        default_fast_model="llama-3.1-8b-instant",
        default_reasoning_model="deepseek-r1-distill-llama-70b",
        max_context=131072,
    ),
    "together": ProviderConfig(
        name="together",
        base_url="https://api.together.xyz/v1",
        api_key_env="TOGETHER_API_KEY",
        default_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        default_fast_model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        default_reasoning_model="deepseek-ai/DeepSeek-R1",
        max_context=131072,
    ),
    "openrouter": ProviderConfig(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        default_model="anthropic/claude-4-sonnet",
        default_fast_model="meta-llama/llama-3.1-8b-instruct",
        default_reasoning_model="deepseek/deepseek-r1",
        max_context=1000000,
    ),
    "mistral": ProviderConfig(
        name="mistral",
        base_url="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
        default_model="mistral-large-latest",
        default_fast_model="mistral-small-latest",
        default_reasoning_model="magistral-medium-latest",
        max_context=131072,
    ),
    "perplexity": ProviderConfig(
        name="perplexity",
        base_url="https://api.perplexity.ai",
        api_key_env="PERPLEXITY_API_KEY",
        default_model="sonar-pro",
        default_fast_model="sonar",
        default_reasoning_model="sonar-reasoning-pro",
        max_context=131072,
    ),
    "cohere": ProviderConfig(
        name="cohere",
        base_url="https://api.cohere.com/v2",
        api_key_env="COHERE_API_KEY",
        auth_header="Authorization",
        auth_prefix="Bearer ",
        api_format="openai",
        default_model="command-a",
        default_fast_model="command-r-plus",
        default_reasoning_model="command-a",
        max_context=131072,
    ),
    "fireworks": ProviderConfig(
        name="fireworks",
        base_url="https://api.fireworks.ai/inference/v1",
        api_key_env="FIREWORKS_API_KEY",
        default_model="accounts/fireworks/models/llama-v3p3-70b-instruct",
        default_fast_model="accounts/fireworks/models/llama-v3p1-8b-instruct",
        default_reasoning_model="accounts/fireworks/models/deepseek-r1",
        max_context=131072,
    ),
    "local": ProviderConfig(
        name="local",
        base_url="http://localhost:1234/v1",
        api_key_env="LOCAL_LLM_API_KEY",
        default_model="local-model",
        default_fast_model="local-model",
        default_reasoning_model="local-model",
        max_context=32768,
    ),
}


def get_provider(name: str) -> Optional[ProviderConfig]:
    return PROVIDERS.get(name.lower())


def get_provider_for_model(model: str) -> ProviderConfig:
    model_lower = model.lower()
    if model_lower.startswith(("gpt-", "o1-", "o3-", "o4-")):
        return PROVIDERS["openai"]
    if model_lower.startswith("deepseek"):
        return PROVIDERS["deepseek"]
    if model_lower.startswith("claude"):
        return PROVIDERS["claude"]
    if model_lower.startswith(("moonshot", "kimi")):
        return PROVIDERS["kimi"]
    if model_lower.startswith("mimo"):
        return PROVIDERS["mimo"]
    if model_lower.startswith(("llama", "mixtral", "gemma", "qwen")):
        return PROVIDERS["groq"]
    if model_lower.startswith("mistral") or model_lower.startswith("magistral") or model_lower.startswith("devstral"):
        return PROVIDERS["mistral"]
    if model_lower.startswith("sonar"):
        return PROVIDERS["perplexity"]
    if model_lower.startswith("command"):
        return PROVIDERS["cohere"]
    return PROVIDERS["ollama"]


def list_providers() -> list[dict]:
    return [
        {
            "name": name,
            "base_url": config.base_url,
            "api_format": config.api_format,
            "default_model": config.default_model,
            "default_fast_model": config.default_fast_model,
            "default_reasoning_model": config.default_reasoning_model,
            "max_context": config.max_context,
            "has_api_key": bool(os.environ.get(config.api_key_env, "")) if config.api_key_env else False,
            "env_var": config.api_key_env or "none",
        }
        for name, config in PROVIDERS.items()
    ]
