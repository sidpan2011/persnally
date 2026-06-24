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

test("empty store: all zeros, 14 daily buckets, retention undecided", () => {
  const a = freshStore().activity(NOW);
  assert.equal(a.firstEventAt, null);
  assert.equal(a.totalReads, 0);
  assert.equal(a.daysSinceFirst, 0);
  assert.equal(a.retainedWeek2, null);
  assert.equal(a.daily.length, 14);
  assert.equal(a.daily.reduce((s, d) => s + d.reads, 0), 0);
});

test("computes read windows, distinct active days, and a positive week-2 retention", () => {
  const s = freshStore();
  s.append([topic(20), read(2), read(2), read(10)]); // onboarded 20d ago; 2 reads ~now, 1 inside the week-2 window
  const a = s.activity(NOW);
  assert.equal(a.daysSinceFirst, 20);
  assert.equal(a.totalReads, 3);
  assert.equal(a.reads7d, 2);
  assert.equal(a.reads30d, 3);
  assert.equal(a.activeDays7d, 1, "two reads on the same day count as one active day");
  assert.equal(a.activeDays14d, 2);
  assert.equal(a.retainedWeek2, true, "a read at -10d falls in [first+7d, first+14d)");
  assert.equal(a.daily.length, 14);
});

test("week-2 retention is false when no read lands in days 8–14", () => {
  const s = freshStore();
  s.append([topic(20), read(18), read(1)]); // reads in week-1 and now, none in the week-2 window
  assert.equal(s.activity(NOW).retainedWeek2, false);
});

test("week-2 retention stays null until the window has fully elapsed", () => {
  const s = freshStore();
  s.append([topic(5), read(1)]); // onboarded only 5d ago
  assert.equal(s.activity(NOW).retainedWeek2, null);
});
