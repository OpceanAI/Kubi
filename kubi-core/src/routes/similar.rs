use axum::{extract::State, Json};
use serde_json::json;
use crate::AppState;

pub async fn similar(State(state): State<AppState>, Json(body): Json<serde_json::Value>) -> Json<serde_json::Value> {
    let url = format!("{}/ai/similar", state.kubi_ai_url);
    match state.http_client.post(&url).json(&body).send().await {
        Ok(resp) => match resp.json::<serde_json::Value>().await {
            Ok(result) => Json(result),
            Err(_) => Json(json!({"error": "Failed to parse response"})),
        },
        Err(e) => Json(json!({"error": "Similar failed", "message": e.to_string()})),
    }
}
