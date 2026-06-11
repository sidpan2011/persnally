import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { parseClaudeCodeTranscripts } from "../src/importers/claude-code.js";

const root = mkdtempSync(join(tmpdir(), "claude-code-"));
after(() => rmSync(root, { recursive: true, force: true }));

const user = (text: unknown, extra: Record<string, unknown> = {}) => ({
  type: "user",
  message: { role: "user", content: text },
  timestamp: "2026-06-01T10:00:00Z",
  sessionId: "s1",
  cwd: "/Users/dev/Projects/persnally",
  ...extra,
});
const lines = (...entries: unknown[]) => entries.map((e) => JSON.stringify(e)).join("\n") + "\n";

const project = join(root, "-Users-dev-Projects-persnally");
mkdirSync(project);
writeFileSync(join(project, "session-a.jsonl"), lines(
  { type: "ai-title", aiTitle: "Fix the decay double-count", sessionId: "s1" },
  user("why does the topic weight grow unbounded?"),
  user([{ type: "text", text: "apply the fix" }, { type: "tool_use", id: "t1" }]),
  user("real question<system-reminder>injected harness text</system-reminder>"),
  user("<command-name>/clear</command-name>"),
  user("[Request interrupted by user]"),
  user("skip me", { isMeta: true }),
  user("agent chatter", { isSidechain: true }),
  user("tool output", { toolUseResult: { ok: true } }),
  { type: "assistant", message: { role: "assistant", content: "answer" } },
  { type: "file-history-snapshot", snapshot: {} },
) + "{truncated-crash-line");

writeFileSync(join(project, "session-thin.jsonl"), lines(
  user("only one message here", { sessionId: "thin" }),
));

writeFileSync(join(project, "session-b.jsonl"), lines(
  user("newer session, first message", { sessionId: "s2", timestamp: "2026-06-10T10:00:00Z" }),
  user("newer session, second message", { sessionId: "s2", timestamp: "2026-06-10T10:01:00Z" }),
));

test("keeps human prompts only and survives malformed tail lines", () => {
  const { parsed } = parseClaudeCodeTranscripts(root);
  const a = parsed.conversations.find((c) => c.uuid === "s1")!;
  assert.deepEqual(a.userMessages, [
    "why does the topic weight grow unbounded?",
    "apply the fix",
    "real question",
  ]);
});

test("names sessions from ai-title, falls back to cwd", () => {
  const { parsed } = parseClaudeCodeTranscripts(root);
  assert.equal(parsed.conversations.find((c) => c.uuid === "s1")!.name, "Fix the decay double-count");
  assert.equal(parsed.conversations.find((c) => c.uuid === "s2")!.name, "Claude Code session in persnally");
});

test("drops sessions below the message floor", () => {
  const { parsed, sessionsFound } = parseClaudeCodeTranscripts(root);
  assert.equal(sessionsFound, 2);
  assert.ok(!parsed.conversations.some((c) => c.uuid === "thin"));
});

test("caps to the most recent sessions and reports the drop", () => {
  const { parsed, sessionsFound, sessionsDropped } = parseClaudeCodeTranscripts(root, 1);
  assert.equal(sessionsFound, 2);
  assert.equal(sessionsDropped, 1);
  assert.deepEqual(parsed.conversations.map((c) => c.uuid), ["s2"]);
});

test("missing transcripts dir fails loudly", () => {
  assert.throws(() => parseClaudeCodeTranscripts(join(root, "nope")), /No Claude Code transcripts/);
});
