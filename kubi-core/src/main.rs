use axum::{routing::{get, post}, Router};
use tower_http::cors::CorsLayer;
use tracing_subscriber::{fmt, EnvFilter};

mod cache;
mod models;
mod ranking;
mod routes;
mod search;
mod streaming;

use cache::RedisCache;

#[derive(Clone)]
pub struct AppState {
    pub kubi_ai_url: String,
    pub cache: Option<RedisCache>,
    pub http_client: reqwest::Client,
}

#[tokio::main]
async fn main() {
    fmt()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")))
        .init();

    let kubi_ai_url = std::env::var("KUBI_AI_URL").unwrap_or_else(|_| "http://localhost:8000".to_string());
    let redis_url = std::env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379".to_string());
    let host = std::env::var("KUBI_CORE_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port: u16 = std::env::var("KUBI_CORE_PORT").unwrap_or_else(|_| "8080".to_string()).parse().unwrap_or(8080);

    let cache = match RedisCache::new(&redis_url).await {
        Ok(c) => {
            tracing::info!("Redis cache connected");
            Some(c)
        }
        Err(e) => {
            tracing::warn!("Redis unavailable, caching disabled: {}", e);
            None
        }
    };

    let http_client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(120))
        .build()
        .expect("Failed to build HTTP client");

    let state = AppState { kubi_ai_url: kubi_ai_url.clone(), cache, http_client };

    let app = Router::new()
        .route("/health", get(routes::health::health))
        .route("/core/search", post(routes::search::search))
        .route("/core/answer", post(routes::answer::answer))
        .route("/core/stream", post(routes::stream::stream))
        .route("/core/expand", post(routes::expand::expand))
        .route("/core/crawl", post(routes::crawl::crawl))
        .route("/core/embed", post(routes::embed::embed))
        .route("/core/similar", post(routes::similar::similar))
        .route("/core/rank", post(routes::rank::rank))
        .layer(CorsLayer::permissive())
        .with_state(state);

    let addr = format!("{}:{}", host, port);
    tracing::info!("Kubi Core listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await.expect("Failed to bind");
    axum::serve(listener, app).await.expect("Server failed");
}
