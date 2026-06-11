/**
 * Claude data-export importer — the first event producer and the cold-start path.
 * parseClaudeExport is pure (testable offline); extractEvents does the LLM passes.
 * Phase 0 finding: memories.json and projects are the highest-signal-per-byte sources.
 */

import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { z } from "zod";
import { newEvent, uuidv7, PAYLOAD_SCHEMAS, type PersnallyEvent } from "../events.js";
import { anthropicExtract, DEFAULT_EXTRACT_MODEL, type LlmExtract } from "../llm.js";

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

export function parseClaudeExport(dir: string): ParsedExport {
  const convPath = join(dir, "conversations.json");
  if (!existsSync(convPath)) throw new Error(`No conversations.json in ${dir}`);

  const raw = JSON.parse(readFileSync(convPath, "utf-8")) as Array<Record<string, unknown>>;
  const conversations: ParsedConversation[] = raw.map((c) => ({
    uuid: String(c.uuid ?? ""),
    name: String(c.name ?? ""),
    summary: String(c.summary ?? ""),
    created_at: String(c.created_at ?? new Date().toISOString()),
    userMessages: ((c.chat_messages as Array<Record<string, unknown>>) ?? [])
      .filter((m) => m.sender === "human")
      .map((m) => (m.text ? String(m.text) : textFromContent(m.content)))
      .filter((t) => t.trim()),
  }));

  let memoryText = "";
  const memPath = join(dir, "memories.json");
  if (existsSync(memPath)) {
    const memories = JSON.parse(readFileSync(memPath, "utf-8")) as Array<Record<string, unknown>>;
    memoryText = memories.map((m) => String(m.conversations_memory ?? "")).join("\n");
  }

  const projects: ParsedExport["projects"] = [];
  const projDir = join(dir, "projects");
  if (existsSync(projDir)) {
    for (const f of readdirSync(projDir).filter((f) => f.endsWith(".json"))) {
      const p = JSON.parse(readFileSync(join(projDir, f), "utf-8")) as Record<string, unknown>;
      if (p.is_starter_project) continue;
      projects.push({ name: String(p.name ?? ""), description: String(p.description ?? "") });
    }
  }

  return { conversations, memoryText, projects };
}

function textFromContent(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content.map((c) => (c && typeof c === "object" ? String((c as Record<string, unknown>).text ?? "") : "")).join(" ");
  }
  return "";
}

const topicsExtraction = z.object({ topics: z.array(PAYLOAD_SCHEMAS["signal.topic"]) });
const assertionsExtraction = z.object({ assertions: z.array(PAYLOAD_SCHEMAS["signal.assertion"]) });

export interface ImportResult {
  events: PersnallyEvent[];
  batch: string;
  conversationsProcessed: number;
}

export async function extractEvents(
  parsed: ParsedExport,
  extract: LlmExtract = anthropicExtract,
  model = DEFAULT_EXTRACT_MODEL,
): Promise<ImportResult> {
  const batch = uuidv7();
  const events: PersnallyEvent[] = [];
  const source = "import:claude";

  for (const convo of parsed.conversations) {
    if (!convo.userMessages.length) continue;
    const text = convo.userMessages.join("\n").slice(0, MAX_CONVO_CHARS);
    const result = await extract({
      model,
      instruction: "Extract 1-5 topic signals from this conversation's user messages. Weight = centrality, depth = engagement level, sentiment = user's attitude toward the topic.",
      schema: topicsExtraction,
      content: `Conversation title: ${convo.name}\n\nUser messages:\n${text}`,
    });
    const { topics } = topicsExtraction.parse(result);
    for (const t of topics) {
      events.push(newEvent("signal.topic", source, t,
        { kind: "import", batch, file: "conversations.json", conversation_uuid: convo.uuid },
        new Date(convo.created_at).toISOString(),
      ));
    }
  }

  if (parsed.memoryText.trim() || parsed.projects.length) {
    const context = [
      parsed.memoryText.trim() && `Assistant's accumulated memory of the user:\n${parsed.memoryText}`,
      parsed.projects.length && `User-created projects:\n${parsed.projects.map((p) => `- ${p.name}: ${p.description}`).join("\n")}`,
    ].filter(Boolean).join("\n\n");
    const result = await extract({
      model,
      instruction: "Extract structured assertions about this person: facts, preferences, behaviors, skills, and context. Confidence reflects how directly the source supports the claim.",
      schema: assertionsExtraction,
      content: context,
    });
    const { assertions } = assertionsExtraction.parse(result);
    for (const a of assertions) {
      events.push(newEvent("signal.assertion", source, a, { kind: "import", batch, file: "memories.json" }));
    }
  }

  const span = parsed.conversations.map((c) => c.created_at).sort();
  events.push(newEvent("system.import", "system", {
    importer: "claude",
    batch,
    events: events.length,
    ...(span.length ? { source_span: [span[0]!, span[span.length - 1]!] } : {}),
  }, { kind: "import", batch, file: "conversations.json" }));

  return { events, batch, conversationsProcessed: parsed.conversations.length };
}

