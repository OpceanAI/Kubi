import { Hono } from "hono";
import { z } from "zod";
import { callKubiService } from "../lib/client";

const crawlSchema = z.object({
  url: z.string().url(),
  extractText: z.boolean().default(true),
  extractHtml: z.boolean().default(false),
  maxChars: z.number().int().min(100).max(100000).optional(),
});

export const crawlRoutes = new Hono();

crawlRoutes.post("/", async (c) => {
  const raw = await c.req.json();
  const parsed = crawlSchema.safeParse(raw);
  if (!parsed.success) return c.json({ error: "Validation error", details: parsed.error.flatten() }, 400);

  const d = parsed.data;
  try {
    const result = await callKubiService({ path: "/ai/crawl", body: {
      url: d.url, extract_text: d.extractText, extract_html: d.extractHtml, max_chars: d.maxChars,
    }});
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Crawl failed", message: err.message }, 500);
  }
});
