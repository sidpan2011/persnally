import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, describe, test } from "node:test";
import { startDaemon } from "../src/daemon.js";
import { newEvent } from "../src/events.js";
import { allowedCategories, clearScope, isAllowed, loadScopes, setScope } from "../src/permissions.js";
import { EventStore } from "../src/store.js";

const dir = mkdtempSync(join(tmpdir(), "perms-test-"));
process.env.PERSNALLY_DIR = dir; // config (scopes) resolves here, in-process
after(() => { delete process.env.PERSNALLY_DIR; rmSync(dir, { recursive: true, force: true }); });

describe("scope storage", () => {
  test("default-open: unknown client sees everything", () => {
    assert.equal(allowedCategories("fresh-client"), null);
    assert.equal(isAllowed("fresh-client", "health"), true);
  });

  test("set/clear scope round-trips and enforces", () => {
    setScope("editor-x", ["technology", "career"]);
    assert.deepEqual(allowedCategories("editor-x"), ["technology", "career"]);
    assert.equal(isAllowed("editor-x", "technology"), true);
    assert.equal(isAllowed("editor-x", "health"), false);
    assert.ok(Object.keys(loadScopes()).includes("editor-x"));
    assert.equal(clearScope("editor-x"), true);
    assert.equal(allowedCategories("editor-x"), null, "cleared = unrestricted again");
    assert.equal(clearScope("editor-x"), false, "clearing twice is a no-op");
  });
});

describe("daemon enforcement", () => {
  const PORT = 49855;
  const BASE = `http://127.0.0.1:${PORT}`;
  const store = new EventStore(join(dir, "test.db"));
  let server: ReturnType<typeof startDaemon>;

  const topic = (name: string, category: string) =>
    newEvent("signal.topic", "import:claude", {
      topic: name, weight: 0.8, intent: "building", sentiment: "positive",
      depth: "deep", category, entities: [],
    }, { kind: "import", batch: "b1", file: "conversations.json" });

  before(() => {
    store.append([topic("rust", "technology"), topic("therapy", "health"), topic("raise", "finance")]);
    store.rebuild();
    store.saveProfile({ headline: "h", sections: [], generated_at: "2026-06-12T00:00:00Z", model: "t" });
    setScope("cursor", ["technology"]);
    server = startDaemon(store, PORT);
  });
  after(() => { server.close(); store.close(); });

  test("/topics filters to the client's allowed categories", async () => {
    const all = await (await fetch(`${BASE}/topics`)).json() as { category: string }[];
    assert.equal(all.length, 3, "unscoped request sees all");

    const scoped = await (await fetch(`${BASE}/topics?client=cursor`)).json() as { category: string }[];
    assert.deepEqual(scoped.map((t) => t.category), ["technology"], "cursor sees only technology");

    const open = await (await fetch(`${BASE}/topics?client=claude-desktop`)).json() as unknown[];
    assert.equal(open.length, 3, "unscoped client sees all");
  });

  test("/profile is 403 for a scoped client, 200 otherwise", async () => {
    assert.equal((await fetch(`${BASE}/profile?client=cursor`)).status, 403);
    assert.equal((await fetch(`${BASE}/profile?client=claude-desktop`)).status, 200);
    assert.equal((await fetch(`${BASE}/profile`)).status, 200);
  });

  test("/scopes reports the config", async () => {
    const scopes = await (await fetch(`${BASE}/scopes`)).json() as Record<string, string[]>;
    assert.deepEqual(scopes.cursor, ["technology"]);
  });
});
