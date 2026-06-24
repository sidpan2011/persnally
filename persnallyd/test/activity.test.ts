import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { newEvent } from "../src/events.js";
import { EventStore } from "../src/store.js";

const NOW = Date.parse("2026-06-25T12:00:00Z");
const DAY = 86_400_000;
const iso = (daysAgo: number) => new Date(NOW - daysAgo * DAY).toISOString();
const read = (daysAgo: number) =>
  newEvent("context.read", "cli", { scope: "brief", client_purpose: "t", items: 3 }, { kind: "local", surface: "cli" }, iso(daysAgo));
const topic = (daysAgo: number) =>
  newEvent("signal.topic", "cli", { topic: "x", weight: 0.5, intent: "building", sentiment: "neutral", depth: "moderate", category: "technology", entities: [] }, { kind: "local", surface: "cli" }, iso(daysAgo));

function freshStore(): EventStore {
  const dir = mkdtempSync(join(tmpdir(), "activity-"));
  const store = new EventStore(join(dir, "t.db"));
  after(() => { store.close(); rmSync(dir, { recursive: true, force: true }); });
  return store;
}

test("empty store: zeros, no anchors, retention undecided", () => {
  const a = freshStore().activity(NOW);
  assert.equal(a.firstEventAt, null);
  assert.equal(a.firstReadAt, null);
  assert.equal(a.totalReads, 0);
  assert.equal(a.daysSinceFirst, 0);
  assert.equal(a.daysSinceFirstRead, 0);
  assert.equal(a.retainedWeek2, null);
  assert.equal(a.daily.length, 14);
  assert.equal(a.daily.reduce((s, d) => s + d.reads, 0), 0);
});

test("anchors retention to the first read, not onboarding; positive week-2", () => {
  const s = freshStore();
  s.append([topic(25), read(20), read(10), read(1)]); // onboarded 25d ago; serving began 20d ago; read in the week-2 window; read now
  const a = s.activity(NOW);
  assert.equal(a.daysSinceFirst, 25, "onboarding clock");
  assert.equal(a.daysSinceFirstRead, 20, "serving clock — drives retention");
  assert.equal(a.totalReads, 3);
  assert.equal(a.reads7d, 1);
  assert.equal(a.reads30d, 3);
  assert.equal(a.activeDays7d, 1);
  assert.equal(a.activeDays14d, 2); // -10d, -1d
  assert.equal(a.retainedWeek2, true, "read at -10d is in [firstRead+7d, firstRead+14d) = [-13d, -6d)");
});

test("week-2 retention is false when no read lands in days 8–14 after the first read", () => {
  const s = freshStore();
  s.append([topic(25), read(20), read(19), read(1)]); // reads cluster at serving-start and now; none in [-13d, -6d)
  assert.equal(s.activity(NOW).retainedWeek2, false);
});

test("a gap between onboarding and first read doesn't false-fail (the founder case)", () => {
  const s = freshStore();
  s.append([topic(90), read(5), read(1)]); // onboarded 90d ago, but serving began only 5d ago
  const a = s.activity(NOW);
  assert.equal(a.daysSinceFirst, 90);
  assert.equal(a.daysSinceFirstRead, 5);
  assert.equal(a.retainedWeek2, null, "long onboarding + recent reads must read as in-progress, not 'inactive'");
});
