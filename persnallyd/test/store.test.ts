import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { newEvent } from "../src/events.js";
import { EventStore } from "../src/store.js";

const dir = mkdtempSync(join(tmpdir(), "persnallyd-test-"));
const store = new EventStore(join(dir, "test.db"));
after(() => { store.close(); rmSync(dir, { recursive: true, force: true }); });

const topic = (name: string, weight = 0.8) =>
  newEvent("signal.topic", "import:claude", {
    topic: name, weight, intent: "building", sentiment: "positive", depth: "deep",
    category: "technology", entities: [],
  }, { kind: "import", batch: "b1", file: "conversations.json" });

test("append, query, and stats round-trip", () => {
  store.append([topic("rust"), topic("react.js"), topic("ReactJS")]);
  assert.equal(store.stats().total, 3);
  assert.equal(store.query({ type: "signal.topic" }).length, 3);
  assert.equal(store.query({ type: "signal.topic" })[0]!.payload.topic, "ReactJS");
});

test("rebuild merges normalized topic variants into one view row", () => {
  store.rebuild();
  const topics = store.topics();
  const react = topics.find((t) => t.topic_key === "reactjs");
  assert.ok(react);
  assert.equal(react.signals, 2);
  assert.equal(react.event_ids.length, 2);
});

test("forgetTopic hard-deletes events and derived descendants, then rebuilds", () => {
  const base = store.query({ type: "signal.topic" }).find((e) => e.payload.topic === "rust")!;
  store.append([
    newEvent("signal.assertion", "system",
      { claim: "likes rust", kind: "preference", confidence: 0.9, evidence: "topics" },
      { kind: "derived", from: [base.id] }),
  ]);
  const deleted = store.forgetTopic("rust");
  assert.equal(deleted, 2);
  assert.ok(!store.topics().some((t) => t.topic_key === "rust"));
});

test("forgetBatch removes an entire import reversibly", () => {
  const before = store.stats().total;
  const deleted = store.forgetBatch("b1");
  assert.ok(deleted > 0);
  assert.equal(store.stats().total, before - deleted);
});

test("forgetAll also clears the synthesized profile (deletable for real)", () => {
  store.append([topic("rust")]);
  store.saveProfile({ headline: "a builder", sections: [], generated_at: "2026-06-15T00:00:00Z", model: "test" });
  assert.ok(store.getProfile(), "profile present before wipe");
  store.forgetAll();
  assert.equal(store.stats().total, 0);
  assert.equal(store.getProfile(), null, "profile must be gone after forget --all");
});
