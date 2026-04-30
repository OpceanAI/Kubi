import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { secureHeaders } from "hono/secure-headers";

import { searchRoutes } from "./routes/search";
import { askRoutes } from "./routes/ask";
import { streamRoutes } from "./routes/stream";
import { expandRoutes } from "./routes/expand";
import { crawlRoutes } from "./routes/crawl";
import { embedRoutes } from "./routes/embed";
import { similarRoutes } from "./routes/similar";
import { contentsRoutes } from "./routes/contents";
import { chatRoutes } from "./routes/chat";
import { researchRoutes } from "./routes/research";
import { presetsRoutes } from "./routes/presets";
import { providersRoutes } from "./routes/providers";
import { authMiddleware } from "./middleware/auth";
import { rateLimitMiddleware } from "./middleware/rateLimit";

const app = new Hono();

app.use("*", logger());
app.use("*", secureHeaders());
app.use("*", cors({
  origin: process.env.KUBI_API_CORS_ORIGINS?.split(",") || ["*"],
  allowMethods: ["GET", "POST", "OPTIONS"],
  allowHeaders: ["Content-Type", "Authorization", "x-api-key"],
}));

app.get("/health", (c) => c.json({
  status: "ok", service: "kubi-api", version: "1.0.0", timestamp: new Date().toISOString(),
}));

const api = new Hono();
api.use("*", authMiddleware);
api.use("*", rateLimitMiddleware);

api.route("/search", searchRoutes);
api.route("/ask", askRoutes);
api.route("/stream", streamRoutes);
api.route("/expand", expandRoutes);
api.route("/crawl", crawlRoutes);
api.route("/embed", embedRoutes);
api.route("/similar", similarRoutes);
api.route("/contents", contentsRoutes);
api.route("/research", researchRoutes);
api.route("/presets", presetsRoutes);
api.route("/providers", providersRoutes);
api.route("/chat", chatRoutes);

app.route("/api/v1", api);

app.notFound((c) => c.json({ error: "Not found", message: "The requested endpoint does not exist" }, 404));

app.onError((err, c) => {
  console.error("API Error:", err);
  return c.json({ error: "Internal server error", message: err.message }, 500);
});

const port = parseInt(process.env.KUBI_API_PORT || "3000");
const host = process.env.KUBI_API_HOST || "0.0.0.0";

console.log(`Kubi API starting on ${host}:${port}`);

export default { port, hostname: host, fetch: app.fetch };
