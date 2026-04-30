"""Kubi AI - Self-hosted AI search engine with intelligent routing."""

import asyncio
import logging
import os
import re
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from sse_starlette.sse import EventSourceResponse

from src.search.searxng_search import SearXNGSearcher
from src.search.ddg_search import DuckDuckGoSearcher
from src.crawl.crawler import WebCrawler
from src.embeddings.embedder import EmbeddingService
from src.rank.reranker import Reranker
from src.expand.expander import QueryExpander
from src.llm.llm_service import LLMService, LLMError
from src.llm.router import IntelligentRouter, get_preset, list_presets, router as intelligent_router
from src.similar.similar_service import SimilarService
from src.models.schemas import (
    SearchRequest, SearchResponse, SearchResult, OutputObject, GroundingItem, GroundingCitation,
    CostDollars, ContentsBatchRequest, ContentsBatchResponse, ContentStatus,
    CrawlRequest, CrawlResponse, EmbedRequest, EmbedResponse,
    ExpandRequest, ExpandResponse, RankRequest, RankResponse,
    AnswerRequest, AnswerResponse, AnswerCitation,
    SimilarRequest, SimilarResponse, StreamRequest,
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice, ChatMessage,
    ContentsRequest, ResearchTaskRequest, ResearchTaskResponse, ResearchTaskStatus,
    PresetInfo, ProviderHealthInfo, UsageBreakdown, Tool, ResponseFormat,
    AgentRequest, AgentResponse, AgentOutput, AgentSearchResult,
)


class Settings(BaseSettings):
    kubi_ai_port: int = 8000
    kubi_ai_host: str = "0.0.0.0"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    llm_provider: str = "ollama"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_fast_model: str = ""
    llm_reasoning_model: str = ""
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096
    searxng_url: str = "http://searxng:8080"
    searxng_engines: str = "google,bing,duckduckgo,wikipedia"
    duckduckgo_enabled: bool = True
    playwright_headless: bool = True
    playwright_timeout: int = 15000
    crawl_max_pages: int = 10
    crawl_max_concurrent: int = 5
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    python_log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
logging.basicConfig(level=getattr(logging, settings.python_log_level))
logger = logging.getLogger("kubi-ai")

searxng_searcher: Optional[SearXNGSearcher] = None
ddg_searcher: Optional[DuckDuckGoSearcher] = None
crawler: Optional[WebCrawler] = None
embedder: Optional[EmbeddingService] = None
reranker: Optional[Reranker] = None
expander: Optional[QueryExpander] = None
llm_service: Optional[LLMService] = None
similar_service: Optional[SimilarService] = None
research_tasks: dict[str, ResearchTaskStatus] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global searxng_searcher, ddg_searcher, crawler, embedder, reranker, expander, llm_service, similar_service

    logger.info("Initializing Kubi AI services...")

    embedder = EmbeddingService(model_name=settings.embedding_model, dimension=settings.embedding_dimension)
    searxng_searcher = SearXNGSearcher(base_url=settings.searxng_url, engines=settings.searxng_engines)

    if settings.duckduckgo_enabled:
        ddg_searcher = DuckDuckGoSearcher()

    crawler = WebCrawler(
        headless=settings.playwright_headless, timeout=settings.playwright_timeout,
        max_pages=settings.crawl_max_pages, max_concurrent=settings.crawl_max_concurrent,
    )
    reranker = Reranker(model_name=settings.rerank_model)
    expander = QueryExpander(
        llm_provider=settings.llm_provider, llm_base_url=settings.llm_base_url or None,
        llm_api_key=settings.llm_api_key or None, llm_model=settings.llm_fast_model or None,
        llm_temperature=settings.llm_temperature,
    )
    llm_service = LLMService(
        provider=settings.llm_provider, base_url=settings.llm_base_url or None,
        api_key=settings.llm_api_key or None, model=settings.llm_model or None,
        fast_model=settings.llm_fast_model or None, reasoning_model=settings.llm_reasoning_model or None,
        temperature=settings.llm_temperature, max_tokens=settings.llm_max_tokens,
    )
    similar_service = SimilarService(embedder=embedder, qdrant_host=settings.qdrant_host, qdrant_port=settings.qdrant_port)

    try:
        await similar_service.init_collections()
    except Exception as e:
        logger.warning(f"Qdrant init failed (will retry): {e}")

    logger.info(f"Kubi AI initialized. Configured providers: {intelligent_router.get_configured_providers()}")
    yield
    logger.info("Shutting down Kubi AI...")
    research_tasks.clear()
    for svc in [crawler, expander, llm_service, similar_service, searxng_searcher, ddg_searcher]:
        if svc and hasattr(svc, 'close'):
            try:
                await svc.close()
            except Exception:
                pass


