"""Pydantic models for Kubi AI - Full Exa + Perplexity API compatibility."""

from __future__ import annotations

import uuid
import time
from typing import Any, Optional
from enum import Enum

from pydantic import BaseModel, Field


class SafeSearchLevel(str, Enum):
    OFF = "off"
    MODERATE = "moderate"
    STRICT = "strict"


class RecencyFilter(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class ResearchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TextOptions(BaseModel):
    max_characters: Optional[int] = Field(None, alias="maxCharacters")
    include_html_tags: bool = Field(False, alias="includeHtmlTags")
    verbosity: str = "compact"
    include_sections: Optional[list[str]] = Field(None, alias="includeSections")
    exclude_sections: Optional[list[str]] = Field(None, alias="excludeSections")


class HighlightsOptions(BaseModel):
    max_characters: Optional[int] = Field(None, alias="maxCharacters")
    query: Optional[str] = None


class SummaryOptions(BaseModel):
    query: Optional[str] = None
    schema: Optional[dict[str, Any]] = None


class ExtrasOptions(BaseModel):
    links: int = 0
    image_links: int = Field(0, alias="imageLinks")


class ContentsRequest(BaseModel):
    text: bool | TextOptions = False
    highlights: bool | HighlightsOptions = False
    summary: bool | SummaryOptions = False
    livecrawl: Optional[str] = None
    livecrawl_timeout: int = Field(10000, alias="livecrawlTimeout")
    max_age_hours: Optional[int] = Field(None, alias="maxAgeHours")
    subpages: int = 0
    subpage_target: Optional[str | list[str]] = Field(None, alias="subpageTarget")
    extras: Optional[ExtrasOptions] = None
    context: bool | dict | None = None


class SearchResult(BaseModel):
    id: Optional[str] = None
    title: str = ""
    url: str = ""
    snippet: str = ""
    published_date: Optional[str] = Field(None, alias="publishedDate")
    last_updated: Optional[str] = Field(None, alias="lastUpdated")
    author: Optional[str] = None
    domain: str = ""
    score: float = 0.0
    image: Optional[str] = None
    favicon: Optional[str] = None
    source: str = "web"
    text: Optional[str] = None
    highlights: Optional[list[str]] = None
    highlight_scores: Optional[list[float]] = Field(None, alias="highlightScores")
    summary: Optional[str] = None
    subpages: Optional[list[SearchResult]] = None
    extras: Optional[dict[str, Any]] = None


class ToolFilter(BaseModel):
    search_domain_filter: Optional[list[str]] = Field(None, alias="searchDomainFilter")
    search_recency_filter: Optional[str] = Field(None, alias="searchRecencyFilter")
    search_language_filter: Optional[list[str]] = Field(None, alias="searchLanguageFilter")


class Tool(BaseModel):
    type: str
    filters: Optional[ToolFilter] = None


class ResponseFormat(BaseModel):
    type: str = "text"
    json_schema: Optional[dict[str, Any]] = Field(None, alias="jsonSchema")


class UsageBreakdown(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    tool_calls: int = 0
    search_calls: int = 0
    fetch_calls: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    tool_calls_cost: float = 0.0
    total_cost: float = 0.0


class SearchRequest(BaseModel):
    query: str | list[str] = ""
    type: str = "auto"
    mode: Optional[str] = None
    stream: bool = False
    preset: Optional[str] = None
    num_results: int = Field(10, alias="numResults", ge=1, le=100)
    max_results: Optional[int] = Field(None, alias="maxResults")
    category: Optional[str] = None
    user_location: Optional[str] = Field(None, alias="userLocation")
    country: Optional[str] = None
    include_domains: list[str] = Field(default_factory=list, alias="includeDomains")
    exclude_domains: list[str] = Field(default_factory=list, alias="excludeDomains")
    search_domain_filter: Optional[list[str]] = Field(None, alias="searchDomainFilter")
    search_language_filter: Optional[list[str]] = Field(None, alias="searchLanguageFilter")
    search_recency_filter: Optional[str] = Field(None, alias="searchRecencyFilter")
    safe_search: Optional[str] = Field(None, alias="safeSearch")
    start_published_date: Optional[str] = Field(None, alias="startPublishedDate")
    end_published_date: Optional[str] = Field(None, alias="endPublishedDate")
    start_crawl_date: Optional[str] = Field(None, alias="startCrawlDate")
    end_crawl_date: Optional[str] = Field(None, alias="endCrawlDate")
    moderation: bool = False
    additional_queries: Optional[list[str]] = Field(None, alias="additionalQueries")
    system_prompt: Optional[str] = Field(None, alias="systemPrompt")
    output_schema: Optional[dict[str, Any]] = Field(None, alias="outputSchema")
    contents: Optional[ContentsRequest] = None
    max_tokens_per_page: Optional[int] = Field(None, alias="maxTokensPerPage", ge=256, le=1000000)
    max_tokens: Optional[int] = Field(None, alias="maxTokens", ge=1, le=1000000)
    provider: Optional[str] = None
    fallback: bool = True

    def model_post_init(self, __context: Any) -> None:
        if isinstance(self.query, list) and not self.query:
            self.query = ""
        if isinstance(self.query, str) and not self.query and not self.preset:
            pass


class GroundingCitation(BaseModel):
    url: str
    title: str


class GroundingItem(BaseModel):
    field: str
    citations: list[GroundingCitation] = Field(default_factory=list)
    confidence: str = "medium"


class OutputObject(BaseModel):
    content: str | dict[str, Any]
    grounding: list[GroundingItem] = Field(default_factory=list)


class CostDollars(BaseModel):
    total: float = 0.0
    input_cost: float = Field(0.0, alias="inputCost")
    output_cost: float = Field(0.0, alias="outputCost")
    tool_calls_cost: float = Field(0.0, alias="toolCallsCost")
    breakdown: Optional[dict[str, float]] = None


class SearchResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    search_type: Optional[str] = Field(None, alias="searchType")
    provider_used: Optional[str] = Field(None, alias="providerUsed")
    results: list[SearchResult]
    output: Optional[OutputObject] = None
    cost_dollars: Optional[CostDollars] = Field(None, alias="costDollars")
    usage: Optional[UsageBreakdown] = None
    mode: Optional[str] = None
    query: Optional[str] = None
    queries: Optional[list[str]] = None
    total: int = 0


class ContentsBatchRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=100)
    ids: Optional[list[str]] = None
    text: bool | TextOptions = False
    highlights: bool | HighlightsOptions = False
    summary: bool | SummaryOptions = False
    livecrawl: Optional[str] = None
    livecrawl_timeout: int = Field(10000, alias="livecrawlTimeout")
    max_age_hours: Optional[int] = Field(None, alias="maxAgeHours")
    subpages: int = 0
    subpage_target: Optional[str | list[str]] = Field(None, alias="subpageTarget")
    extras: Optional[ExtrasOptions] = None
    max_tokens_per_page: Optional[int] = Field(None, alias="maxTokensPerPage")


class ContentStatus(BaseModel):
    id: str
    status: str = "success"
    error: Optional[dict[str, Any]] = None


class ContentsBatchResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    results: list[SearchResult]
    statuses: list[ContentStatus] = Field(default_factory=list)
    cost_dollars: Optional[CostDollars] = Field(None, alias="costDollars")


class CrawlRequest(BaseModel):
    url: str
    extract_text: bool = True
    extract_html: bool = False
    max_chars: Optional[int] = None


class CrawlMetadata(BaseModel):
    url: str = ""
    title: str = ""
    description: str = ""
    author: Optional[str] = None
    published_date: Optional[str] = None
    domain: str = ""
    word_count: int = 0
    language: str = ""


class CrawlResponse(BaseModel):
    url: str
    title: str
    text: str
    html: Optional[str] = None
    metadata: CrawlMetadata = Field(default_factory=CrawlMetadata)


class EmbedRequest(BaseModel):
    text: str


class EmbedResponse(BaseModel):
    embedding: list[float]


class ExpandRequest(BaseModel):
    query: str
    num_variations: int = Field(5, alias="numVariations")


class ExpandResponse(BaseModel):
    queries: list[str]


class RankRequest(BaseModel):
    query: str
    results: list[SearchResult]
    top_k: int = 10


class RankResponse(BaseModel):
    results: list[SearchResult]


class AnswerCitation(BaseModel):
    url: str
    title: str
    author: Optional[str] = None
    published_date: Optional[str] = None
    text: Optional[str] = None
    image: Optional[str] = None
    favicon: Optional[str] = None


class AnswerRequest(BaseModel):
    query: str | list[str]
    stream: bool = False
    text: bool = False
    model: Optional[str] = None
    preset: Optional[str] = None
    output_schema: Optional[dict[str, Any]] = Field(None, alias="outputSchema")
    type: str = "auto"
    mode: Optional[str] = None
    num_results: int = Field(10, alias="numResults")
    include_text: bool = Field(False, alias="includeText")
    system_prompt: Optional[str] = Field(None, alias="systemPrompt")
    search_domain_filter: Optional[list[str]] = Field(None, alias="searchDomainFilter")
    search_language_filter: Optional[list[str]] = Field(None, alias="searchLanguageFilter")
    search_recency_filter: Optional[str] = Field(None, alias="searchRecencyFilter")
    safe_search: Optional[str] = Field(None, alias="safeSearch")
    provider: Optional[str] = None
    fallback: bool = True


class AnswerResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"resp-{uuid.uuid4().hex[:12]}")
    answer: str | dict[str, Any]
    citations: list[AnswerCitation] = Field(default_factory=list)
    provider_used: Optional[str] = Field(None, alias="providerUsed")
    cost_dollars: Optional[CostDollars] = Field(None, alias="costDollars")
    usage: Optional[UsageBreakdown] = None


