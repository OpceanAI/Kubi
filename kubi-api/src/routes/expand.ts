import { Hono } from "hono";
import { z } from "zod";
import { callKubiService } from "../lib/client";

const expandSchema = z.object({
  query: z.string().min(1).max(1000),
  numVariations: z.number().int().min(1).max(20).default(5),
});

export const expandRoutes = new Hono();

expandRoutes.post("/", async (c) => {
  const raw = await c.req.json();
  const parsed = expandSchema.safeParse(raw);
  if (!parsed.success) return c.json({ error: "Validation error", details: parsed.error.flatten() }, 400);

  try {
    const result = await callKubiService({ path: "/ai/expand", body: {
      query: parsed.data.query, num_variations: parsed.data.numVariations,
    }});
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Expand failed", message: err.message }, 500);
  }
});