app = FastAPI(title="Kubi AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


_request_counter = 0


def _request_id() -> str:
    global _request_counter
    _request_counter += 1
    return f"{uuid.uuid4().hex[:8]}-{_request_counter}"


def _cost(search_count: int = 0, llm_tokens: int = 0) -> CostDollars:
    search_cost = search_count * 0.005
    llm_cost = llm_tokens * 0.000002
    return CostDollars(total=search_cost + llm_cost, input_cost=llm_cost, output_cost=0.0, tool_calls_cost=search_cost)


def _normalize_query(query: str | list[str]) -> tuple[str, list[str]]:
    if isinstance(query, list):
        if not query:
            return "", []
        return query[0], query
    if not query:
        return "", []
    return query, [query]


def _apply_recency_filter(query: str, recency: Optional[str]) -> str:
    if not recency:
        return query
    date_map = {"day": "today", "week": "this week", "month": "this month", "year": "this year"}
    suffix = date_map.get(recency, "")
    if suffix:
        return f"{query} {suffix}"
    return query


def _apply_domain_filter(params: dict, include_domains: list, exclude_domains: list, search_domain_filter: Optional[list[str]]):
    if search_domain_filter:
        includes = [d for d in search_domain_filter if not d.startswith("-")]
        excludes = [d.lstrip("-") for d in search_domain_filter if d.startswith("-")]
        if includes:
            params["include_domains"] = includes
        if excludes:
            params["exclude_domains"] = excludes
    else:
        if include_domains:
            params["include_domains"] = include_domains
        if exclude_domains:
            params["exclude_domains"] = exclude_domains


async def _enrich_result(result: SearchResult, contents: ContentsRequest, query: str, max_tokens_per_page: Optional[int] = None) -> SearchResult:
    if not contents:
        return result

    from src.models.schemas import TextOptions, HighlightsOptions, SummaryOptions

    if contents.text:
        try:
            cr = await crawler.crawl(url=result.url)
            text = cr.text or ""
            max_chars = max_tokens_per_page or 4000
            if isinstance(contents.text, TextOptions):
                if contents.text.max_characters:
                    max_chars = contents.text.max_characters
            result.text = text[:max_chars]
        except Exception as e:
            logger.warning(f"Text extraction failed for {result.url}: {e}")

    if contents.highlights and llm_service:
        try:
            text = result.text or result.snippet
            if text:
                q = query
                mc = 4000
                if isinstance(contents.highlights, HighlightsOptions):
                    q = contents.highlights.query or query
                    mc = contents.highlights.max_characters or 4000
                result.highlights = await llm_service.generate_highlights(text, q, mc)
        except Exception as e:
            logger.warning(f"Highlights failed for {result.url}: {e}")

    if contents.summary and llm_service:
        try:
            text = result.text or result.snippet
            if text:
                sq = None
                if isinstance(contents.summary, SummaryOptions):
                    sq = contents.summary.query
                result.summary = await llm_service.generate_summary(text, sq)
        except Exception as e:
            logger.warning(f"Summary failed for {result.url}: {e}")

    if contents.subpages and contents.subpages > 0:
        try:
            result.subpages = await _crawl_subpages(result.url, contents)
        except Exception as e:
            logger.warning(f"Subpage crawl failed for {result.url}: {e}")

    if contents.extras and result.text:
        extras = {}
        if contents.extras.links > 0:
            extras["links"] = re.findall(r'https?://[^\s\)\]\>\"\']+', result.text)[:contents.extras.links]
        if contents.extras.image_links > 0:
            extras["imageLinks"] = []
        result.extras = extras

    return result


async def _crawl_subpages(url: str, contents: ContentsRequest) -> list[SearchResult]:
    try:
        import httpx
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, follow_redirects=True)
            soup = BeautifulSoup(resp.text, "lxml")

            links = []
            for a in soup.find_all("a", href=True):
                full_url = urljoin(url, a["href"])
                title = a.get_text(strip=True)[:200]
                if full_url.startswith("http") and full_url != url and title:
                    links.append((full_url, title))

            targets = contents.subpage_target
            if targets:
                if isinstance(targets, str):
                    targets = [targets]
                links = [(u, t) for u, t in links if any(x.lower() in u.lower() or x.lower() in t.lower() for x in targets)]

            subpages = []
            for link_url, link_title in links[:contents.subpages]:
                try:
                    cr = await crawler.crawl(url=link_url)
                    subpages.append(SearchResult(
                        id=link_url, title=cr.title or link_title, url=link_url,
                        snippet=cr.text[:500] if cr.text else "",
                        text=cr.text if isinstance(contents.text, bool) and contents.text else None,
                    ))
                except Exception:
                    continue
            return subpages
    except Exception as e:
        logger.warning(f"Subpage extraction failed: {e}")
        return []


