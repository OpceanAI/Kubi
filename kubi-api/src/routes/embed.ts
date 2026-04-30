import { Hono } from "hono";
import { z } from "zod";
import { callKubiService } from "../lib/client";

const embedSchema = z.object({ text: z.string().min(1).max(50000) });

export const embedRoutes = new Hono();

embedRoutes.post("/", async (c) => {
  const raw = await c.req.json();
  const parsed = embedSchema.safeParse(raw);
  if (!parsed.success) return c.json({ error: "Validation error", details: parsed.error.flatten() }, 400);

  try {
    const result = await callKubiService({ path: "/ai/embed", body: parsed.data });
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Embed failed", message: err.message }, 500);
  }
});
