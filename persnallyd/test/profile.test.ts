import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";
import { newEvent } from "../src/events.js";
import { synthesizeProfile } from "../src/profile.js";
import { EventStore } from "../src/store.js";

const dir = mkdtempSync(join(tmpdir(), "profile-test-"));
const store = new EventStore(join(dir, "test.db"));
after(() => { store.close(); rmSync(dir, { recursive: true, force: true }); });

test("synthesize fails loudly on an empty store", async () => {
  await assert.rejects(() => synthesizeProfile(store, async () => ({})), /Nothing to synthesize/);
});

test("synthesizes, persists, and round-trips a profile with evidence ids", async () => {
  const topicEvent = newEvent("signal.topic", "import:claude", {
    topic: "event sourcing", weight: 0.9, intent: "building", sentiment: "positive",
    depth: "deep", category: "technology", entities: ["SQLite"],
  }, { kind: "import", batch: "b1", file: "conversations.json" });
  const assertionEvent = newEvent("signal.assertion", "import:claude", {
    claim: "solo founder", kind: "context", confidence: 0.9, evidence: "memory",
  }, { kind: "import", batch: "b1", file: "memories.json" });
  store.append([topicEvent, assertionEvent]);
  store.rebuild();

  let seenContent = "";
  const profile = await synthesizeProfile(store, async ({ content }) => {
    seenContent = content;
    return {
      headline: "A builder",
      sections: [{ title: "Work", body: "Builds things.", evidence_event_ids: [assertionEvent.id] }],
    };
  });

  assert.match(seenContent, /event sourcing/);
  assert.match(seenContent, /solo founder/);
  assert.match(seenContent, new RegExp(assertionEvent.id));

  const stored = store.getProfile();
  assert.equal(stored?.headline, "A builder");
  assert.deepEqual(stored?.sections[0]?.evidence_event_ids, [assertionEvent.id]);
});

test("malformed LLM output is rejected, leaving the stored profile intact", async () => {
  await assert.rejects(() => synthesizeProfile(store, async () => ({ headline: "", sections: [] })));
  assert.equal(store.getProfile()?.headline, "A builder");
});