async def _execute_search(req: SearchRequest) -> SearchResponse:
    request_id = _request_id()
    search_type = req.type or req.mode or "auto"
    start_time = time.time()

    if req.preset:
        preset = get_preset(req.preset)
        if preset:
            search_type = preset.search_type
            if not req.system_prompt and preset.system_prompt:
                req.system_prompt = preset.system_prompt
            if not req.output_schema and preset.output_schema:
                req.output_schema = preset.output_schema
            if preset.category and not req.category:
                req.category = preset.category

    primary_query, all_queries = _normalize_query(req.query)
    if req.additional_queries:
        all_queries.extend(req.additional_queries)

    primary_query = _apply_recency_filter(primary_query, req.search_recency_filter)

    selected_provider, fallback_chain = intelligent_router.select_provider(
        query=primary_query, mode=search_type,
        preferred_provider=req.provider, fallback_chain=req.fallback,
    )

    all_results = []

    if searxng_searcher:
        for q in all_queries[:5]:
            try:
                sxng_params = {"query": q, "num_results": req.num_results}
                _apply_domain_filter(sxng_params, req.include_domains, req.exclude_domains, req.search_domain_filter)
                if req.category:
                    sxng_params["categories"] = req.category
                if req.country or req.user_location:
                    sxng_params["categories"] = (sxng_params.get("categories", "") + f" region-{req.country or req.user_location}").strip()
                sxng_results = await searxng_searcher.search(**sxng_params)
                all_results.extend(sxng_results)
            except Exception as e:
                logger.warning(f"SearXNG search failed for '{q}': {e}")

    if ddg_searcher and not all_results:
        for q in all_queries[:3]:
            try:
                ddg_results = await ddg_searcher.search(query=q, num_results=req.num_results)
                all_results.extend(ddg_results)
            except Exception as e:
                logger.warning(f"DDG search failed for '{q}': {e}")

    seen = set()
    unique = []
    for r in all_results:
        if r.url not in seen:
            seen.add(r.url)
            if not r.id:
                r.id = r.url
            if req.safe_search and req.safe_search == "strict":
                r.snippet = r.snippet[:500]
            unique.append(r)
    unique = unique[:req.num_results]

    if req.contents:
        unique = [await _enrich_result(r, req.contents, primary_query, req.max_tokens_per_page) for r in unique]

    if similar_service and unique:
        try:
            texts = [f"{r.title} {r.snippet}" for r in unique]
            embeddings = await embedder.embed_batch(texts)
            await similar_service.store_results(unique, embeddings)
        except Exception as e:
            logger.warning(f"Failed to store results in Qdrant: {e}")

    output_obj = None
    if req.output_schema and llm_service and unique:
        try:
            contexts = [f"Source: {r.title}\nURL: {r.url}\nContent: {r.text or r.snippet}" for r in unique[:5]]
            synthesized = await llm_service.synthesize(
                query=primary_query, contexts=contexts,
                system_prompt=req.system_prompt, output_schema=req.output_schema,
            )
            output_obj = OutputObject(
                content=synthesized,
                grounding=[GroundingItem(field="content", citations=[
                    GroundingCitation(url=r.url, title=r.title) for r in unique[:5]
                ], confidence="high")],
            )
        except Exception as e:
            logger.warning(f"Output synthesis failed: {e}")

    return SearchResponse(
        request_id=request_id, search_type=search_type, provider_used=selected_provider,
        results=unique, output=output_obj, cost_dollars=_cost(), mode=search_type,
        query=primary_query, queries=all_queries if len(all_queries) > 1 else None,
        total=len(unique),
    )


