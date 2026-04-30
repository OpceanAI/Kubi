use axum::{body::Body, extract::State, response::{IntoResponse, Response}, Json};
use serde_json::json;
use crate::AppState;

pub async fn stream(State(state): State<AppState>, Json(body): Json<serde_json::Value>) -> impl IntoResponse {
    let url = format!("{}/ai/stream", state.kubi_ai_url);
    match state.http_client.post(&url).json(&body).send().await {
        Ok(resp) => {
            let status = resp.status();
            let body = Body::from_stream(resp.bytes_stream());
            match Response::builder()
                .status(status)
                .header("content-type", "text/event-stream")
                .header("cache-control", "no-cache")
                .header("connection", "keep-alive")
                .body(body)
            {
                Ok(r) => r,
                Err(e) => {
                    let err_body = Body::from(json!({"error": "Stream build failed", "message": e.to_string()}).to_string());
                    Response::builder().status(500).header("content-type", "application/json").body(err_body).unwrap()
                }
            }
        }
        Err(e) => {
            tracing::error!("Stream failed: {}", e);
            let body = Body::from(json!({"error": "Stream failed", "message": e.to_string()}).to_string());
            Response::builder().status(500).header("content-type", "application/json").body(body).unwrap()
        }
    }
}
