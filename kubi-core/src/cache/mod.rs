use anyhow::Result;
use redis::aio::ConnectionManager;
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};

#[derive(Clone)]
pub struct RedisCache {
    conn: ConnectionManager,
    default_ttl: u64,
}

impl RedisCache {
    pub async fn new(redis_url: &str) -> Result<Self> {
        let client = redis::Client::open(redis_url)?;
        let conn = ConnectionManager::new(client).await?;
        let ttl = std::env::var("CACHE_TTL_SECONDS")
            .unwrap_or_else(|_| "300".to_string())
            .parse::<u64>()
            .unwrap_or(300);
        Ok(Self { conn, default_ttl: ttl })
    }

    pub async fn get<T: for<'de> Deserialize<'de>>(&self, key: &str) -> Option<T> {
        let mut conn = self.conn.clone();
        let result: Result<String, _> = conn.get(key).await;
        match result {
            Ok(data) => serde_json::from_str(&data).ok(),
            Err(_) => None,
        }
    }

    pub async fn set<T: Serialize>(&self, key: &str, value: &T) -> Result<()> {
        let mut conn = self.conn.clone();
        let data = serde_json::to_string(value)?;
        conn.set_ex::<_, _, ()>(key, data, self.default_ttl).await?;
        Ok(())
    }

    pub fn cache_key(prefix: &str, query: &str, mode: &str) -> String {
        use std::hash::{Hash, Hasher};
        let mut hasher = std::collections::hash_map::DefaultHasher::new();
        query.hash(&mut hasher);
        mode.hash(&mut hasher);
        format!("kubi:{}:{:x}", prefix, hasher.finish())
    }
}