@app.get("/ai/health")
async def health():
    return {
        "status": "ok", "service": "kubi-ai", "version": "1.0.0",
        "llm": llm_service.get_config() if llm_service else None,
        "providers": intelligent_router.get_configured_providers(),
        "provider_health": intelligent_router.get_health_status(),
        "components": {
            "searxng": searxng_searcher is not None, "ddg": ddg_searcher is not None,
            "crawler": crawler is not None, "embedder": embedder is not None,
            "reranker": reranker is not None, "expander": expander is not None,
            "llm": llm_service is not None, "similar": similar_service is not None,
        },
    }


@app.get("/ai/models")
async def list_models():
    from src.llm.providers import list_providers
    return {
        "current": llm_service.get_config() if llm_service else None,
        "providers": list_providers(),
        "configured": intelligent_router.get_configured_providers(),
        "health": intelligent_router.get_health_status(),
    }


@app.get("/ai/presets")
async def get_presets():
    return {"presets": list_presets()}


@app.post("/ai/search")
async def search(req: SearchRequest):
    return await _execute_search(req)


@app.post("/ai/contents")
async def contents(req: ContentsBatchRequest):
    request_id = _request_id()
    urls = req.ids or req.urls
    results: list[SearchResult] = []
    statuses: list[ContentStatus] = []
    semaphore = asyncio.Semaphore(5)

    async def _fetch_one(url: str):
        async with semaphore:
            try:
                cr = await crawler.crawl(url=url)
                text = cr.text or ""
                if req.max_tokens_per_page:
                    text = text[:req.max_tokens_per_page]

                result = SearchResult(
                    id=url, title=cr.title, url=url, snippet="",
                    text=text if req.text else None,
                    published_date=cr.metadata.published_date if cr.metadata else None,
                    author=cr.metadata.author if cr.metadata else None,
                    domain=cr.metadata.domain if cr.metadata else "",
                )

                if req.highlights and llm_service and text:
                    try:
                        q = ""
                        mc = 4000
                        if isinstance(req.highlights, dict):
                            q = req.highlights.get("query", "")
                            mc = req.highlights.get("maxCharacters") or req.highlights.get("max_characters") or 4000
                        result.highlights = await llm_service.generate_highlights(text, q or "", mc)
                    except Exception:
                        pass

                if req.summary and llm_service and text:
                    try:
                        sq = req.summary.get("query") if isinstance(req.summary, dict) else None
                        result.summary = await llm_service.generate_summary(text, sq)
                    except Exception:
                        pass

                if req.extras and text:
                    extras = {}
                    if req.extras.links > 0:
                        extras["links"] = re.findall(r'https?://[^\s\)\]\>\"\']+', text)[:req.extras.links]
                    if req.extras.image_links > 0:
                        extras["imageLinks"] = []
                    result.extras = extras

                results.append(result)
                statuses.append(ContentStatus(id=url, status="success"))
            except Exception as e:
                logger.error(f"Contents fetch failed for {url}: {e}")
                results.append(SearchResult(id=url, url=url, title="Error", snippet=str(e)))
                statuses.append(ContentStatus(id=url, status="error", error={"tag": "CRAWL_UNKNOWN_ERROR", "httpStatusCode": None}))

    await asyncio.gather(*[_fetch_one(u) for u in urls])
    return ContentsBatchResponse(request_id=request_id, results=results, statuses=statuses, cost_dollars=_cost())


