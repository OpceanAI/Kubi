# Kubi Core - Rust Axum Orchestrator
# Build stage
FROM rust:1.83-bookworm AS builder

WORKDIR /app

# Create a dummy project to cache dependencies
RUN cargo init --name kubi-core .

COPY Cargo.toml Cargo.lock* ./
RUN cargo build --release 2>/dev/null || true

# Copy source code
COPY src/ ./src/

# Build the actual binary
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/kubi-core /app/kubi-core

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the binary
CMD ["/app/kubi-core"]
