/**
 * Thin HTTP client for persnallyd — the daemon is the single source of truth;
 * this MCP server is just a protocol adapter in front of it.
 */

const BASE = process.env.PERSNALLYD_URL ?? "http://127.0.0.1:4983";

export const DAEMON_HINT =
  "persnallyd is not running. Start it with `persnallyd serve` (or install: npm i -g persnallyd), then retry.";

export class DaemonUnreachable extends Error {
  constructor() { super(DAEMON_HINT); }
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(BASE + path, init);
  } catch {
    throw new DaemonUnreachable();
  }
}

export async function daemonGet<T>(path: string): Promise<T | null> {
  const r = await request(path);
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`daemon ${path}: ${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

export async function daemonPost<T>(path: string, body: unknown): Promise<T> {
  const r = await request(path, { method: "POST", body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`daemon ${path}: ${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

export async function daemonDelete<T>(path: string): Promise<T> {
  const r = await request(path, { method: "DELETE" });
  if (!r.ok) throw new Error(`daemon ${path}: ${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}
