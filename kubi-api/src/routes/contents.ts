import { Hono } from "hono";
import { z } from "zod";
import { callKubiService } from "../lib/client";

const contentsSchema = z.object({
  urls: z.array(z.string().url()).min(1).max(100),
  ids: z.array(z.string()).optional(),
  text: z.union([z.boolean(), z.object({
    maxCharacters: z.number().int().optional(), includeHtmlTags: z.boolean().optional(),
    verbosity: z.enum(["compact", "standard", "full"]).optional(),
    includeSections: z.array(z.string()).optional(), excludeSections: z.array(z.string()).optional(),
  })]).optional(),
  highlights: z.union([z.boolean(), z.object({
    maxCharacters: z.number().int().optional(), query: z.string().optional(),
  })]).optional(),
  summary: z.union([z.boolean(), z.object({ query: z.string().optional(), schema: z.record(z.any()).optional() })]).optional(),
  livecrawl: z.string().optional(), livecrawlTimeout: z.number().int().optional(),
  maxAgeHours: z.number().int().optional(), subpages: z.number().int().optional(),
  subpageTarget: z.union([z.string(), z.array(z.string())]).optional(),
  extras: z.object({ links: z.number().int().optional(), imageLinks: z.number().int().optional() }).optional(),
});

export const contentsRoutes = new Hono();

contentsRoutes.post("/", async (c) => {
  const raw = await c.req.json();
  const parsed = contentsSchema.safeParse(raw);
  if (!parsed.success) return c.json({ error: "Validation error", details: parsed.error.flatten() }, 400);

  try {
    const result = await callKubiService({ path: "/ai/contents", body: parsed.data });
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Contents failed", message: err.message }, 500);
  }
});
