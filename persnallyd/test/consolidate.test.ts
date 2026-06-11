import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { runConsolidation, shouldRunNow } from "../src/consolidate.js";
import { newEvent } from "../src/events.js";
import { EventStore } from "../src/store.js";

test("shouldRunNow: gated by hour and once-per-day", () => {
  const before = new Date("2026-06-12T02:00:00");
  const after3am = new Date("2026-06-12T03:30:00");
  assert.equal(shouldRunNow(undefined, before), false, "before 3am: no");
  assert.equal(shouldRunNow(undefined, after3am), true, "after 3am, never run: yes");
  assert.equal(shouldRunNow("2026-06-12T03:05:00.000Z", after3am), false, "already ran today: no");
  assert.equal(shouldRunNow("2026-06-11T03:05:00.000Z", after3am), true, "ran yesterday: yes");
});

const dir = mkdtempSync(join(tmpdir(), "consolidate-test-"));
const store = new EventStore(join(dir, "test.db"));
after(() => { store.close(); rmSync(dir, { recursive: true, force: true }); });

const topic = (name: string) =>
  newEvent("signal.topic", "mcp:cursor", {
    topic: name, weight: 0.8, intent: "building", sentiment: "positive",
    depth: "deep", category: "technology", entities: [],
  }, { kind: "mcp", client: "cursor" });

test("without an engine: refreshes decay, emits no assertions", async () => {
  store.append([topic("rust"), topic("sqlite")]);
  const r = await runConsolidation(store, null, new Date("2026-06-12T03:00:00"));
  assert.equal(r.assertions, 0);
  assert.equal(r.profileRefreshed, false);
  assert.ok(store.topics().length >= 1, "decay rebuild ran");
});

test("with engine + enough signal: emits derived behavior assertions", async () => {
  // Fresh store so last_consolidation from the previous test doesn't filter these out.
  const d2 = mkdtempSync(join(tmpdir(), "consolidate-2-"));
  const s2 = new EventStore(join(d2, "t.db"));
  process.env.PERSNALLY_DIR = d2; // config (last_consolidation) lands here
  try {
    s2.append(Array.from({ length: 6 }, (_, i) => topic(`topic-${i}`)));
    let sawSummary = "";
    const engine = {
      model: "mock", label: "mock",
      extract: async ({ content }: { content: string }) => {
        sawSummary = content;
        return { assertions: [{ claim: "deep focus on systems topics", kind: "behavior", confidence: 0.8, evidence: "6 recent deep signals" }] };
      },
    };
    const r = await runConsolidation(s2, engine, new Date("2026-06-12T03:00:00"));
    assert.equal(r.newSignals, 6);
    assert.equal(r.assertions, 1);
    assert.match(sawSummary, /topic-0/);

    const derived = s2.query({ type: "signal.assertion" })[0]!;
    assert.equal(derived.provenance.kind, "derived");
    assert.equal((derived.provenance as { from: string[] }).from.length, 6);
  } finally {
    s2.close();
    delete process.env.PERSNALLY_DIR;
    rmSync(d2, { recursive: true, force: true });
  }
});