class StreamRequest(BaseModel):
    query: str | list[str]
    type: str = "auto"
    mode: Optional[str] = None
    preset: Optional[str] = None
    num_results: int = Field(10, alias="numResults")
    include_text: bool = Field(False, alias="includeText")
    system_prompt: Optional[str] = Field(None, alias="systemPrompt")
    search_domain_filter: Optional[list[str]] = Field(None, alias="searchDomainFilter")
    search_language_filter: Optional[list[str]] = Field(None, alias="searchLanguageFilter")
    search_recency_filter: Optional[str] = Field(None, alias="searchRecencyFilter")
    provider: Optional[str] = None


class SimilarRequest(BaseModel):
    url: str
    query: Optional[str] = None
    type: str = "fast"
    mode: Optional[str] = None
    num_results: int = Field(10, alias="numResults")
    include_domains: list[str] = Field(default_factory=list, alias="includeDomains")
    exclude_domains: list[str] = Field(default_factory=list, alias="excludeDomains")


class SimilarResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    results: list[SearchResult]
    source_url: str
    total: int


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "kubi"
    messages: list[ChatMessage] = Field(min_length=1)
    stream: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = Field(None, alias="maxTokens")
    search: bool = True
    search_type: Optional[str] = Field(None, alias="searchType")
    search_num_results: Optional[int] = Field(None, alias="searchNumResults")
    provider: Optional[str] = None


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: Optional[str] = Field(None, alias="finishReason")


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str = "kubi"
    choices: list[ChatCompletionChoice]


