/**
 * Shared extraction pipeline for conversation-export importers.
 * Parsers produce a ParsedExport; this turns it into provenance-linked events.
 */

import { z } from "zod";
import { newEvent, safeIso, uuidv7, PAYLOAD_SCHEMAS, type PersnallyEvent } from "../events.js";
import { anthropicExtract, DEFAULT_EXTRACT_MODEL, type LlmExtract } from "../llm.js";
import { proseLines, stripNoise } from "../prose.js";
import { analyzeVoice } from "../stylometry.js";

const MAX_CONVO_CHARS = 30_000;

export interface ParsedConversation {
  uuid: string;
  name: string;
  summary: string;
  created_at: string;
  userMessages: string[];
}

export interface ParsedExport {
  conversations: ParsedConversation[];
  memoryText: string;
  projects: { name: string; description: string }[];
}

export interface ImportResult {
  events: PersnallyEvent[];
  batch: string;
  conversationsProcessed: number;
}

const topicsExtraction = z.object({ topics: z.array(PAYLOAD_SCHEMAS["signal.topic"]) });
const assertionsExtraction = z.object({ assertions: z.array(PAYLOAD_SCHEMAS["signal.assertion"]) });

export async function extractEvents(
  parsed: ParsedExport,
  opts: { source: string; importer: string; file: string },
  extract: LlmExtract = anthropicExtract,
  model = DEFAULT_EXTRACT_MODEL,
): Promise<ImportResult> {
  const batch = uuidv7();
  const events: PersnallyEvent[] = [];
  const voiceCorpus: string[] = []; // clean prose for the deterministic voice fingerprint

  for (const convo of parsed.conversations) {
    if (!convo.userMessages.length) continue;
    const joined = convo.userMessages.join("\n");
    voiceCorpus.push(...proseLines(joined)); // prose feeds the deterministic voice fingerprint even if topic extraction fails
    const text = stripNoise(joined).slice(0, MAX_CONVO_CHARS); // strip pasted paths/URLs/logs before the LLM sees it
    if (!text) continue;
    try {
      const result = await extract({
        model,
        instruction:
          "Extract 1-5 topic signals from this conversation's user messages. Weight = centrality, depth = engagement level, sentiment = user's attitude toward the topic. Capture decisions and rejected options as their own signals.",
        schema: topicsExtraction,
        content: `Conversation title: ${convo.name}\n\nUser messages:\n${text}`,
      });
      const { topics } = topicsExtraction.parse(result);
      for (const t of topics) {
        events.push(newEvent("signal.topic", opts.source, t,
          { kind: "import", batch, file: opts.file, conversation_uuid: convo.uuid },
          safeIso(convo.created_at),
        ));
      }
    } catch (e) {
      // One malformed extraction (e.g. the model returns an out-of-enum value)
      // must not abort a whole multi-conversation import. Skip it — leaving no
      // conversation_uuid marker, so the next pass retries it — and keep the rest.
      console.error(`extract: skipped "${convo.name}" — ${(e instanceof Error ? e.message : String(e)).split("\n")[0]}`);
    }
  }

  if (parsed.memoryText.trim() || parsed.projects.length) {
    const context = [
      parsed.memoryText.trim() && `Assistant's accumulated memory of the user:\n${parsed.memoryText}`,
      parsed.projects.length && `User-created projects:\n${parsed.projects.map((p) => `- ${p.name}: ${p.description}`).join("\n")}`,
    ].filter(Boolean).join("\n\n");
    try {
      const result = await extract({
        model,
        instruction:
          "Extract structured assertions about this person: facts, preferences, behaviors, skills, and context. Confidence reflects how directly the source supports the claim.",
        schema: assertionsExtraction,
        content: context,
      });
      const { assertions } = assertionsExtraction.parse(result);
      for (const a of assertions) {
        events.push(newEvent("signal.assertion", opts.source, a, { kind: "import", batch, file: opts.file }));
      }
    } catch (e) {
      // A malformed assertions response shouldn't discard the topics already gathered.
      console.error(`extract: skipped memory/projects assertions — ${(e instanceof Error ? e.message : String(e)).split("\n")[0]}`);
    }
  }

  // Deterministic voice fingerprint over the user's own prose — no LLM, no tokens.
  for (const s of analyzeVoice(voiceCorpus).signals) {
    events.push(newEvent("signal.style", opts.source, s, { kind: "import", batch, file: opts.file }));
  }

  const span = parsed.conversations.map((c) => c.created_at).sort();
  events.push(newEvent("system.import", "system", {
    importer: opts.importer,
    batch,
    events: events.length,
    ...(span.length ? { source_span: [span[0]!, span[span.length - 1]!] } : {}),
  }, { kind: "import", batch, file: opts.file }));

  return { events, batch, conversationsProcessed: parsed.conversations.length };
}
