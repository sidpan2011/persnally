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
