use axum::{extract::State, Json};
use std::collections::HashMap;
use crate::models::HealthResponse;
use crate::AppState;

pub async fn health(State(state): State<AppState>) -> Json<HealthResponse> {
    let mut components = HashMap::new();
    components.insert("kubi_core".to_string(), true);

    let kubi_healthy = match state.http_client.get(format!("{}/ai/health", state.kubi_ai_url)).send().await {
        Ok(resp) => resp.status().is_success(),
        Err(_) => false,
    };
    components.insert("kubi_ai".to_string(), kubi_healthy);

    Json(HealthResponse {
        status: if kubi_healthy { "ok".to_string() } else { "degraded".to_string() },
        service: "kubi-core".to_string(),
        version: "1.0.0".to_string(),
        components,
    })
}
