import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";

const KUBI_API_URL = process.env.KUBI_API_URL || "http://localhost:3000";
const KUBI_API_KEY = process.env.KUBI_API_KEY || "";

async function callKubi(path: string, body: Record<string, unknown>) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (KUBI_API_KEY) headers["x-api-key"] = KUBI_API_KEY;

  const resp = await fetch(`${KUBI_API_URL}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const err = await resp.text().catch(() => "Unknown error");
    throw new Error(`Kubi API error (${resp.status}): ${err}`);
  }

  return resp.json();
}

function createServer(): McpServer {
  const server = new McpServer({ name: "kubi", version: "1.0.0" });

  server.tool(
    "web_search",
    "Search the web for any topic and get clean, ready-to-use content",
    {
      query: z.string().describe("Natural language search query"),
      numResults: z.number().optional().default(5).describe("Number of results (1-100)"),
    },
    async ({ query, numResults }) => {
      const result = (await callKubi("/api/v1/search", {
        query,
        type: "fast",
        numResults: numResults || 5,
        contents: { highlights: { maxCharacters: 4000 } },
      })) as any;

      const formatted = (result.results || [])
        .map(
          (r: any, i: number) =>
            `### ${i + 1}. ${r.title}\nURL: ${r.url}\n${r.highlights?.join("\n") || r.snippet || ""}`
        )
        .join("\n\n");

      return { content: [{ type: "text", text: formatted || "No results found." }] };
    }
  );

  server.tool(
    "web_fetch",
    "Read a webpage's full content as clean markdown from one or more URLs",
    {
      urls: z.array(z.string().url()).describe("Array of URLs to fetch"),
      maxCharacters: z.number().optional().default(10000).describe("Max characters per page"),
    },
    async ({ urls, maxCharacters }) => {
      const result = (await callKubi("/api/v1/contents", {
        urls,
        text: { maxCharacters: maxCharacters || 10000 },
      })) as any;

      const formatted = (result.results || [])
        .map(
          (r: any) =>
            `## ${r.title || r.url}\nSource: ${r.url}\n\n${r.text || "No content extracted."}`
        )
        .join("\n\n---\n\n");

      return { content: [{ type: "text", text: formatted || "No content extracted." }] };
    }
  );

  server.tool(
    "web_search_advanced",
    "Advanced web search with full control over category filters, domain restrictions, date ranges, highlights, summaries, and subpage crawling",
    {
      query: z.string().describe("Natural language search query"),
      type: z.enum(["instant", "fast", "auto", "deep-lite", "deep", "deep-reasoning"]).optional().default("auto"),
      numResults: z.number().optional().default(10),
      category: z.enum(["company", "people", "research paper", "news", "personal site", "financial report"]).optional(),
      includeDomains: z.array(z.string()).optional().describe("Only return results from these domains"),
      excludeDomains: z.array(z.string()).optional(),
      startPublishedDate: z.string().optional().describe("ISO 8601 date - only results after this date"),
      endPublishedDate: z.string().optional(),
      outputSchema: z.record(z.any()).optional().describe("JSON Schema for structured output"),
      systemPrompt: z.string().optional().describe("Instructions for synthesis"),
    },
    async (params) => {
      const result = (await callKubi("/api/v1/search", params)) as any;

      if (result.output) {
        return { content: [{ type: "text", text: JSON.stringify(result.output.content, null, 2) }] };
      }

      const formatted = (result.results || [])
        .map(
          (r: any, i: number) =>
            `### ${i + 1}. ${r.title}\nURL: ${r.url}\nPublished: ${r.publishedDate || "Unknown"}\n${r.summary || r.highlights?.join("\n") || r.snippet || ""}`
        )
        .join("\n\n");

      return { content: [{ type: "text", text: formatted || "No results found." }] };
    }
  );

  server.tool(
    "ask",
    "Ask a question and get an AI-synthesized answer with citations from web search",
    {
      query: z.string().describe("Question to answer"),
      type: z.enum(["instant", "fast", "auto", "deep-lite", "deep", "deep-reasoning"]).optional().default("auto"),
    },
    async ({ query, type }) => {
      const result = (await callKubi("/api/v1/ask", {
        query,
        mode: type || "auto",
        numResults: 5,
      })) as any;

      let text = result.answer || "No answer generated.";
      if (result.citations?.length) {
        text += "\n\nSources:\n" + result.citations.map((c: any, i: number) => `[${i + 1}] ${c.title} - ${c.url}`).join("\n");
      }

      return { content: [{ type: "text", text }] };
    }
  );

  server.tool(
    "find_similar",
    "Find pages similar to a given URL using semantic search",
    {
      url: z.string().url().describe("URL to find similar pages for"),
      numResults: z.number().optional().default(5),
    },
    async ({ url, numResults }) => {
      const result = (await callKubi("/api/v1/similar", {
        url,
        numResults: numResults || 5,
      })) as any;

      const formatted = (result.results || [])
        .map((r: any, i: number) => `${i + 1}. ${r.title}\n   ${r.url} (score: ${r.score?.toFixed(3)})`)
        .join("\n");

      return { content: [{ type: "text", text: formatted || "No similar pages found." }] };
    }
  );

  return server;
}

const port = parseInt(process.env.KUBI_MCP_PORT || "3001");
const host = process.env.KUBI_MCP_HOST || "0.0.0.0";

console.log(`Kubi MCP Server starting on ${host}:${port}`);

const httpServer = Bun.serve({
  port,
  hostname: host,
  async fetch(req) {
    const url = new URL(req.url);

    if (url.pathname === "/mcp" && req.method === "POST") {
      try {
        const server = createServer();
        const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
        await server.connect(transport);
        return transport.handleRequest(req);
      } catch (e: any) {
        return Response.json({ error: "MCP error", message: e.message }, { status: 500 });
      }
    }

    if (url.pathname === "/health") {
      return Response.json({ status: "ok", service: "kubi-mcp", version: "1.0.0" });
    }

    return new Response("Not Found", { status: 404 });
  },
});

console.log(`Kubi MCP Server listening on http://${host}:${port}/mcp`);
