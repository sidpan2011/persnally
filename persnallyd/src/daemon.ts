/**
 * Local HTTP API + dashboard — loopback only, the single access path to the event store.
 * Phase 2's MCP context server will be a client of this API.
 */

import http from "node:http";
import { readFileSync } from "node:fs";
import { loadConfig } from "./config.js";
import { runConsolidation, shouldRunNow } from "./consolidate.js";
import { allowedCategories, loadScopes, type Category } from "./permissions.js";
import { newEvent, validateEvent, type EventType, type PersnallyEvent, type Provenance } from "./events.js";
import { chooseExtractor } from "./llm.js";
import { synthesizeProfile } from "./profile.js";
import type { EventStore } from "./store.js";

export const DEFAULT_PORT = 4983;
const MAX_BODY_BYTES = 25 * 1024 * 1024; // generous for import batches; bounds memory
const MAX_QUERY_LIMIT = 10_000;          // ceiling for public ?limit= params

// Single source of truth for the user-visible version: package.json.
const pkg = JSON.parse(readFileSync(new URL("../../package.json", import.meta.url), "utf-8")) as { version: string };
export const VERSION: string = pkg.version;

export function startDaemon(store: EventStore, port = DEFAULT_PORT): http.Server {
  const localHosts = [`127.0.0.1:${port}`, `localhost:${port}`];
  const server = http.createServer(async (req, res) => {
    // Loopback binding alone doesn't stop browsers: webpages can fire
    // no-preflight POSTs at 127.0.0.1 (CSRF) or reach it via DNS rebinding.
    if (!localHosts.includes(req.headers.host ?? "")) {
      return json(res, 403, { error: "forbidden: unrecognized Host" });
    }
    const origin = req.headers.origin;
    if (origin && !localHosts.some((h) => origin === `http://${h}`)) {
      return json(res, 403, { error: "forbidden: cross-origin requests are not allowed" });
    }
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
        const client = url.searchParams.get("client");
        const allowed = client ? allowedCategories(client) : null;
        let topics = store.topics(num(url, "limit", 50));
        if (allowed) topics = topics.filter((t) => allowed.includes(t.category as Category));
        return json(res, 200, topics);
      }
      if (req.method === "GET" && url.pathname === "/profile") {
        // The synthesized profile is holistic prose — a scoped client gets only its
        // allowed topics (above), never the cross-category narrative.
        const client = url.searchParams.get("client");
        if (client && allowedCategories(client) !== null) {
          return json(res, 403, { error: "scoped: this client does not have profile access", scoped: true });
        }
        const profile = store.getProfile();
        return profile ? json(res, 200, profile) : json(res, 404, { error: "no profile synthesized yet" });
      }
      if (req.method === "GET" && url.pathname === "/scopes") {
        return json(res, 200, loadScopes());
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
        // JSON-only forces browsers to preflight (which fails above) — no-preflight
        // content types like text/plain can't reach the write path.
        if (!(req.headers["content-type"] ?? "").includes("application/json")) {
          return json(res, 415, { error: "Content-Type must be application/json" });
        }
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
        // Views derive only from signal.* events — skip the O(all-events) rebuild
        // for telemetry writes like context.read.
        if (events.some((e) => e.type.startsWith("signal."))) store.rebuild();
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
  // Never throw from the responder — the request socket may already be gone
  // (e.g. an oversized body we destroyed), and a throw here would be unhandled.
  if (res.headersSent || res.writableEnded) return;
  try {
    res.writeHead(status, { "Content-Type": "application/json" });
    res.end(JSON.stringify(body));
  } catch { /* socket closed mid-response */ }
}

function num(url: URL, key: string, fallback: number): number {
  const v = Number(url.searchParams.get(key));
  return Number.isFinite(v) && v > 0 ? Math.min(v, MAX_QUERY_LIMIT) : fallback;
}

function readBody(req: http.IncomingMessage): Promise<unknown> {
  return new Promise((resolve, reject) => {
    let data = "";
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(new Error("request body too large"));
        req.destroy();
        return;
      }
      data += chunk;
    });
    req.on("end", () => {
      try { resolve(JSON.parse(data)); } catch { reject(new Error("invalid JSON body")); }
    });
    req.on("error", reject);
  });
}
