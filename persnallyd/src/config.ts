/**
 * Daemon config at ~/.persnally/config.json — most importantly the Anthropic
 * key, so the launchd-run daemon (no shell env) can synthesize. Unknown fields
 * are preserved (the file predates v2). Saved with owner-only permissions.
 */

import { chmodSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { DATA_DIR } from "./paths.js";

// Resolved at call time so PERSNALLY_DIR overrides work in-process (tests), not just for subprocesses.
function configFile(): string {
  return join(process.env.PERSNALLY_DIR ?? DATA_DIR, "config.json");
}

export function loadConfig(): Record<string, unknown> {
  try {
    return JSON.parse(readFileSync(configFile(), "utf-8")) as Record<string, unknown>;
  } catch {
    return {};
  }
}

export function saveConfig(updates: Record<string, unknown>): void {
  const file = configFile();
  mkdirSync(dirname(file), { recursive: true });
  const merged = { ...loadConfig(), ...updates };
  // mode on create closes the world-readable window before chmod; chmod also
  // corrects perms on a pre-existing file. The config holds the API key.
  writeFileSync(file, JSON.stringify(merged, null, 2) + "\n", { mode: 0o600 });
  chmodSync(file, 0o600);
}

/** Env wins over config; sets process.env so the Anthropic SDK picks it up. */
export function applyApiKey(): boolean {
  if (process.env.ANTHROPIC_API_KEY) return true;
  const key = loadConfig().anthropic_api_key;
  if (typeof key === "string" && key.startsWith("sk-ant-")) {
    process.env.ANTHROPIC_API_KEY = key;
    return true;
  }
  return false;
}

export function configPath(): string {
  const file = configFile();
  return existsSync(file) ? file : `${file} (not created yet)`;
}