@app.post("/ai/crawl")
async def crawl_endpoint(req: CrawlRequest):
    try:
        result = await crawler.crawl(url=req.url)
        return CrawlResponse(url=req.url, title=result.title, text=result.text, html=result.html, metadata=result.metadata)
    except Exception as e:
        logger.error(f"Crawl failed for {req.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")


@app.post("/ai/embed")
async def embed_endpoint(req: EmbedRequest):
    try:
        return EmbedResponse(embedding=await embedder.embed(req.text))
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")


@app.post("/ai/expand")
async def expand_endpoint(req: ExpandRequest):
    try:
        return ExpandResponse(queries=await expander.expand(query=req.query, num_variations=req.num_variations))
    except Exception as e:
        logger.error(f"Query expansion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Expansion failed: {str(e)}")


@app.post("/ai/rank")
async def rank_endpoint(req: RankRequest):
    try:
        return RankResponse(results=await reranker.rerank(query=req.query, results=req.results, top_k=req.top_k))
    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")


@app.post("/ai/answer")
async def answer(req: AnswerRequest):
    try:
        primary_query, all_queries = _normalize_query(req.query)
        search_type = req.type or req.mode or "auto"

        selected_provider, fallback_chain = intelligent_router.select_provider(
            query=primary_query, mode=search_type,
            preferred_provider=req.provider, fallback_chain=req.fallback,
        )

        search_req = SearchRequest(
            query=req.query, type=search_type, numResults=req.num_results,
            searchDomainFilter=req.search_domain_filter,
            searchLanguageFilter=req.search_language_filter,
            searchRecencyFilter=req.search_recency_filter,
            safeSearch=req.safe_search, preset=req.preset,
        )
        search_resp = await _execute_search(search_req)

        contexts, sources = [], []
        for r in search_resp.results[:5]:
            if req.include_text or req.text:
                try:
                    cr = await crawl_endpoint(CrawlRequest(url=r.url))
                    text = cr.text[:3000] if cr.text else r.snippet
                    contexts.append(f"Source: {r.title}\nURL: {r.url}\nContent: {text}")
                except Exception:
                    contexts.append(f"Source: {r.title}\nURL: {r.url}\nContent: {r.snippet}")
            else:
                contexts.append(f"Source: {r.title}\nURL: {r.url}\nContent: {r.snippet}")
            sources.append(AnswerCitation(url=r.url, title=r.title, author=r.author, published_date=r.published_date, text=r.text, image=r.image, favicon=r.favicon))

        answer_text = None
        for provider in fallback_chain:
            try:
                provider_config = __import__('src.llm.providers', fromlist=['get_provider']).get_provider(provider)
                if not provider_config:
                    continue
                temp_llm = LLMService(
                    provider=provider, base_url=provider_config.base_url,
                    api_key=os.environ.get(provider_config.api_key_env, ""),
                    model=provider_config.default_model,
                    reasoning_model=provider_config.default_reasoning_model,
                    temperature=settings.llm_temperature, max_tokens=settings.llm_max_tokens,
                )
                answer_text = await temp_llm.synthesize(
                    query=primary_query, contexts=contexts,
                    system_prompt=req.system_prompt, output_schema=req.output_schema,
                )
                intelligent_router.record_success(provider, 0)
                selected_provider = provider
                await temp_llm.close()
                break
            except Exception as e:
                intelligent_router.record_failure(provider, str(e))
                logger.warning(f"Provider {provider} failed for answer: {e}")
                continue

        if answer_text is None:
            answer_text = await llm_service.synthesize(
                query=primary_query, contexts=contexts,
                system_prompt=req.system_prompt, output_schema=req.output_schema,
            )

        return AnswerResponse(
            answer=answer_text, citations=sources,
            provider_used=selected_provider, cost_dollars=_cost(),
        )
    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Answer failed: {str(e)}")


