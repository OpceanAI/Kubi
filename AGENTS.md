# Kubi v1 - Self-Hosted AI Search Engine

## Build & Run Commands

### Docker Compose (recommended)
```bash
cp .env.example .env
docker compose up -d
docker compose --profile with-ollama up -d
docker compose logs -f
docker compose down
```

### Development
```bash
# kubi-ai
cd kubi-ai && pip install -r requirements.txt && python -m uvicorn src.main:app --reload --port 8000

# kubi-api
cd kubi-api && bun install && bun run dev

# kubi-core
cd kubi-core && cargo run

# kubi-mcp
cd kubi-mcp && bun install && bun run dev
```

## API Endpoints (Exa-Compatible)

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/search` | POST | Hybrid search with nested contents, output schema |
| `/api/v1/contents` | POST | Batch URL content extraction |
| `/api/v1/ask` | POST | Search + LLM reasoning with citations |
| `/api/v1/stream` | POST | Streaming version of /ask (SSE) |
| `/api/v1/expand` | POST | Query expansion for better retrieval |
| `/api/v1/crawl` | POST | Crawl and extract URL content |
| `/api/v1/embed` | POST | Generate text embeddings |
| `/api/v1/similar` | POST | Find similar pages by URL |
| `/api/v1/chat/completions` | POST | OpenAI SDK compatible endpoint |
| `/mcp` | POST | MCP Server endpoint (Model Context Protocol) |

## MCP Server (Model Context Protocol)

Kubi includes an MCP server for use with Claude, Cursor, VS Code, and other MCP clients.

### Available Tools

| Tool | Description |
|---|---|
| `web_search` | Search the web for any topic |
| `web_fetch` | Read webpage content as clean markdown |
| `web_search_advanced` | Advanced search with filters, categories, structured output |
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

## LLM Providers (15 providers)

| Provider | Default Model |
|---|---|
| ollama | qwen3:8b |
| openai | gpt-5 |
| deepseek | deepseek-v4-flash |
| claude | claude-4-sonnet |
| kimi | kimi-k2 |
| mimo | mimo-v2.5 |
| groq | llama-3.3-70b-versatile |
| together | Llama-3.3-70B |
| openrouter | claude-4-sonnet |
| mistral | mistral-large-latest |
| perplexity | sonar-pro |
| cohere | command-a |
| fireworks | llama-v3p3-70b |
| local | local-model |

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
