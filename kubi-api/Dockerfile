# Kubi API - Bun + Hono
FROM oven/bun:1.1-alpine

WORKDIR /app

# Install dependencies
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile || bun install

# Copy application code
COPY src/ ./src/
COPY tsconfig.json ./

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --spider -q http://localhost:3000/health || exit 1

# Run the application
CMD ["bun", "run", "src/index.ts"]
