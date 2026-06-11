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
