import { Hono } from "hono";
import { z } from "zod";
import { callKubiService } from "../lib/client";

const researchSchema = z.object({
  query: z.string().min(1).max(5000),
  numResults: z.number().int().min(1).max(50).default(20),
  systemPrompt: z.string().optional(),
  searchDomainFilter: z.array(z.string()).optional(),
  searchLanguageFilter: z.array(z.string()).optional(),
});

export const researchRoutes = new Hono();

researchRoutes.post("/", async (c) => {
  const raw = await c.req.json();
  const parsed = researchSchema.safeParse(raw);
  if (!parsed.success) return c.json({ error: "Validation error", details: parsed.error.flatten() }, 400);

  const d = parsed.data;
  try {
    const result = await callKubiService({ path: "/ai/research", body: {
      query: d.query, num_results: d.numResults,
      system_prompt: d.systemPrompt,
      search_domain_filter: d.searchDomainFilter,
      search_language_filter: d.searchLanguageFilter,
    }});
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Research failed", message: err.message }, 500);
  }
});

researchRoutes.get("/:taskId", async (c) => {
  const taskId = c.req.param("taskId");
  try {
    const kubiAiUrl = process.env.KUBI_AI_URL || "http://localhost:8000";
    const resp = await fetch(`${kubiAiUrl}/ai/research/${taskId}`);
    if (!resp.ok) {
      return c.json({ error: "Research task not found" }, 404);
    }
    return c.json(await resp.json());
  } catch (err: any) {
    return c.json({ error: "Research task not found", message: err.message }, 404);
  }
});
