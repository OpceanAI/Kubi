import { Hono } from "hono";
import { callKubiService } from "../lib/client";

export const chatRoutes = new Hono();

chatRoutes.post("/completions", async (c) => {
  const raw = await c.req.json();

  try {
    const result = await callKubiService({ path: "/v1/chat/completions", body: {
      model: raw.model || "kubi", messages: raw.messages || [], stream: raw.stream || false,
      temperature: raw.temperature || 0.7, max_tokens: raw.maxTokens || raw.max_tokens || 2048,
      search: raw.search !== false, search_type: raw.searchType, search_num_results: raw.searchNumResults,
      provider: raw.provider,
    }});
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Chat completion failed", message: err.message }, 500);
  }
});

chatRoutes.post("/agent", async (c) => {
  const raw = await c.req.json();

  try {
    const result = await callKubiService({ path: "/v1/agent", body: {
      model: raw.model, input: raw.input, instructions: raw.instructions,
      tools: raw.tools || [], tool_choice: raw.toolChoice || raw.tool_choice || "auto",
      max_tool_calls: raw.maxToolCalls || raw.max_tool_calls,
      parallel_tool_calls: raw.parallelToolCalls !== false,
      reasoning: raw.reasoning,
      max_output_tokens: raw.maxOutputTokens || raw.max_output_tokens,
      temperature: raw.temperature || 1.0,
      response_format: raw.responseFormat || raw.response_format,
      previous_response_id: raw.previousResponseId || raw.previous_response_id,
      stream: raw.stream || false,
      provider: raw.provider, fallback: raw.fallback !== false,
    }});
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Agent request failed", message: err.message }, 500);
  }
});

chatRoutes.post("/responses", async (c) => {
  const raw = await c.req.json();

  try {
    const result = await callKubiService({ path: "/v1/responses", body: raw });
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: "Responses request failed", message: err.message }, 500);
  }
});
