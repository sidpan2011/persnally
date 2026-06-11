/**
 * Daemon config at ~/.persnally/config.json — most importantly the Anthropic
 * key, so the launchd-run daemon (no shell env) can synthesize. Unknown fields
 * are preserved (the file predates v2). Saved with owner-only permissions.
 */

import { chmodSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { DATA_DIR } from "./paths.js";

const CONFIG_FILE = join(DATA_DIR, "config.json");

export function loadConfig(): Record<string, unknown> {
  try {
    return JSON.parse(readFileSync(CONFIG_FILE, "utf-8")) as Record<string, unknown>;
  } catch {
    return {};
  }
}

export function saveConfig(updates: Record<string, unknown>): void {
  mkdirSync(DATA_DIR, { recursive: true });
  const merged = { ...loadConfig(), ...updates };
  writeFileSync(CONFIG_FILE, JSON.stringify(merged, null, 2) + "\n");
  chmodSync(CONFIG_FILE, 0o600);
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
  return existsSync(CONFIG_FILE) ? CONFIG_FILE : `${CONFIG_FILE} (not created yet)`;
}