@app.post("/ai/stream")
async def stream(req: StreamRequest):
    try:
        primary_query, _ = _normalize_query(req.query)
        search_type = req.type or req.mode or "auto"

        selected_provider, _ = intelligent_router.select_provider(
            query=primary_query, mode=search_type,
            preferred_provider=req.provider,
        )

        search_req = SearchRequest(
            query=req.query, type=search_type, numResults=req.num_results,
            searchDomainFilter=req.search_domain_filter,
            searchLanguageFilter=req.search_language_filter,
            searchRecencyFilter=req.search_recency_filter,
        )
        search_resp = await _execute_search(search_req)

        contexts = [f"Source: {r.title}\nURL: {r.url}\nContent: {r.snippet}" for r in search_resp.results[:5]]
        sources = [{"url": r.url, "title": r.title} for r in search_resp.results[:5]]

        async def event_generator():
            yield {"event": "sources", "data": _json({"sources": sources, "provider": selected_provider})}
            async for token in llm_service.stream_synthesize(query=primary_query, contexts=contexts, system_prompt=req.system_prompt):
                yield {"event": "token", "data": _json({"token": token})}
            yield {"event": "done", "data": _json({"done": True})}

        return EventSourceResponse(event_generator())
    except Exception as e:
        logger.error(f"Stream failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stream failed: {str(e)}")


@app.post("/ai/similar")
async def similar_endpoint(req: SimilarRequest):
    try:
        result = await similar_service.find_similar(
            url=req.url, query=req.query,
            num_results=req.num_results, include_domains=req.include_domains, exclude_domains=req.exclude_domains,
        )
        return SimilarResponse(request_id=_request_id(), results=result.results, source_url=req.url, total=result.total)
    except Exception as e:
        logger.error(f"Similar search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Similar failed: {str(e)}")


@app.post("/ai/research", response_model=ResearchTaskResponse)
async def start_research(req: ResearchTaskRequest):
    task_id = f"research-{uuid.uuid4().hex[:12]}"
    task = ResearchTaskStatus(task_id=task_id, status="pending", query=req.query, created_at=time.time())
    research_tasks[task_id] = task

    asyncio.create_task(_run_research(task_id, req))

    return ResearchTaskResponse(task_id=task_id, status="pending", query=req.query)


@app.get("/ai/research/{task_id}")
async def get_research_status(task_id: str):
    task = research_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Research task not found")
    return task


