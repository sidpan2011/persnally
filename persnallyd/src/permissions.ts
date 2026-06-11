/**
 * Per-client category scopes. Default-open: a client with no entry sees
 * everything. Once scoped, it sees only its allowed categories — enforced
 * at the daemon, so no MCP client can read past its grant. Stored in config.
 */

import { loadConfig, saveConfig } from "./config.js";

export const CATEGORIES = [
  "technology", "business", "finance", "career", "health",
  "science", "creative", "education", "lifestyle", "news", "other",
] as const;
export type Category = (typeof CATEGORIES)[number];

export type Scopes = Record<string, Category[]>;

export function loadScopes(): Scopes {
  const s = loadConfig().client_scopes;
  return s && typeof s === "object" ? (s as Scopes) : {};
}

export function setScope(client: string, categories: Category[]): void {
  saveConfig({ client_scopes: { ...loadScopes(), [client]: categories } });
}

export function clearScope(client: string): boolean {
  const scopes = loadScopes();
  if (!(client in scopes)) return false;
  delete scopes[client];
  saveConfig({ client_scopes: scopes });
  return true;
}

/** null = unrestricted (sees all). An array = the only categories this client may read. */
export function allowedCategories(client: string): Category[] | null {
  return loadScopes()[client] ?? null;
}

export function isAllowed(client: string, category: string): boolean {
  const allowed = allowedCategories(client);
  return allowed === null || allowed.includes(category as Category);
}
