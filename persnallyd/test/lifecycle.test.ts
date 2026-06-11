import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { promisify } from "node:util";

const run = promisify(execFile);
const dir = mkdtempSync(join(tmpdir(), "lifecycle-test-"));
const CLI = join(import.meta.dirname, "..", "src", "cli.js");
const PORT = "49877";
const env = { ...process.env, PERSNALLY_DIR: dir };

after(() => rmSync(dir, { recursive: true, force: true }));

test("start → health → status → second start refused → stop", async () => {
  const started = await run("node", [CLI, "start", "--port", PORT], { env });
  assert.match(started.stdout, /started \(pid \d+\)/);
  assert.ok(existsSync(join(dir, "daemon.pid")));

  const health = await fetch(`http://127.0.0.1:${PORT}/health`);
  assert.equal(health.status, 200);

  const status = await run("node", [CLI, "status"], { env });
  assert.match(status.stdout, /Daemon: running \(pid \d+\)/);

  await assert.rejects(run("node", [CLI, "start", "--port", PORT], { env }), /already running/);

  const stopped = await run("node", [CLI, "stop"], { env });
  assert.match(stopped.stdout, /Stopped daemon/);
  assert.ok(!existsSync(join(dir, "daemon.pid")), "pidfile removed on graceful shutdown");
  await assert.rejects(fetch(`http://127.0.0.1:${PORT}/health`), "port must be closed");
});

test("stale pidfile (dead pid) is detected and cleaned up", async () => {
  writeFileSync(join(dir, "daemon.pid"), "999999");
  const status = await run("node", [CLI, "status"], { env });
  assert.match(status.stdout, /Daemon: not running/);
  assert.ok(!existsSync(join(dir, "daemon.pid")), "stale pidfile cleaned");
});

test("stop when nothing is running is a clean no-op", async () => {
  const stopped = await run("node", [CLI, "stop"], { env });
  assert.match(stopped.stdout, /was not running/);
});
