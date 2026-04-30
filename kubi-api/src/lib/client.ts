const KUBI_AI_URL = process.env.KUBI_AI_URL || "http://localhost:8000";
const KUBI_CORE_URL = process.env.KUBI_CORE_URL || "http://localhost:8080";

export interface KubiRequestOptions {
  path: string;
  body: Record<string, unknown>;
  service?: "ai" | "core";
  timeout?: number;
}

export async function callKubiService<T = unknown>(opts: KubiRequestOptions): Promise<T> {
  const baseUrl = opts.service === "core" ? KUBI_CORE_URL : KUBI_AI_URL;
  const url = `${baseUrl}${opts.path}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), opts.timeout || 30000);

  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(opts.body),
      signal: controller.signal,
    });

    if (!resp.ok) {
      const errorBody = await resp.text().catch(() => "Unknown error");
      throw new Error(`Service error (${resp.status}): ${errorBody}`);
    }

    return (await resp.json()) as T;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function callKubiStream(opts: KubiRequestOptions): Promise<Response> {
  const baseUrl = opts.service === "core" ? KUBI_CORE_URL : KUBI_AI_URL;
  const resp = await fetch(`${baseUrl}${opts.path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(opts.body),
  });

  if (!resp.ok) {
    const errorBody = await resp.text().catch(() => "Unknown error");
    throw new Error(`Service error (${resp.status}): ${errorBody}`);
  }

  return resp;
}
