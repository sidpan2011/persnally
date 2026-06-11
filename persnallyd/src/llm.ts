/**
 * Structured extraction shared by importers and profile synthesis.
 * Uses output_config structured outputs (works on every current model,
 * including Fable 5 where forced tool_choice is not supported).
 */

import Anthropic from "@anthropic-ai/sdk";
import { zodOutputFormat } from "@anthropic-ai/sdk/helpers/zod";
import { z } from "zod";

export const DEFAULT_EXTRACT_MODEL = process.env.PERSNALLY_MODEL ?? "claude-haiku-4-5";
export const DEFAULT_PROFILE_MODEL = process.env.PERSNALLY_PROFILE_MODEL ?? "claude-fable-5";

export type LlmExtract = (opts: {
  model: string;
  instruction: string;
  schema: z.ZodType;
  content: string;
  maxTokens?: number;
}) => Promise<unknown>;

/** Default extractor backed by the Anthropic API; injectable for tests. */
export const anthropicExtract: LlmExtract = async ({ model, instruction, schema, content, maxTokens }) => {
  const client = new Anthropic();
  const response = await client.messages.parse({
    model,
    max_tokens: maxTokens ?? 4000,
    system: instruction,
    output_config: { format: zodOutputFormat(schema) },
    messages: [{ role: "user", content }],
  });
  if (response.stop_reason === "refusal") {
    throw new Error("Extraction request was refused by the model's safety classifiers");
  }
  if (response.parsed_output == null) {
    throw new Error("Extraction returned no parseable output");
  }
  return response.parsed_output;
};

// ── Local extraction via Ollama: zero key, zero cloud ───────

const OLLAMA_URL = process.env.PERSNALLY_OLLAMA_URL ?? "http://127.0.0.1:11434";
const LOCAL_MODEL_PREFERENCE = ["qwen2.5:14b", "qwen2.5:7b", "llama3.1:8b", "llama3.2", "qwen2.5:1.5b"];

export const ollamaExtract: LlmExtract = async ({ model, instruction, schema, content }) => {
  const r = await fetch(`${OLLAMA_URL}/api/chat`, {
    method: "POST",
    body: JSON.stringify({
      model,
      stream: false,
      format: z.toJSONSchema(schema),
      messages: [
        { role: "system", content: instruction },
        { role: "user", content },
      ],
    }),
  });
  if (!r.ok) throw new Error(`ollama: ${r.status} ${await r.text()}`);
  const body = (await r.json()) as { message?: { content?: string } };
  return schema.parse(JSON.parse(body.message?.content ?? "{}"));
};

async function localModel(): Promise<string | null> {
  if (process.env.PERSNALLY_LOCAL_MODEL) return process.env.PERSNALLY_LOCAL_MODEL;
  try {
    const r = await fetch(`${OLLAMA_URL}/api/tags`, { signal: AbortSignal.timeout(1500) });
    const tags = ((await r.json()) as { models?: { name: string }[] }).models?.map((m) => m.name) ?? [];
    return LOCAL_MODEL_PREFERENCE.find((p) => tags.some((t) => t === p || t === `${p}:latest`)) ?? tags[0] ?? null;
  } catch {
    return null;
  }
}

export interface ChosenExtractor {
  extract: LlmExtract;
  model: string;
  label: string;
}

/** Anthropic key wins (quality); otherwise local Ollama (privacy, zero setup); otherwise guide the user. */
export async function chooseExtractor(purpose: "extract" | "profile" = "extract"): Promise<ChosenExtractor> {
  if (process.env.ANTHROPIC_API_KEY) {
    const model = purpose === "profile" ? DEFAULT_PROFILE_MODEL : DEFAULT_EXTRACT_MODEL;
    return { extract: anthropicExtract, model, label: `${model} (Anthropic API)` };
  }
  const model = await localModel();
  if (model) {
    return { extract: ollamaExtract, model, label: `${model} (local via Ollama — nothing leaves this machine)` };
  }
  throw new Error(
    "No extraction engine available. Either:\n" +
    "  - persnallyd config set-key <sk-ant-…>   (Anthropic API, best quality), or\n" +
    "  - install Ollama and `ollama pull llama3.2`   (fully local, no key), or\n" +
    "  - start key-free with: persnallyd import git <path>",
  );
}
