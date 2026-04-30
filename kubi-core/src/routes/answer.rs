use axum::{extract::State, Json};
use serde_json::json;
use crate::AppState;

pub async fn answer(State(state): State<AppState>, Json(body): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let cache_key = crate::cache::RedisCache::cache_key(
        "answer",
        body.get("query").and_then(|q| q.as_str()).unwrap_or("default"),
        body.get("type").and_then(|t| t.as_str()).unwrap_or("auto"),
    );

    if let Some(ref cache) = state.cache {
        if let Some(cached) = cache.get::<serde_json::Value>(&cache_key).await {
            return Json(cached);
        }
    }

    let url = format!("{}/ai/answer", state.kubi_ai_url);
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
        Err(e) => Json(json!({"error": "Answer failed", "message": e.to_string()})),
    }
}
