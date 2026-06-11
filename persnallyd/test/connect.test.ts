import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { promisify } from "node:util";

const run = promisify(execFile);
const home = mkdtempSync(join(tmpdir(), "connect-test-"));
const CLI = join(import.meta.dirname, "..", "src", "cli.js");

// Hermetic MCP target: CI doesn't build the sibling mcp_server package (build/ is gitignored).
const fakeMcp = join(home, "fake-mcp", "index.js");
mkdirSync(join(home, "fake-mcp"));
writeFileSync(fakeMcp, "// stub\n");

const env = { ...process.env, HOME: home, PERSNALLY_DIR: join(home, ".persnally"), PERSNALLY_MCP: fakeMcp };

after(() => rmSync(home, { recursive: true, force: true }));

// Fake installed clients: claude-code (existing config with another server), cursor (dir only)
writeFileSync(join(home, ".claude.json"), JSON.stringify({ mcpServers: { other: { command: "x" } }, theme: "dark" }));
mkdirSync(join(home, ".cursor"));

test("connect --all writes installed clients, merges configs, skips missing", async () => {
  const { stdout } = await run("node", [CLI, "connect", "--all"], { env });
  assert.match(stdout, /Connected claude-code/);
  assert.match(stdout, /Connected cursor/);
  assert.match(stdout, /claude-desktop not installed — skipped/);

  const claude = JSON.parse(readFileSync(join(home, ".claude.json"), "utf-8"));
  assert.ok(claude.mcpServers.persnally.args[0].endsWith("index.js"));
  assert.equal(claude.mcpServers.other.command, "x", "existing servers preserved");
  assert.equal(claude.theme, "dark", "unrelated config preserved");

  const cursor = JSON.parse(readFileSync(join(home, ".cursor", "mcp.json"), "utf-8"));
  assert.ok(cursor.mcpServers.persnally);
});

test("connect rejects unknown clients", async () => {
  await assert.rejects(run("node", [CLI, "connect", "vscode"], { env }), /unknown client/);
});
