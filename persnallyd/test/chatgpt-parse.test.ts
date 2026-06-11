import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { parseChatGPTExport } from "../src/importers/chatgpt.js";

const dir = mkdtempSync(join(tmpdir(), "chatgpt-export-"));
after(() => rmSync(dir, { recursive: true, force: true }));

writeFileSync(join(dir, "conversations.json"), JSON.stringify([
  {
    conversation_id: "c1",
    title: "Debugging asyncio",
    create_time: 1767225600, // 2026-01-01
    mapping: {
      root: { message: undefined },
      a: { message: { author: { role: "user" }, content: { content_type: "text", parts: ["why does gather hang"] }, create_time: 2 } },
      b: { message: { author: { role: "assistant" }, content: { content_type: "text", parts: ["because..."] }, create_time: 3 } },
      c: { message: { author: { role: "user" }, content: { content_type: "multimodal_text", parts: [{ image: "..." }, "and this screenshot"] }, create_time: 1 } },
      d: { message: { author: { role: "system" }, content: { content_type: "text", parts: ["hidden"] }, create_time: 0 } },
    },
  },
]));

test("parses user messages only, in time order, skipping non-string parts", () => {
  const parsed = parseChatGPTExport(dir);
  assert.equal(parsed.conversations.length, 1);
  const c = parsed.conversations[0]!;
  assert.equal(c.uuid, "c1");
  assert.equal(c.name, "Debugging asyncio");
  assert.equal(c.created_at, "2026-01-01T00:00:00.000Z");
  assert.deepEqual(c.userMessages, ["and this screenshot", "why does gather hang"]);
});

test("accepts a direct conversations.json path and fails loudly otherwise", () => {
  assert.equal(parseChatGPTExport(join(dir, "conversations.json")).conversations.length, 1);
  assert.throws(() => parseChatGPTExport(join(dir, "nope.json")));
});
