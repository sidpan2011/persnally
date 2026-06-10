/**
 * Local HTTP API — loopback only, the single access path to the event store.
 * Phase 2's MCP context server will be a client of this API.
 */

import http from "node:http";
import { validateEvent, type PersnallyEvent } from "./events.js";
import type { EventStore } from "./store.js";

export const DEFAULT_PORT = 4983;
export const VERSION = "0.1.0";

export function startDaemon(store: EventStore, port = DEFAULT_PORT): http.Server {
  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url ?? "/", `http://127.0.0.1:${port}`);
    try {
      if (req.method === "GET" && url.pathname === "/health") {
        return json(res, 200, { ok: true, version: VERSION });
      }
      if (req.method === "GET" && url.pathname === "/stats") {
        return json(res, 200, store.stats());
      }
      if (req.method === "GET" && url.pathname === "/topics") {
        return json(res, 200, store.topics(num(url, "limit", 50)));
      }
      if (req.method === "GET" && url.pathname === "/events") {
        return json(res, 200, store.query({
          type: url.searchParams.get("type") ?? undefined,
          source: url.searchParams.get("source") ?? undefined,
          since: url.searchParams.get("since") ?? undefined,
          limit: num(url, "limit", 100),
        }));
      }
      if (req.method === "POST" && url.pathname === "/events") {
        const body = await readBody(req);
        const events = (Array.isArray(body) ? body : [body]).map(validateEvent) as PersnallyEvent[];
        store.append(events);
        store.rebuild();
        return json(res, 201, { inserted: events.length });
      }
      return json(res, 404, { error: "not found" });
    } catch (e) {
      return json(res, 400, { error: e instanceof Error ? e.message : "bad request" });
    }
  });
  server.listen(port, "127.0.0.1");
  return server;
}

function json(res: http.ServerResponse, status: number, body: unknown): void {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

function num(url: URL, key: string, fallback: number): number {
  const v = Number(url.searchParams.get(key));
  return Number.isFinite(v) && v > 0 ? v : fallback;
}

function readBody(req: http.IncomingMessage): Promise<unknown> {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (chunk) => (data += chunk));
    req.on("end", () => {
      try { resolve(JSON.parse(data)); } catch { reject(new Error("invalid JSON body")); }
    });
    req.on("error", reject);
  });
}
