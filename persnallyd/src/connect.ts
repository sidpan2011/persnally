/**
 * Writes the Persnally MCP server into AI clients' configs.
 * Only touches clients that are actually installed; merges, never clobbers.
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

export const CLIENTS = ["claude-code", "claude-desktop", "cursor"] as const;
export type Client = (typeof CLIENTS)[number];

function configPathFor(client: Client): { file: string; installed: boolean } {
  const home = homedir();
  switch (client) {
    case "claude-code": {
      const file = join(home, ".claude.json");
      return { file, installed: existsSync(file) || existsSync(join(home, ".claude")) };
    }
    case "claude-desktop": {
      const dir = join(home, "Library", "Application Support", "Claude");
      return { file: join(dir, "claude_desktop_config.json"), installed: existsSync(dir) };
    }
    case "cursor": {
      const dir = join(home, ".cursor");
      return { file: join(dir, "mcp.json"), installed: existsSync(dir) };
    }
  }
}

export function mcpServerPath(): string {
  if (process.env.PERSNALLY_MCP && existsSync(process.env.PERSNALLY_MCP)) return process.env.PERSNALLY_MCP;
  // Bundled in this package: build/src/connect.js → build/src/mcp/index.js
  const bundled = join(import.meta.dirname, "mcp", "index.js");
  if (existsSync(bundled)) return bundled;
  throw new Error("Persnally MCP server build not found — set PERSNALLY_MCP to its index.js");
}

/** Returns the config file written, or null when the client isn't installed. */
export function connectClient(client: Client): string | null {
  const { file, installed } = configPathFor(client);
  if (!installed) return null;
  const cfg = existsSync(file)
    ? (JSON.parse(readFileSync(file, "utf-8")) as Record<string, unknown>)
    : {};
  const servers = (cfg.mcpServers ??= {}) as Record<string, unknown>;
  servers.persnally = { command: "node", args: [mcpServerPath()] };
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, JSON.stringify(cfg, null, 2) + "\n");
  return file;
}

export function connectAll(): { client: Client; file: string | null }[] {
  return CLIENTS.map((client) => ({ client, file: connectClient(client) }));
}
