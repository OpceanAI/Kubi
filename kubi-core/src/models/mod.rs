use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchRequest {
    pub query: serde_json::Value,
    #[serde(default = "default_mode")]
    pub r#type: String,
    #[serde(default)]
    pub mode: Option<String>,
    #[serde(default)]
    pub stream: bool,
    #[serde(default)]
    pub preset: Option<String>,
    #[serde(default = "default_num_results")]
    pub num_results: u32,
    #[serde(default)]
    pub max_results: Option<u32>,
    #[serde(default)]
    pub category: Option<String>,
    #[serde(default)]
    pub user_location: Option<String>,
    #[serde(default)]
    pub country: Option<String>,
    #[serde(default)]
    pub include_domains: Vec<String>,
    #[serde(default)]
    pub exclude_domains: Vec<String>,
    #[serde(default)]
    pub search_domain_filter: Option<Vec<String>>,
    #[serde(default)]
    pub search_language_filter: Option<Vec<String>>,
    #[serde(default)]
    pub search_recency_filter: Option<String>,
    #[serde(default)]
    pub safe_search: Option<String>,
    #[serde(default)]
    pub start_published_date: Option<String>,
    #[serde(default)]
    pub end_published_date: Option<String>,
    #[serde(default)]
    pub start_crawl_date: Option<String>,
    #[serde(default)]
    pub end_crawl_date: Option<String>,
    #[serde(default)]
    pub moderation: bool,
    #[serde(default)]
    pub additional_queries: Option<Vec<String>>,
    #[serde(default)]
    pub system_prompt: Option<String>,
    #[serde(default)]
    pub output_schema: Option<serde_json::Value>,
    #[serde(default)]
    pub contents: Option<serde_json::Value>,
    #[serde(default)]
    pub max_tokens_per_page: Option<u32>,
    #[serde(default)]
    pub max_tokens: Option<u32>,
    #[serde(default)]
    pub provider: Option<String>,
    #[serde(default = "default_true")]
    pub fallback: bool,
}

