<p align="center">
  <img src="https://img.shields.io/badge/Kubi-v1.0.0-00D4AA?style=for-the-badge&labelColor=0A0A0A" alt="Kubi v1.0.0">
  <img src="https://img.shields.io/badge/License-EPL--2.0-00D4AA?style=for-the-badge&labelColor=0A0A0A" alt="License">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&labelColor=0A0A0A&logo=python&logoColor=3776AB" alt="Python">
  <img src="https://img.shields.io/badge/Rust-1.83+-DEA584?style=for-the-badge&labelColor=0A0A0A&logo=rust&logoColor=DEA584" alt="Rust">
  <img src="https://img.shields.io/badge/TypeScript-5.7+-3178C6?style=for-the-badge&labelColor=0A0A0A&logo=typescript&logoColor=3178C6" alt="TypeScript">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&labelColor=0A0A0A&logo=docker&logoColor=2496ED" alt="Docker Compose">
  <img src="https://img.shields.io/badge/Qdrant-Vector_DB-DC2954?style=for-the-badge&labelColor=0A0A0A" alt="Qdrant">
  <img src="https://img.shields.io/badge/SearXNG-Metasearch-3058A5?style=for-the-badge&labelColor=0A0A0A" alt="SearXNG">
  <img src="https://img.shields.io/badge/MCP-Compatible-FF6B35?style=for-the-badge&labelColor=0A0A0A" alt="MCP Compatible">
</p>

---

