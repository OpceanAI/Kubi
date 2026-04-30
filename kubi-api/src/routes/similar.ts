import { Hono } from "hono";
import { z } from "zod";
import { callKubiService } from "../lib/client";

const similarSchema = z.object({
  url: z.string().url(),
  query: z.string().optional(),
  type: z.enum(["instant", "fast", "auto", "deep-lite", "deep", "research"]).default("fast"),
  numResults: z.number().int().min(1).max(100).default(10),
  includeDomains: z.array(z.string()).optional(),
  excludeDomains: z.array(z.string()).optional(),
});

export const similarRoutes = new Hono();

similarRoutes.post("/", async (c) => {
  const raw = await c.req.json();
  const parsed = similarSchema.safeParse(raw);
  if (!parsed.success) return c.json({ error: "Validation error", details: parsed.error.flatten() }, 400);

  const d = parsed.data;
  try {
    const result = await callKubiService({ path: "/ai/similar", body: {
      url: d.url, query: d.query, type: d.type, num_results: d.numResults,
      include_domains: d.includeDomains || [], exclude_domains: d.excludeDomains || [],
    }});
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Similar search failed", message: err.message }, 500);
  }
});