async def _run_research(task_id: str, req: ResearchTaskRequest):
    task = research_tasks[task_id]
    task.status = "running"

    try:
        search_req = SearchRequest(
            query=req.query, type="deep-reasoning", numResults=req.num_results,
            searchDomainFilter=req.search_domain_filter,
            searchLanguageFilter=req.search_language_filter,
            contents=ContentsRequest(
                text=TextOptions(max_characters=15000),
                highlights=HighlightsOptions(max_characters=4000),
                summary=SummaryOptions(),
                subpages=2,
            ),
            systemPrompt=req.system_prompt or "You are a deep research analyst. Conduct exhaustive research and provide a comprehensive report with sections, citations, and analysis.",
        )
        search_resp = await _execute_search(search_req)

        contexts = [f"Source: {r.title}\nURL: {r.url}\nContent: {r.text or r.snippet}" for r in search_resp.results[:10]]

        report = await llm_service.synthesize(
            query=req.query, contexts=contexts,
            system_prompt=req.system_prompt or "Synthesize all sources into a comprehensive research report with clear sections, analysis, and citations.",
        )

        task.status = "completed"
        task.completed_at = time.time()
        task.result = {
            "report": report,
            "sources": [{"title": r.title, "url": r.url} for r in search_resp.results],
            "total_sources": len(search_resp.results),
        }
    except Exception as e:
        task.status = "failed"
        task.completed_at = time.time()
        task.error = str(e)
        logger.error(f"Research task {task_id} failed: {e}")


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="Messages array cannot be empty")

    user_msg = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
    system_msg = next((m.content for m in req.messages if m.role == "system"), "")

    if not user_msg:
        raise HTTPException(status_code=400, detail="At least one user message is required")

    selected_provider, _ = intelligent_router.select_provider(
        query=user_msg, mode="auto", preferred_provider=req.provider,
    )

    enhanced_user = user_msg
    if req.search and user_msg:
        search_resp = await _execute_search(SearchRequest(query=user_msg, type=req.search_type or "auto", numResults=req.search_num_results or 5))
        contexts = [f"Source: {r.title}\nURL: {r.url}\nContent: {r.snippet}" for r in search_resp.results[:3]]
        ctx_block = "\n\n---\n\n".join(contexts)
        enhanced_user = f"Based on the following sources, answer the question.\n\nSources:\n{ctx_block}\n\nQuestion: {user_msg}"

    actual_model = req.model if req.model != "kubi" else (llm_service.model if llm_service else "kubi")
    answer_text = await llm_service._chat(
        system=system_msg or "You are a helpful assistant.", user=enhanced_user,
        model=req.model if req.model != "kubi" else None,
        temperature=req.temperature, max_tokens=req.max_tokens or 2048,
    )

    return ChatCompletionResponse(
        model=actual_model,
        choices=[ChatCompletionChoice(index=0, message=ChatMessage(role="assistant", content=answer_text), finish_reason="stop")],
    )


@app.get("/ai/providers")
async def list_provider_health():
    return {
        "configured": intelligent_router.get_configured_providers(),
        "health": intelligent_router.get_health_status(),
    }