<p align="center">
  <strong>Kubi</strong> is a self-hosted, open-source AI search engine designed as a production-grade alternative to Exa Search. It provides semantic web search, hybrid retrieval, multi-provider LLM reasoning, and full API compatibility — running entirely on your own infrastructure.
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> ·
  <a href="#api-reference">API Reference</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#llm-providers">Providers</a> ·
  <a href="#deployment">Deployment</a> ·
  <a href="#mcp-integration">MCP</a>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quickstart](#quickstart)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Search Modes](#search-modes)
- [LLM Providers](#llm-providers)
- [Intelligent Routing](#intelligent-routing)
- [MCP Integration](#mcp-integration)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Development](#development)
- [License](#license)

---

## Overview

Kubi is search infrastructure for AI systems. It enables:

- **Semantic web search** using embeddings-based retrieval
- **Hybrid retrieval** combining vector search with keyword-based search
- **AI reasoning** over retrieved results with multi-provider LLM support
- **Full self-hosted deployment** with no dependency on external search APIs
- **Production-grade resilience** with automatic failover, retry logic, and health monitoring

If Exa is search as a service, Kubi is search as infrastructure.

### Design Principles

| Principle | Description |
|:----------|:------------|
| **User owns infrastructure** | Full control over models, data, and execution flow |
| **No mandatory cloud dependency** | Runs entirely on private infrastructure |
| **Modular architecture** | Replaceable components (models, search, storage) |
| **Scalable** | From local machine to distributed systems |
| **API-compatible** | Drop-in replacement for Exa Search API |

---

## Key Features

### Search Capabilities

- **Hybrid Search**: Combines semantic vector search (Qdrant) with keyword-based search (SearXNG, DuckDuckGo)
- **Multi-Query Search**: Process up to 5 queries simultaneously in a single request
- **Content Extraction**: Clean, LLM-ready content from any URL via Playwright + Trafilatura
- **Subpage Crawling**: Automatically discover and extract content from linked pages
- **Highlights**: Token-efficient excerpts (10x fewer tokens than full text)
- **Summaries**: LLM-generated abstracts with structured output support
- **Find Similar**: Semantic similarity search via vector embeddings

### Filtering and Control

- **Domain Filtering**: Allowlist and denylist modes (max 1,200 domains)
- **Language Filtering**: ISO 639-1 language codes (max 10 languages)
- **Recency Filtering**: Quick filters for day, week, month, year
- **Date Range Filtering**: ISO 8601 start/end date filters
- **Category Filtering**: company, people, research paper, news, personal site, financial report
- **Content Moderation**: Configurable safe search levels (off, moderate, strict)
- **Geographic Localization**: Country-specific results via ISO 3166-1 codes

### LLM Integration

- **15 Providers**: OpenAI, Claude, DeepSeek, Kimi, MiMo, Groq, Together, OpenRouter, Mistral, Perplexity, Cohere, Fireworks, Ollama, Local, Custom
- **Intelligent Routing**: Automatic provider selection based on query type and provider health
- **Model Fallback Chains**: Automatic failover to next available provider on failure
- **Streaming**: Server-Sent Events (SSE) for real-time token streaming
- **Structured Output**: JSON Schema support for typed responses with field-level grounding

### Agent API

- **Tool-Based Architecture**: Web search and URL fetch as callable tools
- **Presets**: Pre-configured profiles (quick-search, pro-search, deep-research, company-research, news-monitoring, academic-research)
- **Deep Research**: Asynchronous multi-step research with comprehensive report generation
- **Multi-Turn Conversations**: Response chaining via `previous_response_id`

### Integration

- **MCP Server**: Compatible with Claude Desktop, Cursor, VS Code, Windsurf, Zed, and 10+ other clients
- **OpenAI SDK Compatible**: `/v1/chat/completions` endpoint works with existing OpenAI integrations
- **Agent API**: `/v1/agent` and `/v1/responses` endpoints for tool-based workflows

---

## Quickstart

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM (8GB recommended)
- An API key for at least one LLM provider (or Ollama for local models)

### Installation

```bash
# Clone the repository
git clone https://github.com/OpceanAI/Kubi.git
cd Kubi

# Copy environment configuration
cp .env.example .env

# Edit .env with your API keys
# At minimum, set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, DEEPSEEK_API_KEY

# Start all services
docker compose up -d

# Verify health
curl http://localhost:3000/health
```

### First Search

```bash
curl -X POST http://localhost:3000/api/v1/search \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-kubi-change-me-in-production" \
  -d '{
    "query": "latest developments in AI agents",
    "type": "auto",
    "numResults": 5,
    "contents": {
      "highlights": {
        "maxCharacters": 4000
      }
    }
  }'
```

### Ask a Question

```bash
curl -X POST http://localhost:3000/api/v1/ask \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-kubi-change-me-in-production" \
  -d '{
    "query": "What are the most significant AI breakthroughs in 2026?",
    "type": "deep-lite",
    "numResults": 10
  }'
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Clients                                  │
│  (Web Apps, AI Assistants, MCP Clients, OpenAI SDK)             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    kubi-api (Bun + Hono)                         │
│                    Port 3000 · Public API                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Auth    │ │  Rate    │ │  Routes  │ │  Validation      │   │
│  │  Middleware│ │  Limiter │ │  (15)   │ │  (Zod schemas)   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   kubi-core (Axum/Rust)                          │
│                   Port 8080 · Orchestrator                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Routing │ │  Cache   │ │  Health  │ │  Streaming       │   │
│  │  Engine  │ │  (Redis) │ │  Checks  │ │  Proxy           │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   kubi-ai (FastAPI/Python)                       │
│                   Port 8000 · Intelligence Layer                 │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Search      │  │  LLM         │  │  Content             │  │
│  │  ┌─────────┐ │  │  ┌─────────┐ │  │  ┌───────────────┐   │  │
│  │  │ SearXNG │ │  │  │ Router  │ │  │  │ Playwright    │   │  │
│  │  │ DuckDG  │ │  │  │ 15 Prov │ │  │  │ Trafilatura   │   │  │
│  │  └─────────┘ │  │  └─────────┘ │  │  └───────────────┘   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Embeddings  │  │  Reranking   │  │  Vector DB           │  │
│  │  Sentence    │  │  Cross-      │  │  Qdrant              │  │
│  │  Transformers│  │  Encoder     │  │  (3 collections)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Service Communication

| Layer | Technology | Port | Protocol | Role |
|:------|:-----------|:-----|:---------|:-----|
| **kubi-api** | Bun + Hono | 3000 | HTTP | Public API, auth, validation |
| **kubi-core** | Rust + Axum | 8080 | HTTP | Orchestration, caching, health |
| **kubi-ai** | Python + FastAPI | 8000 | HTTP | Search, LLM, embeddings, crawling |
| **Qdrant** | Vector Database | 6333 | gRPC/HTTP | Semantic search, embeddings storage |
| **SearXNG** | Meta Search | 8080 | HTTP | Web search aggregation |
| **Redis** | Cache | 6379 | TCP | Response caching, rate limiting |
| **Ollama** | LLM Server | 11434 | HTTP | Local model inference (optional) |
| **kubi-mcp** | Bun + MCP SDK | 3001 | HTTP | MCP protocol server |

---

## API Reference

All endpoints are Exa Search API compatible. Base URL: `/api/v1`

### Endpoints

| Endpoint | Method | Description | Exa Equivalent |
|:---------|:-------|:------------|:---------------|
| `/search` | POST | Hybrid search with nested contents | `POST /search` |
| `/contents` | POST | Batch URL content extraction | `POST /contents` |
| `/ask` | POST | Search + LLM reasoning with citations | `POST /answer` |
| `/stream` | POST | Streaming version of `/ask` (SSE) | `/answer?stream=true` |
| `/expand` | POST | Query expansion for better retrieval | `additionalQueries` |
| `/crawl` | POST | Crawl and extract URL content | (internal) |
| `/embed` | POST | Generate text embeddings | (internal) |
| `/similar` | POST | Find similar pages by URL | find similar |
| `/research` | POST | Deep research task (async) | Deep Research |
| `/chat/completions` | POST | OpenAI SDK compatible endpoint | — |
| `/chat/agent` | POST | Agent API with tools | — |
| `/chat/responses` | POST | OpenAI Responses API compatible | — |
| `/presets` | GET | List available presets | — |
| `/providers` | GET | Provider health status | — |

### Search Parameters

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `query` | `string \| string[]` | required | Natural language query or array of queries (max 5) |
| `type` | `string` | `"auto"` | Search mode: `instant`, `fast`, `auto`, `deep-lite`, `deep`, `deep-reasoning` |
| `numResults` | `integer` | `10` | Number of results (1-100) |
| `category` | `string` | — | `company`, `people`, `research paper`, `news`, `personal site`, `financial report` |
| `country` | `string` | — | ISO 3166-1 country code for geo-localized results |
| `includeDomains` | `string[]` | — | Only return results from these domains (max 1,200) |
| `excludeDomains` | `string[]` | — | Exclude results from these domains (max 1,200) |
| `searchDomainFilter` | `string[]` | — | Combined allowlist/denylist (prefix with `-` to exclude) |
| `searchLanguageFilter` | `string[]` | — | ISO 639-1 language codes (max 10) |
| `searchRecencyFilter` | `string` | — | `day`, `week`, `month`, `year` |
| `safeSearch` | `string` | — | `off`, `moderate`, `strict` |
| `startPublishedDate` | `string` | — | ISO 8601 date (only results after this date) |
| `endPublishedDate` | `string` | — | ISO 8601 date (only results before this date) |
| `moderation` | `boolean` | `false` | Enable content moderation |
| `additionalQueries` | `string[]` | — | Extra query variations for deep search |
| `systemPrompt` | `string` | — | Instructions for LLM synthesis |
| `outputSchema` | `object` | — | JSON Schema for structured output |
| `preset` | `string` | — | Pre-configured profile name |
| `provider` | `string` | — | Preferred LLM provider |
| `fallback` | `boolean` | `true` | Enable automatic provider fallback |
| `contents` | `object` | — | Content extraction configuration |

### Contents Object

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `contents.text` | `boolean \| object` | Full page text (`maxCharacters`, `verbosity`, `includeSections`, `excludeSections`) |
| `contents.highlights` | `boolean \| object` | Key excerpts (`maxCharacters`, `query`) |
| `contents.summary` | `boolean \| object` | LLM summary (`query`, `schema`) |
| `contents.subpages` | `integer` | Number of subpages to crawl |
| `contents.subpageTarget` | `string \| string[]` | Keywords for subpage targeting |
| `contents.extras.links` | `integer` | Number of URLs to extract from each page |
| `contents.extras.imageLinks` | `integer` | Number of image URLs to extract |
| `contents.maxAgeHours` | `integer` | Cache freshness (0=always live, -1=cache only) |

### Response Format

```json
{
  "requestId": "a1b2c3d4e5f6",
  "searchType": "auto",
  "providerUsed": "openai",
  "results": [
    {
      "id": "https://example.com/article",
      "title": "Example Article",
      "url": "https://example.com/article",
      "snippet": "Brief description...",
      "publishedDate": "2026-01-15T00:00:00.000Z",
      "author": "Author Name",
      "domain": "example.com",
      "score": 0.95,
      "highlights": ["Most relevant excerpt..."],
      "summary": "LLM-generated summary..."
    }
  ],
  "output": {
    "content": "Synthesized answer...",
    "grounding": [
      {
        "field": "content",
        "citations": [{"url": "https://example.com", "title": "Source"}],
        "confidence": "high"
      }
    ]
  },
  "costDollars": {"total": 0.007},
  "total": 10
}
```

---

## Search Modes

| Mode | Latency | Description | Use Case |
|:-----|:--------|:------------|:---------|
| `instant` | ~200ms | SearXNG direct, no processing | Real-time chat, autocomplete |
| `fast` | ~500ms | SearXNG + snippets | Quick lookups, high-throughput |
| `auto` | ~1s | Hybrid neural + keyword (default) | General purpose |
| `deep-lite` | ~2-10s | Search + light LLM synthesis | Research with summaries |
| `deep` | ~5-30s | Multi-query + crawl + Qdrant + LLM | Comprehensive research |
| `deep-reasoning` | ~10-60s | Agentic loop with iterative reasoning | Complex analysis, reports |

### Mode Selection Guide

```
Need instant results?          → instant
Need fast results?             → fast
General search?                → auto (default)
Need synthesized answers?      → deep-lite
Need comprehensive research?   → deep
Need maximum reasoning depth?  → deep-reasoning
```

---

## LLM Providers

Kubi supports 15 LLM providers with automatic failover.

| Provider | Default Model | Fast Model | Reasoning Model | Context |
|:---------|:--------------|:-----------|:----------------|:--------|
| **OpenAI** | gpt-5 | gpt-5-mini | o3-mini | 1M |
| **Claude** | claude-4-sonnet | claude-4-haiku | claude-4-opus | 1M |
| **DeepSeek** | deepseek-v4-flash | deepseek-v4-flash | deepseek-v4-pro | 1M |
| **Kimi** | kimi-k2 | kimi-k2 | kimi-k2-thinking | 131K |
| **MiMo** | mimo-v2.5 | mimo-v2-flash | mimo-v2.5-pro | 131K |
| **Groq** | llama-3.3-70b | llama-3.1-8b | deepseek-r1-distill | 131K |
| **Together** | Llama-3.3-70B | Llama-3.1-8B | DeepSeek-R1 | 131K |
| **OpenRouter** | claude-4-sonnet | llama-3.1-8b | deepseek-r1 | 1M |
| **Mistral** | mistral-large | mistral-small | magistral-medium | 131K |
| **Perplexity** | sonar-pro | sonar | sonar-reasoning-pro | 131K |
| **Cohere** | command-a | command-r-plus | command-a | 131K |
| **Fireworks** | llama-v3p3-70b | llama-v3p1-8b | deepseek-r1 | 131K |
| **Ollama** | qwen3:8b | qwen3:1.7b | deepseek-r1:7b | 32K |
| **Local** | local-model | local-model | local-model | 32K |

### Configuration

```bash
# In .env
LLM_PROVIDER=openai          # Primary provider
OPENAI_API_KEY=sk-...         # Provider API key
LLM_MODEL=gpt-5              # Override default model
LLM_FAST_MODEL=gpt-5-mini    # Override fast model
LLM_REASONING_MODEL=o3-mini  # Override reasoning model
```

---

## Intelligent Routing

Kubi automatically selects the optimal LLM provider based on query characteristics.

### Routing Logic

| Query Type | Selected Providers | Reasoning |
|:-----------|:-------------------|:----------|
| News / Recent | perplexity, deepseek, openai | Real-time data access |
| Code / Programming | deepseek, openai, groq | Strong coding capabilities |
| Research Papers | perplexity, claude, openai | Academic understanding |
| Creative Writing | claude, openai, kimi | Creative capabilities |
| Analysis / Reasoning | claude, openai, deepseek | Logical reasoning |
| Fast / Instant | groq, deepseek, mimo | Low latency |
| Deep / Research | claude, openai, deepseek | Comprehensive output |

### Health Monitoring

Each provider is tracked for:
- **Availability**: Automatically disabled after 3 consecutive failures
- **Latency**: Rolling average response time
- **Error Rate**: Total requests vs failures
- **Cooldown**: Auto-recovery after 60 seconds

---

## MCP Integration

Kubi includes a Model Context Protocol (MCP) server for integration with AI assistants.

### Available Tools

| Tool | Description |
|:-----|:------------|
| `web_search` | Search the web for any topic |
| `web_fetch` | Read webpage content as clean markdown |
| `web_search_advanced` | Advanced search with filters and structured output |
| `ask` | Get AI-synthesized answers with citations |
| `find_similar` | Find pages similar to a URL |

### Configuration

**Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "kubi": {
      "url": "http://localhost:3001/mcp"
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "kubi": {
      "type": "http",
      "url": "http://localhost:3001/mcp"
    }
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "kubi": {
      "url": "http://localhost:3001/mcp"
    }
  }
}
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|:---------|:--------|:------------|
| `KUBI_API_PORT` | `3000` | API server port |
| `KUBI_API_KEY` | `sk-kubi-change-me-in-production` | API authentication key |
| `LLM_PROVIDER` | `ollama` | Primary LLM provider |
| `LLM_MODEL` | (provider default) | Override default model |
| `LLM_FAST_MODEL` | (provider default) | Override fast model |
| `LLM_REASONING_MODEL` | (provider default) | Override reasoning model |
| `LLM_TEMPERATURE` | `0.3` | Generation temperature |
| `LLM_MAX_TOKENS` | `4096` | Maximum output tokens |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence Transformer model |
| `SEARXNG_URL` | `http://searxng:8080` | SearXNG instance URL |
| `QDRANT_HOST` | `qdrant` | Qdrant host |
| `REDIS_URL` | `redis://redis:6379` | Redis connection URL |
| `CACHE_TTL_SECONDS` | `300` | Cache time-to-live |

See `.env.example` for the complete list.

---

## Deployment

### Docker Compose (Recommended)

```bash
# Standard deployment
docker compose up -d

# With local Ollama for LLM inference
docker compose --profile with-ollama up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Services

| Service | Image | Ports | Health Check |
|:--------|:------|:------|:-------------|
| kubi-api | Custom (Bun) | 3000 | `GET /health` |
| kubi-core | Custom (Rust) | 8080 | `GET /health` |
| kubi-ai | Custom (Python) | 8000 | `GET /ai/health` |
| kubi-mcp | Custom (Bun) | 3001 | `GET /health` |
| Qdrant | `qdrant/qdrant:v1.13.2` | 6333, 6334 | `GET /healthz` |
| SearXNG | `searxng/searxng:latest` | 8888 | `GET /healthz` |
| Redis | `redis:7-alpine` | 6379 | `PING` |
| Ollama | `ollama/ollama:latest` | 11434 | `GET /api/tags` |

### Resource Requirements

| Component | Minimum | Recommended |
|:----------|:--------|:------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4GB | 8GB+ |
| Disk | 10GB | 50GB+ |
| GPU | Not required | Optional (for local LLM) |

---

## Development

### Prerequisites

- Python 3.12+
- Rust 1.83+
- Bun 1.1+
- Docker (for Qdrant, SearXNG, Redis)

### Running Individual Services

```bash
# kubi-ai (Python)
cd kubi-ai
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8000

# kubi-api (Bun + Hono)
cd kubi-api
bun install
bun run dev

# kubi-core (Rust)
cd kubi-core
cargo run

# kubi-mcp (Bun + MCP SDK)
cd kubi-mcp
bun install
bun run dev
```

### Linting and Type Checking

```bash
# Python
cd kubi-ai && python -m py_compile src/main.py

# TypeScript
cd kubi-api && bun run lint && bun run typecheck

# Rust
cd kubi-core && cargo clippy
```

### Project Structure

```
Kubi/
├── kubi-api/           # Public HTTP API (Bun + Hono)
│   ├── src/
│   │   ├── routes/     # 15 route handlers
│   │   ├── middleware/ # Auth, rate limiting
│   │   └── lib/        # Service client
│   ├── Dockerfile
│   └── package.json
├── kubi-core/          # Orchestrator (Rust + Axum)
│   ├── src/
│   │   ├── routes/     # 9 proxy routes
│   │   ├── cache/      # Redis integration
│   │   └── models/     # Data structures
│   ├── Dockerfile
│   └── Cargo.toml
├── kubi-ai/            # Intelligence layer (Python + FastAPI)
│   ├── src/
│   │   ├── search/     # SearXNG, DuckDuckGo
│   │   ├── crawl/      # Playwright + Trafilatura
│   │   ├── embeddings/ # Sentence Transformers
│   │   ├── rank/       # Cross-encoder reranking
│   │   ├── expand/     # Query expansion
│   │   ├── llm/        # Multi-provider LLM service
│   │   ├── similar/    # Qdrant vector search
│   │   └── models/     # Pydantic schemas
│   ├── Dockerfile
│   └── requirements.txt
├── kubi-mcp/           # MCP Server (Bun + MCP SDK)
│   ├── src/
│   │   └── index.ts    # 5 MCP tools
│   ├── Dockerfile
│   └── package.json
├── config/             # Service configurations
├── docker-compose.yml  # Full stack deployment
├── .env.example        # Environment template
└── LICENSE             # Eclipse Public License v2.0
```

---

## License

Kubi is licensed under the [Eclipse Public License v2.0](LICENSE).

```
Copyright (c) 2024-2026 OpceanAI

Licensed under the Eclipse Public License v2.0.
You may obtain a copy of the License at

    https://www.eclipse.org/legal/epl-2.0
```

Commercial use permitted. Modification permitted. Distribution permitted.

---

<p align="center">
  <strong>Kubi</strong> — Search as infrastructure.
</p>

<p align="center">
  Built by <a href="https://github.com/OpceanAI">OpceanAI</a>
</p>
