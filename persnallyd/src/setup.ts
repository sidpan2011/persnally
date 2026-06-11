/**
 * One-command onboarding: find exports (zipped or unzipped), pick an engine,
 * import everything, synthesize, connect AI clients, open the dashboard.
 * Idempotent — already-imported sources are recorded in config and skipped.
 */

import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, openSync, readSync, closeSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { loadConfig, saveConfig } from "./config.js";

export type ExportKind = "claude" | "chatgpt";

export interface FoundExport {
  kind: ExportKind;
  path: string;     // dir or conversations.json, ready to import
  origin: string;   // what the user recognizes (zip path or dir) — also the idempotency key
  cleanup?: string; // temp dir to remove after import
}

function sniffKind(conversationsJson: string): ExportKind | null {
  const fd = openSync(conversationsJson, "r");
  const buf = Buffer.alloc(4096);
  const n = readSync(fd, buf, 0, buf.length, 0);
  closeSync(fd);
  const head = buf.toString("utf-8", 0, n);
  if (head.includes('"chat_messages"')) return "claude";
  if (head.includes('"mapping"')) return "chatgpt";
  return null;
}

function zipHasConversations(zipPath: string): boolean {
  try {
    return execFileSync("unzip", ["-l", zipPath], { encoding: "utf-8", stdio: ["ignore", "pipe", "ignore"] })
      .includes("conversations.json");
  } catch {
    return false;
  }
}

/** Scans a directory (default ~/Downloads) for Claude/ChatGPT exports, zipped or not. */
export function detectExports(searchDir = join(homedir(), "Downloads")): FoundExport[] {
  if (!existsSync(searchDir)) return [];
  const found: FoundExport[] = [];

  for (const entry of readdirSync(searchDir, { withFileTypes: true })) {
    const full = join(searchDir, entry.name);
    if (entry.isDirectory() && existsSync(join(full, "conversations.json"))) {
      const kind = sniffKind(join(full, "conversations.json"));
      if (kind) found.push({ kind, path: full, origin: full });
    } else if (entry.isFile() && entry.name.endsWith(".zip") && zipHasConversations(full)) {
      const tmp = mkdtempSync(join(tmpdir(), "persnally-export-"));
      execFileSync("unzip", ["-q", full, "-d", tmp]);
      const root = existsSync(join(tmp, "conversations.json"))
        ? tmp
        : readdirSync(tmp).map((d) => join(tmp, d)).find((d) => existsSync(join(d, "conversations.json")));
      const kind = root ? sniffKind(join(root, "conversations.json")) : null;
      if (root && kind) found.push({ kind, path: root, origin: full, cleanup: tmp });
      else rmSync(tmp, { recursive: true, force: true });
    }
  }
  return found;
}

export function alreadyImported(origin: string): boolean {
  const sources = loadConfig().imported_sources;
  return Array.isArray(sources) && sources.includes(origin);
}

export function markImported(origin: string): void {
  const sources = loadConfig().imported_sources;
  const list = Array.isArray(sources) ? (sources as string[]) : [];
  if (!list.includes(origin)) saveConfig({ imported_sources: [...list, origin] });
}