class ResearchTaskRequest(BaseModel):
    query: str
    num_results: int = Field(20, alias="numResults")
    system_prompt: Optional[str] = Field(None, alias="systemPrompt")
    search_domain_filter: Optional[list[str]] = Field(None, alias="searchDomainFilter")
    search_language_filter: Optional[list[str]] = Field(None, alias="searchLanguageFilter")


class ResearchTaskResponse(BaseModel):
    task_id: str
    status: str = "pending"
    query: str


class ResearchTaskStatus(BaseModel):
    task_id: str
    status: str
    query: str
    created_at: float
    completed_at: Optional[float] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class PresetInfo(BaseModel):
    name: str
    description: str
    search_type: str


class ProviderHealthInfo(BaseModel):
    name: str
    available: bool
    avg_latency_ms: float
    total_requests: int
    total_failures: int
    consecutive_failures: int
    last_error: Optional[str]


class AgentRequest(BaseModel):
    model: Optional[str] = None
    input: str | list[dict[str, Any]]
    instructions: Optional[str] = None
    tools: list[Tool] = Field(default_factory=list)
    tool_choice: str = Field("auto", alias="toolChoice")
    max_tool_calls: Optional[int] = Field(None, alias="maxToolCalls")
    parallel_tool_calls: bool = Field(True, alias="parallelToolCalls")
    reasoning: Optional[dict[str, Any]] = None
    max_output_tokens: Optional[int] = Field(None, alias="maxOutputTokens")
    temperature: float = 1.0
    response_format: Optional[ResponseFormat] = Field(None, alias="responseFormat")
    previous_response_id: Optional[str] = Field(None, alias="previousResponseId")
    stream: bool = False
    provider: Optional[str] = None
    fallback: bool = True


class AgentToolCall(BaseModel):
    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:12]}")
    type: str = "function"
    function: dict[str, Any]


class AgentOutput(BaseModel):
    type: str = "message"
    role: str = "assistant"
    content: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "completed"


class AgentSearchResult(BaseModel):
    queries: list[str] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)
    type: str = "search_results"


class AgentResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"resp-{uuid.uuid4().hex[:12]}")
    object: str = "response"
    model: str = "kubi"
    status: str = "completed"
    output: list[dict[str, Any]] = Field(default_factory=list)
    usage: Optional[UsageBreakdown] = None
    tools: list[Tool] = Field(default_factory=list)
    instructions: Optional[str] = None
    temperature: float = 1.0
    previous_response_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    error: Optional[dict[str, Any]] = None
