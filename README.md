# Kubi v1 — Self-Hosted AI Search Engine

Kubi is a self-hosted AI-powered search and retrieval system designed as an open-source alternative to Exa Search. It enables running a full semantic search engine locally or on private infrastructure with full control over models, data, and execution flow.

## Features

- **Hybrid Search**: Combines semantic vector search with keyword-based search
- **Multi-Provider LLM**: 15+ providers (OpenAI, Claude, DeepSeek, Kimi, MiMo, Groq, Mistral, Perplexity, Cohere, etc.)
- **Intelligent Routing**: Auto-selects the best LLM provider based on query type
- **Full Exa API Compatibility**: All Exa Search endpoints implemented
- **Perplexity Features**: Multi-query, language filters, recency filters, presets, deep research
- **MCP Server**: Works with Claude, Cursor, VS Code, and other MCP clients
- **Content Extraction**: Playwright + Trafilatura for clean web content
- **Vector Search**: Qdrant for semantic similarity search
- **Streaming**: SSE streaming for real-time responses
- **Structured Output**: JSON Schema support for structured responses

## Quick Start

```bash
cp .env.example .env
docker compose up -d
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/search` | POST | Hybrid search with nested contents |
| `/api/v1/contents` | POST | Batch URL content extraction |
| `/api/v1/ask` | POST | Search + LLM reasoning with citations |
| `/api/v1/stream` | POST | Streaming version of /ask (SSE) |
| `/api/v1/expand` | POST | Query expansion |
| `/api/v1/crawl` | POST | Crawl and extract URL content |
| `/api/v1/embed` | POST | Generate text embeddings |
| `/api/v1/similar` | POST | Find similar pages by URL |
| `/api/v1/research` | POST | Deep research task |
| `/api/v1/chat/completions` | POST | OpenAI SDK compatible |
| `/api/v1/chat/agent` | POST | Agent API with tools |
| `/api/v1/presets` | GET | List available presets |
| `/api/v1/providers` | GET | Provider health status |
| `/mcp` | POST | MCP Server endpoint |

## Architecture

```
Client → kubi-api (Hono/Bun :3000)
           ↓
       kubi-core (Axum/Rust :8080)
           ↓
       kubi-ai (FastAPI/Python :8000)
           ↓
       ├── SearXNG (metasearch)
       ├── DuckDuckGo (fallback)
       ├── Playwright (dynamic crawl)
       ├── Trafilatura (extraction)
       ├── Sentence Transformers (embeddings)
       ├── Cross-encoder (reranking)
       ├── Qdrant (vector DB)
       └── Ollama/LLM (reasoning)

MCP Clients → kubi-mcp (Bun :3001) → kubi-api
```

## License

Eclipse Public License v2.0