fn default_mode() -> String { "auto".to_string() }
fn default_num_results() -> u32 { 10 }
fn default_true() -> bool { true }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub title: String,
    #[serde(default)]
    pub url: String,
    #[serde(default)]
    pub snippet: String,
    #[serde(default)]
    pub published_date: Option<String>,
    #[serde(default)]
    pub last_updated: Option<String>,
    #[serde(default)]
    pub author: Option<String>,
    #[serde(default)]
    pub domain: String,
    #[serde(default)]
    pub score: f64,
    #[serde(default)]
    pub image: Option<String>,
    #[serde(default)]
    pub favicon: Option<String>,
    #[serde(default)]
    pub source: String,
    #[serde(default)]
    pub text: Option<String>,
    #[serde(default)]
    pub highlights: Option<Vec<String>>,
    #[serde(default)]
    pub highlight_scores: Option<Vec<f64>>,
    #[serde(default)]
    pub summary: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResponse {
    #[serde(default)]
    pub request_id: String,
    #[serde(default)]
    pub search_type: Option<String>,
    #[serde(default)]
    pub provider_used: Option<String>,
    #[serde(default)]
    pub results: Vec<SearchResult>,
    #[serde(default)]
    pub output: Option<serde_json::Value>,
    #[serde(default)]
    pub cost_dollars: Option<serde_json::Value>,
    #[serde(default)]
    pub usage: Option<serde_json::Value>,
    #[serde(default)]
    pub mode: Option<String>,
    #[serde(default)]
    pub query: Option<String>,
    #[serde(default)]
    pub queries: Option<Vec<String>>,
    #[serde(default)]
    pub total: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnswerRequest {
    pub query: serde_json::Value,
    #[serde(default)]
    pub stream: bool,
    #[serde(default)]
    pub text: bool,
    #[serde(default)]
    pub model: Option<String>,
    #[serde(default)]
    pub preset: Option<String>,
    #[serde(default)]
    pub output_schema: Option<serde_json::Value>,
    #[serde(default = "default_mode")]
    pub r#type: String,
    #[serde(default)]
    pub mode: Option<String>,
    #[serde(default = "default_num_results")]
    pub num_results: u32,
    #[serde(default)]
    pub include_text: bool,
    #[serde(default)]
    pub system_prompt: Option<String>,
    #[serde(default)]
    pub search_domain_filter: Option<Vec<String>>,
    #[serde(default)]
    pub search_language_filter: Option<Vec<String>>,
    #[serde(default)]
    pub search_recency_filter: Option<String>,
    #[serde(default)]
    pub safe_search: Option<String>,
    #[serde(default)]
    pub provider: Option<String>,
    #[serde(default = "default_true")]
    pub fallback: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnswerResponse {
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub answer: serde_json::Value,
    #[serde(default)]
    pub citations: Vec<AnswerCitation>,
    #[serde(default)]
    pub provider_used: Option<String>,
    #[serde(default)]
    pub cost_dollars: Option<serde_json::Value>,
    #[serde(default)]
    pub usage: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnswerCitation {
    pub url: String,
    pub title: String,
    #[serde(default)]
    pub author: Option<String>,
    #[serde(default)]
    pub published_date: Option<String>,
    #[serde(default)]
    pub text: Option<String>,
    #[serde(default)]
    pub image: Option<String>,
    #[serde(default)]
    pub favicon: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StreamRequest {
    pub query: serde_json::Value,
    #[serde(default = "default_mode")]
    pub r#type: String,
    #[serde(default)]
    pub mode: Option<String>,
    #[serde(default)]
    pub preset: Option<String>,
    #[serde(default = "default_num_results")]
    pub num_results: u32,
    #[serde(default)]
    pub include_text: bool,
    #[serde(default)]
    pub system_prompt: Option<String>,
    #[serde(default)]
    pub search_domain_filter: Option<Vec<String>>,
    #[serde(default)]
    pub search_language_filter: Option<Vec<String>>,
    #[serde(default)]
    pub search_recency_filter: Option<String>,
    #[serde(default)]
    pub provider: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpandRequest {
    pub query: String,
    #[serde(default = "default_num_variations")]
    pub num_variations: u32,
}

fn default_num_variations() -> u32 { 5 }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpandResponse {
    pub queries: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrawlRequest {
    pub url: String,
    #[serde(default = "default_true")]
    pub extract_text: bool,
    #[serde(default)]
    pub extract_html: bool,
    #[serde(default)]
    pub max_chars: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimilarRequest {
    pub url: String,
    #[serde(default)]
    pub query: Option<String>,
    #[serde(default = "default_mode")]
    pub r#type: String,
    #[serde(default)]
    pub mode: Option<String>,
    #[serde(default = "default_num_results")]
    pub num_results: u32,
    #[serde(default)]
    pub include_domains: Vec<String>,
    #[serde(default)]
    pub exclude_domains: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RankRequest {
    pub query: String,
    pub results: Vec<SearchResult>,
    #[serde(default = "default_num_results")]
    pub top_k: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbedRequest {
    pub text: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentsRequest {
    pub urls: Vec<String>,
    #[serde(default)]
    pub ids: Option<Vec<String>>,
    #[serde(default)]
    pub text: Option<serde_json::Value>,
    #[serde(default)]
    pub highlights: Option<serde_json::Value>,
    #[serde(default)]
    pub summary: Option<serde_json::Value>,
    #[serde(default)]
    pub max_tokens_per_page: Option<u32>,
    #[serde(default)]
    pub subpages: Option<u32>,
    #[serde(default)]
    pub subpage_target: Option<serde_json::Value>,
    #[serde(default)]
    pub extras: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResearchRequest {
    pub query: String,
    #[serde(default = "default_num_results")]
    pub num_results: u32,
    #[serde(default)]
    pub system_prompt: Option<String>,
    #[serde(default)]
    pub search_domain_filter: Option<Vec<String>>,
    #[serde(default)]
    pub search_language_filter: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentRequest {
    #[serde(default)]
    pub model: Option<String>,
    pub input: serde_json::Value,
    #[serde(default)]
    pub instructions: Option<String>,
    #[serde(default)]
    pub tools: Option<Vec<serde_json::Value>>,
    #[serde(default)]
    pub tool_choice: Option<String>,
    #[serde(default)]
    pub max_tool_calls: Option<u32>,
    #[serde(default)]
    pub parallel_tool_calls: bool,
    #[serde(default)]
    pub reasoning: Option<serde_json::Value>,
    #[serde(default)]
    pub max_output_tokens: Option<u32>,
    #[serde(default = "default_temperature")]
    pub temperature: f64,
    #[serde(default)]
    pub response_format: Option<serde_json::Value>,
    #[serde(default)]
    pub previous_response_id: Option<String>,
    #[serde(default)]
    pub stream: bool,
    #[serde(default)]
    pub provider: Option<String>,
    #[serde(default = "default_true")]
    pub fallback: bool,
}

fn default_temperature() -> f64 { 1.0 }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatRequest {
    #[serde(default = "default_chat_model")]
    pub model: String,
    pub messages: Vec<serde_json::Value>,
    #[serde(default)]
    pub stream: bool,
    #[serde(default = "default_temperature")]
    pub temperature: f64,
    #[serde(default)]
    pub max_tokens: Option<u32>,
    #[serde(default = "default_true")]
    pub search: bool,
    #[serde(default)]
    pub search_type: Option<String>,
    #[serde(default)]
    pub search_num_results: Option<u32>,
    #[serde(default)]
    pub provider: Option<String>,
}

fn default_chat_model() -> String { "kubi".to_string() }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub service: String,
    pub version: String,
    pub components: HashMap<String, bool>,
}
