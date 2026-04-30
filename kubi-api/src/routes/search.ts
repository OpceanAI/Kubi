import { Hono } from "hono";
import { z } from "zod";
import { callKubiService } from "../lib/client";

const searchSchema = z.object({
  query: z.union([z.string().min(1).max(2000), z.array(z.string().min(1).max(2000)).max(5)]),
  type: z.enum(["instant", "fast", "auto", "deep-lite", "deep", "deep-reasoning"]).default("auto"),
  stream: z.boolean().default(false),
  preset: z.string().optional(),
  numResults: z.number().int().min(1).max(100).default(10),
  maxResults: z.number().int().optional(),
  category: z.enum(["company", "people", "research paper", "news", "personal site", "financial report"]).optional(),
  userLocation: z.string().optional(),
  country: z.string().optional(),
  includeDomains: z.array(z.string()).optional(),
  excludeDomains: z.array(z.string()).optional(),
  searchDomainFilter: z.array(z.string()).optional(),
  searchLanguageFilter: z.array(z.string()).optional(),
  searchRecencyFilter: z.enum(["day", "week", "month", "year"]).optional(),
  safeSearch: z.enum(["off", "moderate", "strict"]).optional(),
  startPublishedDate: z.string().optional(),
  endPublishedDate: z.string().optional(),
  startCrawlDate: z.string().optional(),
  endCrawlDate: z.string().optional(),
  moderation: z.boolean().optional(),
  additionalQueries: z.array(z.string()).optional(),
  systemPrompt: z.string().optional(),
  outputSchema: z.record(z.any()).optional(),
  maxTokensPerPage: z.number().int().optional(),
  maxTokens: z.number().int().optional(),
  provider: z.string().optional(),
  fallback: z.boolean().optional(),
  contents: z.object({
    text: z.union([z.boolean(), z.object({ maxCharacters: z.number().int().optional() })]).optional(),
    highlights: z.union([z.boolean(), z.object({ maxCharacters: z.number().int().optional(), query: z.string().optional() })]).optional(),
    summary: z.union([z.boolean(), z.object({ query: z.string().optional() })]).optional(),
    subpages: z.number().int().optional(),
    subpageTarget: z.union([z.string(), z.array(z.string())]).optional(),
    extras: z.object({ links: z.number().int().optional(), imageLinks: z.number().int().optional() }).optional(),
  }).optional(),
});

export const searchRoutes = new Hono();

searchRoutes.post("/", async (c) => {
  const raw = await c.req.json();
  const parsed = searchSchema.safeParse(raw);
  if (!parsed.success) return c.json({ error: "Validation error", details: parsed.error.flatten() }, 400);

  const d = parsed.data;
  try {
    const result = await callKubiService({ path: "/ai/search", body: {
      query: d.query, type: d.type, stream: d.stream, preset: d.preset,
      num_results: d.numResults || d.maxResults, category: d.category,
      user_location: d.userLocation, country: d.country,
      include_domains: d.includeDomains || [], exclude_domains: d.excludeDomains || [],
      search_domain_filter: d.searchDomainFilter,
      search_language_filter: d.searchLanguageFilter,
      search_recency_filter: d.searchRecencyFilter,
      safe_search: d.safeSearch,
      start_published_date: d.startPublishedDate, end_published_date: d.endPublishedDate,
      start_crawl_date: d.startCrawlDate, end_crawl_date: d.endCrawlDate,
      moderation: d.moderation || false, additional_queries: d.additionalQueries,
      system_prompt: d.systemPrompt, output_schema: d.outputSchema,
      max_tokens_per_page: d.maxTokensPerPage, max_tokens: d.maxTokens,
      provider: d.provider, fallback: d.fallback !== false,
      contents: d.contents,
    }});
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Search failed", message: err.message }, 500);
  }
});
