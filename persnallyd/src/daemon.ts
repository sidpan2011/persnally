/**
 * Local HTTP API + dashboard — loopback only, the single access path to the event store.
 * Phase 2's MCP context server will be a client of this API.
 */

import http from "node:http";
import { readFileSync } from "node:fs";
import { loadConfig } from "./config.js";
import { runConsolidation, shouldRunNow } from "./consolidate.js";
import { newEvent, validateEvent, type EventType, type PersnallyEvent, type Provenance } from "./events.js";
import { chooseExtractor } from "./llm.js";
import { synthesizeProfile } from "./profile.js";
import type { EventStore } from "./store.js";

export const DEFAULT_PORT = 4983;
export const VERSION = "0.1.0";

export function startDaemon(store: EventStore, port = DEFAULT_PORT): http.Server {
  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url ?? "/", `http://127.0.0.1:${port}`);
    try {
      if (req.method === "GET" && url.pathname === "/") {
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        return res.end(dashboardHtml());
      }
      if (req.method === "GET" && url.pathname === "/health") {
        return json(res, 200, { ok: true, version: VERSION });
      }
      if (req.method === "GET" && url.pathname === "/stats") {
        return json(res, 200, store.stats());
      }
      if (req.method === "GET" && url.pathname === "/topics") {
        return json(res, 200, store.topics(num(url, "limit", 50)));
      }
      if (req.method === "GET" && url.pathname === "/profile") {
        const profile = store.getProfile();
        return profile ? json(res, 200, profile) : json(res, 404, { error: "no profile synthesized yet" });
      }
      if (req.method === "POST" && url.pathname === "/synthesize") {
        const engine = await chooseExtractor("profile");
        return json(res, 200, await synthesizeProfile(store, engine.extract, engine.model));
      }
      if (req.method === "POST" && url.pathname === "/consolidate") {
        const engine = await chooseExtractor("extract").catch(() => null);
        return json(res, 200, await runConsolidation(store, engine));
      }
      if (req.method === "GET" && url.pathname === "/events") {
        const ids = url.searchParams.get("ids");
        if (ids) return json(res, 200, store.getEvents(ids.split(",").filter(Boolean)));
        return json(res, 200, store.query({
          type: url.searchParams.get("type") ?? undefined,
          source: url.searchParams.get("source") ?? undefined,
          since: url.searchParams.get("since") ?? undefined,
          limit: num(url, "limit", 100),
        }));
      }
      if (req.method === "POST" && url.pathname === "/events") {
        const body = await readBody(req);
        // The daemon owns event identity: items without an id get one assigned here.
        const events: PersnallyEvent[] = (Array.isArray(body) ? body : [body]).map((raw) => {
          const r = raw as Record<string, unknown>;
          return r.id
            ? validateEvent(r)
            : newEvent(
                r.type as EventType,
                String(r.source ?? ""),
                r.payload as Record<string, unknown>,
                r.provenance as Provenance,
                typeof r.ts === "string" ? r.ts : undefined,
              );
        });
        store.append(events);
        store.rebuild();
        return json(res, 201, { inserted: events.length, ids: events.map((e) => e.id) });
      }
      if (req.method === "DELETE" && url.pathname === "/events") {
        if (url.searchParams.get("confirm") !== "all") {
          return json(res, 400, { error: "destructive: requires ?confirm=all" });
        }
        store.forgetAll();
        return json(res, 200, { deleted: "all" });
      }
      if (req.method === "DELETE" && url.pathname.startsWith("/topics/")) {
        const topic = decodeURIComponent(url.pathname.slice("/topics/".length));
        if (!topic) return json(res, 400, { error: "topic required" });
        return json(res, 200, { deleted: store.forgetTopic(topic) });
      }
      return json(res, 404, { error: "not found" });
    } catch (e) {
      return json(res, 400, { error: e instanceof Error ? e.message : "bad request" });
    }
  });
  server.listen(port, "127.0.0.1");

  // Nightly reflection: check every 30 min, run once per day at/after the consolidation hour.
  const timer = setInterval(async () => {
    const lastRun = loadConfig().last_consolidation;
    if (!shouldRunNow(typeof lastRun === "string" ? lastRun : undefined, new Date())) return;
    try {
      const engine = await chooseExtractor("extract").catch(() => null);
      const r = await runConsolidation(store, engine);
      console.error(`consolidation: ${r.newSignals} new signals, ${r.assertions} assertions, profile ${r.profileRefreshed ? "refreshed" : "kept"}`);
    } catch (e) {
      console.error("consolidation failed:", e instanceof Error ? e.message : e);
    }
  }, 30 * 60 * 1000);
  timer.unref();
  server.on("close", () => clearInterval(timer));

  return server;
}

let cachedHtml: string | undefined;
function dashboardHtml(): string {
  cachedHtml ??= readFileSync(new URL("./dashboard.html", import.meta.url), "utf-8");
  return cachedHtml;
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
