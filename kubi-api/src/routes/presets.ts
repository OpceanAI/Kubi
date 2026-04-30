import { Hono } from "hono";
import { callKubiService } from "../lib/client";

export const presetsRoutes = new Hono();

presetsRoutes.get("/", async (c) => {
  try {
    const result = await callKubiService({ path: "/ai/presets", body: {} });
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Failed to list presets", message: err.message }, 500);
  }
});
