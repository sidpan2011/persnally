import assert from "node:assert/strict";
import { test } from "node:test";
import { newEvent, normalizeTopic, safeIso, uuidv7, validateEvent } from "../src/events.js";

const topicPayload = {
  topic: "rust async",
  weight: 0.8,
  intent: "debugging",
  sentiment: "negative",
  depth: "deep",
  category: "technology",
  entities: ["tokio"],
};

test("newEvent builds a valid signal.topic event", () => {
  const e = newEvent("signal.topic", "mcp:claude-code", topicPayload, { kind: "mcp", client: "claude-code" });
  assert.equal(e.type, "signal.topic");
  assert.equal(e.schema_ver, 1);
  assert.ok(e.id.match(/^[0-9a-f-]{36}$/));
});

test("safeIso passes valid dates through and falls back on junk (never throws)", () => {
  assert.equal(safeIso("2026-01-02T03:04:05.000Z"), "2026-01-02T03:04:05.000Z");
  assert.equal(safeIso(1700000000000), new Date(1700000000000).toISOString());
  for (const junk of ["not-a-date", "", undefined, null, {}, NaN]) {
    const out = safeIso(junk);
    assert.ok(!Number.isNaN(Date.parse(out)), `safeIso(${JSON.stringify(junk)}) must yield a valid ISO date`);
  }
});

test("unknown event type is rejected", () => {
  assert.throws(() =>
    validateEvent({
      id: uuidv7(), ts: new Date().toISOString(), recorded_at: new Date().toISOString(),
      source: "cli", type: "signal.unknown", payload: {}, provenance: { kind: "local", surface: "cli" }, schema_ver: 1,
    }),
  );
});

test("payload violating its type schema is rejected", () => {
  assert.throws(() =>
    newEvent("signal.topic", "cli", { ...topicPayload, weight: 5 }, { kind: "local", surface: "cli" }),
  );
});

test("invalid source is rejected", () => {
  assert.throws(() => newEvent("signal.topic", "random-thing", topicPayload, { kind: "local", surface: "cli" }));
});

test("uuidv7 is time-ordered", () => {
  const a = uuidv7();
  const b = uuidv7();
  assert.ok(a.slice(0, 13) <= b.slice(0, 13));
});

test("normalizeTopic merges framework variants", () => {
  assert.equal(normalizeTopic("React.js"), normalizeTopic("ReactJS"));
  assert.equal(normalizeTopic("React JS"), "reactjs");
  assert.equal(normalizeTopic("C++"), "cpp");
});
