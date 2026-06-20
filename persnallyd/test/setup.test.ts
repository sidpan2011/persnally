import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { detectExports } from "../src/setup.js";

const dir = mkdtempSync(join(tmpdir(), "setup-detect-"));
after(() => rmSync(dir, { recursive: true, force: true }));

// Unzipped Claude export
mkdirSync(join(dir, "claude-export"));
writeFileSync(join(dir, "claude-export", "conversations.json"),
  JSON.stringify([{ uuid: "1", chat_messages: [] }]));

// Unzipped ChatGPT export
mkdirSync(join(dir, "chatgpt-export"));
writeFileSync(join(dir, "chatgpt-export", "conversations.json"),
  JSON.stringify([{ conversation_id: "1", mapping: {} }]));

// Zipped Claude export
const zipSrc = join(dir, "zip-src");
mkdirSync(zipSrc);
writeFileSync(join(zipSrc, "conversations.json"), JSON.stringify([{ uuid: "2", chat_messages: [] }]));
execFileSync("zip", ["-q", "-j", join(dir, "data-export.zip"), join(zipSrc, "conversations.json")]);
rmSync(zipSrc, { recursive: true });

// Noise that must be ignored
mkdirSync(join(dir, "random-folder"));
writeFileSync(join(dir, "notes.txt"), "hi");

test("detects unzipped + zipped exports and sniffs the right kind", () => {
  const found = detectExports(dir);
  const byOrigin = Object.fromEntries(found.map((f) => [f.origin.split("/").pop(), f]));

  assert.equal(found.length, 3);
  assert.equal(byOrigin["claude-export"]!.kind, "claude");
  assert.equal(byOrigin["chatgpt-export"]!.kind, "chatgpt");
  assert.equal(byOrigin["data-export.zip"]!.kind, "claude");
  assert.ok(byOrigin["data-export.zip"]!.cleanup, "zip extraction uses a temp dir");
  for (const f of found) if (f.cleanup) rmSync(f.cleanup, { recursive: true, force: true });
});

test("empty or missing search dir yields nothing", () => {
  assert.deepEqual(detectExports(join(dir, "random-folder")), []);
  assert.deepEqual(detectExports(join(dir, "does-not-exist")), []);
});

test("a corrupt zip is skipped, not crashed on, and the failure is surfaced (not silently swallowed)", () => {
  const corruptDir = mkdtempSync(join(tmpdir(), "setup-corrupt-"));
  try {
    writeFileSync(join(corruptDir, "corrupt.zip"), "this is not a real zip file");
    const original = console.error;
    const logged: string[] = [];
    console.error = (...args: unknown[]) => logged.push(args.join(" "));
    try {
      assert.deepEqual(detectExports(corruptDir), [], "corrupt zip excluded, not crashed on");
    } finally {
      console.error = original;
    }
    assert.ok(logged.some((l) => l.includes("corrupt.zip")), "the read failure is surfaced, not silently swallowed");
  } finally {
    rmSync(corruptDir, { recursive: true, force: true });
  }
});

// ── density floor ──

test("isThin thresholds", async () => {
  const { isThin } = await import("../src/setup.js");
  assert.equal(isThin(0), true);
  assert.equal(isThin(14), true);
  assert.equal(isThin(15), false);
});

test("eventsFromAnswers without engine splits phrases deterministically", async () => {
  const { eventsFromAnswers } = await import("../src/setup.js");
  const events = await eventsFromAnswers(
    ["building a local-first context engine, robotics", "rust and embedded systems"],
    null,
  );
  const topics = events.map((e) => (e.payload as { topic: string }).topic);
  assert.deepEqual(topics, ["building a local-first context engine", "robotics", "rust", "embedded systems"]);
  assert.equal(events[0]!.source, "cli");
  assert.deepEqual(events[0]!.provenance, { kind: "local", surface: "cli" });
});

test("eventsFromAnswers with engine extracts via LLM and validates", async () => {
  const { eventsFromAnswers } = await import("../src/setup.js");
  const events = await eventsFromAnswers(["working on persnally"], {
    model: "mock",
    label: "mock",
    extract: async () => ({
      topics: [{ topic: "persnally", weight: 0.9, intent: "building", sentiment: "positive", depth: "deep", category: "technology", entities: [] }],
    }),
  });
  assert.equal(events.length, 1);
  assert.equal((events[0]!.payload as { topic: string }).topic, "persnally");
});

test("eventsFromAnswers yields nothing for empty/punctuation answers", async () => {
  const { eventsFromAnswers } = await import("../src/setup.js");
  assert.deepEqual(await eventsFromAnswers(["", "  ...  "], null), []);
});
