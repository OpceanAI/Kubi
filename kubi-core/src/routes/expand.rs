use axum::{extract::State, Json};
use serde_json::json;
use crate::AppState;

pub async fn expand(State(state): State<AppState>, Json(body): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let cache_key = crate::cache::RedisCache::cache_key(
        "expand",
        body.get("query").and_then(|q| q.as_str()).unwrap_or("default"),
        "default",
    );

    if let Some(ref cache) = state.cache {
        if let Some(cached) = cache.get::<serde_json::Value>(&cache_key).await {
            return Json(cached);
        }
    }

    let url = format!("{}/ai/expand", state.kubi_ai_url);
    match state.http_client.post(&url).json(&body).send().await {
        Ok(resp) => match resp.json::<serde_json::Value>().await {
            Ok(result) => {
                if let Some(ref cache) = state.cache {
                    let _ = cache.set(&cache_key, &result).await;
                }
                Json(result)
            }
            Err(_) => Json(json!({"error": "Failed to parse response"})),
        },
        Err(e) => Json(json!({"error": "Expand failed", "message": e.to_string()})),
    }
}
