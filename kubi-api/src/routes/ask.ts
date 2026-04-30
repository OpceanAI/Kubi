import { Hono } from "hono";
import { z } from "zod";
import { callKubiService } from "../lib/client";

const askSchema = z.object({
  query: z.union([z.string().min(1).max(2000), z.array(z.string().min(1).max(2000)).max(5)]),
  mode: z.enum(["instant", "fast", "auto", "deep-lite", "deep", "research"]).default("auto"),
  preset: z.string().optional(),
  numResults: z.number().int().min(1).max(100).default(10),
  model: z.string().optional(),
  includeText: z.boolean().default(false),
  systemPrompt: z.string().optional(),
  outputSchema: z.record(z.any()).optional(),
  searchDomainFilter: z.array(z.string()).optional(),
  searchLanguageFilter: z.array(z.string()).optional(),
  searchRecencyFilter: z.enum(["day", "week", "month", "year"]).optional(),
  safeSearch: z.enum(["off", "moderate", "strict"]).optional(),
  provider: z.string().optional(),
  fallback: z.boolean().optional(),
});

export const askRoutes = new Hono();

askRoutes.post("/", async (c) => {
  const raw = await c.req.json();
  const parsed = askSchema.safeParse(raw);
  if (!parsed.success) return c.json({ error: "Validation error", details: parsed.error.flatten() }, 400);

  const d = parsed.data;
  try {
    const result = await callKubiService({ path: "/ai/answer", body: {
      query: d.query, type: d.mode, num_results: d.numResults, model: d.model,
      include_text: d.includeText, system_prompt: d.systemPrompt, output_schema: d.outputSchema,
      preset: d.preset,
      search_domain_filter: d.searchDomainFilter,
      search_language_filter: d.searchLanguageFilter,
      search_recency_filter: d.searchRecencyFilter,
      safe_search: d.safeSearch,
      provider: d.provider, fallback: d.fallback !== false,
    }});
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Ask failed", message: err.message }, 500);
  }
});
