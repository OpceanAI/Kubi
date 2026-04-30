FROM oven/bun:1.1-alpine
WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile || bun install
COPY src/ ./src/
EXPOSE 3001
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --spider -q http://localhost:3001/health || exit 1
CMD ["bun", "run", "src/index.ts"]
