import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { promisify } from "node:util";

const run = promisify(execFile);
const dir = mkdtempSync(join(tmpdir(), "config-test-"));
const CLI = join(import.meta.dirname, "..", "src", "cli.js");
const env = { ...process.env, PERSNALLY_DIR: dir };

after(() => rmSync(dir, { recursive: true, force: true }));

test("set-key writes owner-only file and preserves pre-existing v1 fields", async () => {
  writeFileSync(join(dir, "config.json"), JSON.stringify({ email: "old@v1.com", frequency: "daily" }));

  await run("node", [CLI, "config", "set-key", "sk-ant-test-12345678"], { env });

  const file = join(dir, "config.json");
  assert.equal(statSync(file).mode & 0o777, 0o600);
  const cfg = JSON.parse(readFileSync(file, "utf-8"));
  assert.equal(cfg.anthropic_api_key, "sk-ant-test-12345678");
  assert.equal(cfg.email, "old@v1.com", "v1 fields preserved");
});

test("config shows the key masked, never in full", async () => {
  const { stdout } = await run("node", [CLI, "config"], { env });
  assert.ok(!stdout.includes("sk-ant-test-12345678"), "full key must not be printed");
  assert.match(stdout, /sk-ant-test-…5678/);
});

test("set-key rejects non-Anthropic-shaped input", async () => {
  await assert.rejects(run("node", [CLI, "config", "set-key", "hunter2"], { env }), /expected an Anthropic key/);
});

test("a freshly created key file is owner-only (no world-readable window)", async () => {
  const fresh = mkdtempSync(join(tmpdir(), "config-fresh-"));
  try {
    await run("node", [CLI, "config", "set-key", "sk-ant-fresh-87654321"], { env: { ...process.env, PERSNALLY_DIR: fresh } });
    assert.equal(statSync(join(fresh, "config.json")).mode & 0o777, 0o600);
  } finally {
    rmSync(fresh, { recursive: true, force: true });
  }
});
