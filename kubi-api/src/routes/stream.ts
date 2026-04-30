import { Hono } from "hono";
import { z } from "zod";
import { callKubiStream } from "../lib/client";

const streamSchema = z.object({
  query: z.string().min(1).max(2000),
  type: z.enum(["instant", "fast", "auto", "deep-lite", "deep", "research"]).default("auto"),
  numResults: z.number().int().min(1).max(100).default(10),
  includeText: z.boolean().default(false),
  systemPrompt: z.string().optional(),
});

export const streamRoutes = new Hono();

streamRoutes.post("/", async (c) => {
  const raw = await c.req.json();
  const parsed = streamSchema.safeParse(raw);
  if (!parsed.success) return c.json({ error: "Validation error", details: parsed.error.flatten() }, 400);

  const d = parsed.data;
  try {
    const aiResponse = await callKubiStream({ path: "/ai/stream", body: {
      query: d.query, type: d.type, num_results: d.numResults,
      include_text: d.includeText, system_prompt: d.systemPrompt,
    }});

    return new Response(aiResponse.body, {
      headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", Connection: "keep-alive", "X-Accel-Buffering": "no" },
    });
  } catch (err: any) {
    return c.json({ error: "Stream failed", message: err.message }, 500);
  }
});
