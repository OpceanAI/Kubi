import type { Context, Next } from "hono";

const API_KEY = process.env.KUBI_API_KEY || "sk-kubi-change-me-in-production";

export async function authMiddleware(c: Context, next: Next) {
  const apiKey = c.req.header("x-api-key") || c.req.header("Authorization")?.replace("Bearer ", "");

  if (!apiKey) {
    return c.json({
      error: "Unauthorized",
      message: "API key is required. Provide it via x-api-key header or Authorization: Bearer <key>",
    }, 401);
  }

  if (apiKey !== API_KEY) {
    return c.json({ error: "Unauthorized", message: "Invalid API key" }, 401);
  }

  await next();
}
