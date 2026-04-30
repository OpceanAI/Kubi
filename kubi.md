Kubi v1 — Self-Hosted AI Search Engine

Kubi is a self-hosted AI-powered search and retrieval system designed as an alternative to closed search APIs such as Exa. It enables running a full semantic search engine locally or on private infrastructure with full control over models, data, and execution flow.


---

Vision

Kubi is a search infrastructure for AI systems.

It enables:

Semantic web search

Hybrid retrieval (vector + keyword)

AI reasoning over retrieved results

Fully self-hosted deployment

No dependency on external search APIs



---

Core Principles

User owns infrastructure and data

No mandatory cloud dependency

Modular architecture by design

Replaceable components (models, search, storage)

Scalable from local machine to distributed systems



---

System Architecture

Kubi v1 uses a multi-language distributed architecture:

Frontend/API Layer: Bun + TypeScript Core Engine: Rust AI/Search Layer: Python Vector Database: Qdrant Search Backends: SearXNG, DuckDuckGo, custom crawlers


---

Core Components

Rust Core (kubi-core)

High-performance orchestration layer.

Responsibilities:

API request routing

Search mode selection (fast, deep, research)

Coordination between Python AI services

Result aggregation and ranking

Streaming response handling


Technologies:

Axum

Tokio

Serde



---

API Layer (kubi-api)

External interface for clients and applications.

Responsibilities:

Public HTTP API

Streaming responses (SSE/WebSockets)

Authentication and API keys

Request validation


Framework:

Bun runtime

Hono (TypeScript)



---

AI and Search Layer (kubi-ai)

Intelligence and retrieval system.

Responsibilities:

Query expansion

Web search orchestration

Crawling and extraction

Embedding generation

Ranking and filtering

LLM orchestration


Components:

SearXNG (metasearch)

Playwright (dynamic crawling)

Trafilatura (content extraction)

Sentence Transformers (embeddings)



---

Vector Database

Semantic storage layer.

Qdrant used as primary vector database

Stores embeddings for:

Web pages

Crawled documents

Cached search results




---

LLM Layer (pluggable)

Supports multiple models depending on configuration.

Search and execution models:

Qwen 2B (fast routing and planning)

Qwen 14B (advanced planning and tool usage)


Reasoning models:

LiquidAI LFM2.5 (light reasoning)

Qwen 9B (balanced reasoning)

Phi-4 Reasoning Plus (structured logic)

DeepSeek R1 32B (deep reasoning and synthesis)



---

Search Modes

Fast Mode

Low latency search

Uses SearXNG only

Minimal processing


Deep Mode

Hybrid retrieval (vector + web)

Query expansion enabled

Optional crawling


Research Mode

Multi-step agentic search loop

Iterative query refinement

Multi-source synthesis



---

Search Pipeline

User Query → Rust Core (routing) → Python AI Layer

Query expansion via LLM

Web search (SearXNG / DuckDuckGo)

Crawlers (if required)

Vector search (Qdrant) → Ranking and merging layer → LLM reasoning layer → Streaming response via API



---

API Specification

Base URL

/api/v1


---

Endpoints

POST /search

Performs hybrid search across web and vector database.

Request: { "query": "string", "mode": "fast | deep | research", "limit": 10 }

Response: { "results": [ { "title": "string", "url": "string", "snippet": "string", "score": 0.0 } ], "mode": "string" }


---

POST /ask

Performs search + LLM reasoning over results.

Request: { "query": "string", "mode": "fast | deep | research", "model": "string" }

Response: { "answer": "string", "sources": [ { "title": "string", "url": "string" } ] }


---

POST /stream

Streaming version of /ask.

Response is streamed tokens using SSE.


---

POST /expand

Generates expanded queries for better retrieval.

Request: { "query": "string" }

Response: { "queries": ["string"] }


---

POST /crawl

Crawls and extracts content from a URL.

Request: { "url": "string" }

Response: { "content": "string", "metadata": {} }


---

POST /embed

Generates embeddings for a given text.

Request: { "text": "string" }

Response: { "embedding": [0.0] }


---

Key Features

Hybrid Search

Combines semantic vector search with keyword-based search.

Query Expansion

Automatically generates multiple query variations to improve recall.

LLM-Ready Output

Cleans and structures web data into LLM-friendly context.

Agentic Search Loop

Supports iterative search refinement for complex queries.

Streaming Responses

Real-time token streaming for low-latency UX.

Modular Design

All components can be replaced independently.


---

Deployment

Docker Compose (recommended)

Includes:

Rust core service

Python AI service

Qdrant

SearXNG

Redis (optional caching)


Bare Metal Deployment

Supported on Linux VPS systems. GPU optional depending on LLM configuration.


---

License

Apache 2.0

Permissions:

Commercial use allowed

Modification allowed

Distribution allowed


Conditions:

License and attribution must be included



---

Target Users

AI developers

RAG system builders

Self-hosting enthusiasts

Research teams

Companies avoiding external APIs



---

Design Goal

Kubi aims to provide a fully self-hosted alternative to AI search APIs, offering full control over retrieval, reasoning, and infrastructure.


---

Future Extensions

Distributed search clusters

Plugin ecosystem

Multi-node indexing system

Hybrid cloud/self-host mode

Continuous web indexing pipeline



---

Summary

Kubi v1 is:

Self-hosted AI search engine

Hybrid retrieval system

Multi-model reasoning pipeline

Modular distributed architecture

Designed for full control and extensibility


If Exa is search as a service, Kubi is search as infrastructure.