@app.post("/v1/agent")
async def agent_endpoint(req: AgentRequest):
    start_time = time.time()
    input_text = ""
    if isinstance(req.input, str):
        input_text = req.input
    elif isinstance(req.input, list):
        for item in req.input:
            if isinstance(item, dict) and item.get("type") == "message":
                content = item.get("content", "")
                if isinstance(content, str):
                    input_text += content + "\n"
                elif isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            input_text += c.get("text", "") + "\n"

    has_search_tool = any(t.type == "web_search" for t in req.tools)
    has_fetch_tool = any(t.type == "fetch_url" for t in req.tools)
    selected_provider, fallback_chain = intelligent_router.select_provider(
        query=input_text.strip(), mode="auto", preferred_provider=req.provider,
    )

    search_results_data = []
    fetch_results_data = []
    tool_calls_count = 0

    if has_search_tool:
        search_tool = next((t for t in req.tools if t.type == "web_search"), None)
        search_req = SearchRequest(
            query=input_text.strip(), type="auto", numResults=10,
        )
        if search_tool and search_tool.filters:
            if search_tool.filters.search_domain_filter:
                search_req.search_domain_filter = search_tool.filters.search_domain_filter
            if search_tool.filters.search_recency_filter:
                search_req.search_recency_filter = search_tool.filters.search_recency_filter
            if search_tool.filters.search_language_filter:
                search_req.search_language_filter = search_tool.filters.search_language_filter

        search_resp = await _execute_search(search_req)
        tool_calls_count += 1

        for r in search_resp.results:
            search_results_data.append({
                "id": len(search_results_data) + 1,
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "date": r.published_date,
                "last_updated": r.last_updated,
                "source": "web",
            })

    if has_fetch_tool and search_results_data:
        urls_to_fetch = [r["url"] for r in search_results_data[:3]]
        for url in urls_to_fetch:
            try:
                cr = await crawler.crawl(url=url)
                fetch_results_data.append({
                    "title": cr.title,
                    "url": url,
                    "snippet": cr.text[:2000] if cr.text else "",
                })
                tool_calls_count += 1
            except Exception:
                pass

    contexts = []
    if search_results_data:
        for r in search_results_data[:5]:
            fetch_match = next((f for f in fetch_results_data if f["url"] == r["url"]), None)
            content = fetch_match["snippet"] if fetch_match else r.get("snippet", "")
            contexts.append(f"Source: {r['title']}\nURL: {r['url']}\nContent: {content}")

    system_instructions = req.instructions or "You are a helpful research assistant. Answer based on the provided sources. Cite all sources using [Source N] notation."
    enhanced_input = input_text.strip()

    if contexts:
        ctx_block = "\n\n---\n\n".join(contexts)
        enhanced_input = f"Based on the following sources, answer the question.\n\nSources:\n{ctx_block}\n\nQuestion: {input_text.strip()}"

    answer_text = None
    for provider in fallback_chain:
        try:
            provider_config = __import__('src.llm.providers', fromlist=['get_provider']).get_provider(provider)
            if not provider_config:
                continue
            temp_llm = LLMService(
                provider=provider, base_url=provider_config.base_url,
                api_key=os.environ.get(provider_config.api_key_env, ""),
                model=req.model or provider_config.default_model,
                reasoning_model=provider_config.default_reasoning_model,
                temperature=req.temperature, max_tokens=req.max_output_tokens or settings.llm_max_tokens,
            )
            answer_text = await temp_llm._chat(
                system=system_instructions, user=enhanced_input,
                model=req.model if req.model else provider_config.default_model,
                temperature=req.temperature, max_tokens=req.max_output_tokens or settings.llm_max_tokens,
            )
            intelligent_router.record_success(provider, (time.time() - start_time) * 1000)
            selected_provider = provider
            await temp_llm.close()
            break
        except Exception as e:
            intelligent_router.record_failure(provider, str(e))
            continue

    if answer_text is None:
        answer_text = await llm_service._chat(
            system=system_instructions, user=enhanced_input,
            temperature=req.temperature, max_tokens=req.max_output_tokens or settings.llm_max_tokens,
        )

    elapsed = time.time() - start_time
    output = []

    if search_results_data:
        output.append({
            "type": "search_results",
            "queries": [input_text.strip()],
            "results": search_results_data,
        })

    if fetch_results_data:
        output.append({
            "type": "fetch_url_results",
            "contents": fetch_results_data,
        })

    output.append({
        "type": "message",
        "role": "assistant",
        "content": [{"type": "output_text", "text": answer_text or ""}],
        "status": "completed",
    })

    usage = UsageBreakdown(
        input_tokens=len(enhanced_input.split()) * 2,
        output_tokens=len((answer_text or "").split()) * 2,
        total_tokens=(len(enhanced_input.split()) + len((answer_text or "").split())) * 2,
        tool_calls=tool_calls_count,
        search_calls=1 if has_search_tool else 0,
        fetch_calls=len(fetch_results_data),
    )

    return AgentResponse(
        model=req.model or selected_provider,
        status="completed",
        output=output,
        usage=usage,
        tools=req.tools,
        instructions=req.instructions,
        temperature=req.temperature,
        previous_response_id=req.previous_response_id,
        created_at=start_time,
        completed_at=time.time(),
    )


@app.post("/v1/responses")
async def responses_endpoint(req: AgentRequest):
    return await agent_endpoint(req)


def _json(obj: dict) -> str:
    import orjson
    return orjson.dumps(obj).decode()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=settings.kubi_ai_host, port=settings.kubi_ai_port, log_level=settings.python_log_level.lower())
