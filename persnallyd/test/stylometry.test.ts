import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { proseLines, stripNoise } from "../src/prose.js";
import { analyzeVoice, assemblePack } from "../src/stylometry.js";
import { newEvent, PAYLOAD_SCHEMAS } from "../src/events.js";
import { EventStore } from "../src/store.js";

test("stripNoise removes paths, URLs, code fences, and injected blocks; keeps prose", () => {
  const t = stripNoise(
    "please check the auth flow\nhttps://github.com/x/y\n/Users/me/projects/app/src/index.ts\n```secret code```\n<task-notification>noise</task-notification>",
  );
  assert.match(t, /please check the auth flow/);
  assert.doesNotMatch(t, /github\.com/);
  assert.doesNotMatch(t, /Users\/me|index\.ts/);
  assert.doesNotMatch(t, /task-notification|noise|secret code/);
});

test("proseLines keeps sentences, drops json/paths/single-word lines", () => {
  const lines = proseLines('can you fix this bug\n{"a":1,"b":2,"c":3,"d":4}\n/var/log/app/output.txt\nyes');
  assert.deepEqual(lines, ["can you fix this bug"]);
});

test("analyzeVoice surfaces a repeated phrase + terse tone and builds a valid pack", () => {
  const msgs = Array.from({ length: 20 }, () => "be 100% sure about the analysis. fix it now.");
  const v = analyzeVoice(msgs);
  assert.ok(v.signals.some((s) => s.dimension === "emphasis"), "extracts a recurring phrase as emphasis");
  assert.ok(v.signals.some((s) => /terse/.test(s.pattern)), "detects terse short sentences");
  assert.match(v.pack, /^Write like this user:/);
  for (const s of v.signals) PAYLOAD_SCHEMAS["signal.style"].parse(s); // every signal is schema-valid
});

test("assemblePack lists tone first, then recurring phrasing", () => {
  const pack = assemblePack([
    { dimension: "voice", pattern: "terse", polarity: "does", confidence: 0.8, evidence: "x", basis: "stylometry" },
    { dimension: "emphasis", pattern: "be 100% sure", polarity: "insists", confidence: 0.9, evidence: "10×", basis: "stylometry" },
  ]);
  assert.match(pack, /terse/);
  assert.match(pack, /recurring phrasing.*be 100% sure/);
});

const dir = mkdtempSync(join(tmpdir(), "voice-store-"));
after(() => rmSync(dir, { recursive: true, force: true }));

test("store.voice dedups by pattern (newest wins) and orders richest first", () => {
  const store = new EventStore(join(dir, "t.db"));
  const sig = (pattern: string, confidence: number, ts: string) =>
    newEvent("signal.style", "import:claude-code",
      { dimension: "voice", pattern, polarity: "does", confidence, evidence: "x", basis: "stylometry" },
      { kind: "import", batch: "b", file: "f" }, ts);
  store.append([
    sig("terse", 0.6, "2026-06-01T00:00:00.000Z"),
    sig("terse", 0.9, "2026-06-10T00:00:00.000Z"), // newer → should win
    sig("no emoji", 0.7, "2026-06-05T00:00:00.000Z"),
  ]);
  const v = store.voice();
  const terse = v.items.filter((i) => i.pattern === "terse");
  assert.equal(terse.length, 1, "deduped by pattern");
  assert.equal(terse[0]!.confidence, 0.9, "newest occurrence wins");
  assert.equal(v.items[0]!.pattern, "terse", "highest confidence first");
  assert.match(v.pack, /Write like this user/);
  store.close();
});
