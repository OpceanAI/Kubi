import { Hono } from "hono";
import { callKubiService } from "../lib/client";

export const providersRoutes = new Hono();

providersRoutes.get("/", async (c) => {
  try {
    const result = await callKubiService({ path: "/ai/providers", body: {} });
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Failed to list providers", message: err.message }, 500);
  }
});
