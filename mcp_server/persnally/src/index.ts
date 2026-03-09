#!/usr/bin/env node

/**
 * Persnally MCP Server
 *
 * An AI-native personalized intelligence engine that learns from your conversations.
 *
 * How it works:
 * 1. You install this as an MCP server in Claude/ChatGPT
 * 2. As you chat, the AI calls `persnally_track` to note what you're interested in
 * 3. Persnally builds an interest graph locally (no raw messages stored)
 * 4. Daily/weekly, it curates a personalized digest and emails it via Resend
 *
 * Tools exposed:
 * - persnally_track: Track topics from the current conversation
 * - persnally_interests: View your current interest graph
 * - persnally_digest: Trigger a digest generation
 * - persnally_config: Configure email, frequency, preferences
 * - persnally_forget: Remove a topic or clear all data
 *
 * Privacy: Only structured signals are stored (topic, weight, category).
 * Raw conversations NEVER leave your machine. Fully open source.
 */

import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { InterestEngine, TopicSignal } from "./interest-engine.js";
import { DigestClient } from "./digest-client.js";

const engine = new InterestEngine();
const digestClient = new DigestClient();

const server = new McpServer({
  name: "persnally",
  version: "1.0.0",
});

// ============================================================
// TOOL: persnally_track
// This is the core tool. Claude calls this during/after conversations
// to report what topics the user is interested in.
//
// KEY INSIGHT: Claude IS the NLP engine. We don't need to parse
// conversations ourselves — Claude already understands the context
// and fills in structured data as tool parameters. Zero extra AI cost.
// ============================================================

server.tool(
  "persnally_track",
  `Track topics and interests from the current conversation to build a personalized intelligence profile.

Call this tool when the user discusses topics they care about. Extract the key themes, technologies, concepts, or interests from the conversation.

IMPORTANT GUIDELINES:
- Extract 1-5 topics per conversation, focusing on what the user is ACTIVELY engaged with
- Weight reflects how central this topic is to the conversation (0.1 = briefly mentioned, 1.0 = main focus)
- Depth: "mention" = just referenced, "moderate" = discussed in some detail, "deep" = extensive discussion or problem-solving
- Sentiment: "negative" means the user is frustrated with or dislikes the topic (e.g., "I hate CSS")
- Category should be one of: technology, business, finance, career, health, science, creative, education, lifestyle, news, other
- Entities are specific names: "Next.js" not "web framework", "YC" not "accelerator"

The user has explicitly opted in to having their conversation topics tracked for personalized content curation. No raw messages are stored — only structured topic signals.`,
  {
    topics: z.array(z.object({
      topic: z.string().describe("The topic or interest (e.g., 'SaaS pricing strategies', 'Rust async programming', 'index fund investing')"),
      weight: z.number().min(0).max(1).describe("How central this topic is to the conversation (0.1 = brief mention, 1.0 = main focus)"),
      intent: z.enum(["learning", "building", "researching", "deciding", "discussing", "debugging"]).describe("What the user is doing with this topic"),
      sentiment: z.enum(["positive", "negative", "neutral"]).describe("User's sentiment toward this topic"),
      depth: z.enum(["mention", "moderate", "deep"]).describe("How deeply the user engaged with this topic"),
      category: z.string().describe("Topic category: technology, business, finance, career, health, science, creative, education, lifestyle, news, other"),
      entities: z.array(z.string()).describe("Specific entities mentioned: tool names, company names, people, concepts"),
    })).describe("Array of topics extracted from the current conversation"),
  },
  async ({ topics }) => {
    const signals: TopicSignal[] = topics.map(t => ({
      ...t,
      timestamp: new Date().toISOString(),
    }));

    const result = engine.processSignals(signals);

    return {
      content: [{
        type: "text" as const,
        text: `Tracked ${result.tracked} topic(s): ${result.topics.join(", ")}.\n\nYour interest profile is being updated. These signals will help curate your personalized digest.`,
      }],
    };
  }
);

// ============================================================
// TOOL: persnally_interests
// Shows the user what Persnally knows about them
// ============================================================

server.tool(
  "persnally_interests",
  `Show the user's current interest profile — what Persnally has learned from their conversations.

Call this when the user asks about their profile, interests, or what Persnally knows about them. Also useful for transparency — users can see exactly what data is stored.`,
  {
    detail: z.enum(["summary", "full"]).optional().default("summary").describe("Level of detail to show"),
  },
  async ({ detail }) => {
    const stats = engine.getStats();

    if (stats.total_signals === 0) {
      return {
        content: [{
          type: "text" as const,
          text: "No interests tracked yet. As we chat about topics you care about, I'll build your personalized profile. You can also say \"track this\" during any conversation.",
        }],
      };
    }

    const interests = engine.getTopInterests(detail === "full" ? 30 : 10);
    const config = engine.getConfig();

    let text = `## Your Interest Profile\n\n`;
    text += `**${stats.active_topics}** active topics from **${stats.total_conversations}** conversations (${stats.total_signals} signals)\n`;
    text += `Tracking since: ${new Date(stats.data_since).toLocaleDateString()}\n`;
    text += `Digest email: ${config.email || "Not configured"}\n\n`;

    // Group by category
    const byCategory: Record<string, typeof interests> = {};
    for (const interest of interests) {
      const cat = interest.category;
      if (!byCategory[cat]) byCategory[cat] = [];
      byCategory[cat].push(interest);
    }

    for (const [category, items] of Object.entries(byCategory)) {
      text += `### ${category.charAt(0).toUpperCase() + category.slice(1)}\n`;
      for (const item of items) {
        const weightBar = "█".repeat(Math.round(item.current_weight * 5)) + "░".repeat(5 - Math.round(item.current_weight * 5));
        const sentiment = item.sentiment_balance > 0.2 ? "+" : item.sentiment_balance < -0.2 ? "-" : "~";
        text += `- ${item.topic} [${weightBar}] (${item.dominant_intent}, ${sentiment}) — ${item.frequency}x\n`;
        if (detail === "full" && item.entities.length > 0) {
          text += `  Entities: ${item.entities.slice(0, 5).join(", ")}\n`;
        }
      }
      text += "\n";
    }

    return { content: [{ type: "text" as const, text }] };
  }
);

// ============================================================
// TOOL: persnally_digest
// Generates the interest summary for digest curation
// ============================================================

server.tool(
  "persnally_digest",
  `Generate a digest request based on the user's interest profile.

This produces a structured summary of what the user cares about, balanced across categories, that can be sent to the Persnally curation API to generate a personalized email digest.

Call this when the user asks for their digest, or it can be triggered automatically.`,
  {
    preview: z.boolean().optional().default(false).describe("If true, show what the digest would contain without sending"),
  },
  async ({ preview }) => {
    const stats = engine.getStats();
    if (stats.total_signals === 0) {
      return {
        content: [{
          type: "text" as const,
          text: "Not enough data to generate a digest yet. Keep chatting and I'll track your interests!",
        }],
      };
    }

    const config = engine.getConfig();
    const balanced = engine.getBalancedInterests(config.max_items);
    const summary = engine.getGraphSummary();

    let text = "";

    if (preview) {
      text += `## Digest Preview\n\n`;
      text += `Based on your interest profile, here's what your next digest would cover:\n\n`;

      for (const [category, data] of Object.entries(balanced)) {
        text += `**${category}** (${data.allocation} items):\n`;
        for (const interest of data.interests) {
          text += `- ${interest.topic} (weight: ${interest.current_weight.toFixed(2)}, intent: ${interest.dominant_intent})\n`;
        }
        text += "\n";
      }

      if (!config.email) {
        text += `\n⚠️ No email configured. Use persnally_config to set your email address.`;
      }
    } else {
      // Build digest payload and send to API
      const digestPayload = {
        email: config.email,
        interest_graph: summary,
        balanced_allocation: Object.fromEntries(
          Object.entries(balanced).map(([cat, data]) => [
            cat,
            {
              allocation: data.allocation,
              topics: data.interests.map(i => ({
                topic: i.topic,
                weight: i.current_weight,
                intent: i.dominant_intent,
                entities: i.entities.slice(0, 5),
              })),
            },
          ])
        ),
        preferences: {
          max_items: config.max_items,
          frequency: config.frequency,
        },
      };

      if (!config.email) {
        text += `Cannot send digest — no email configured. Use persnally_config to set your email.\n\n`;
        text += `Here's what would be sent:\n${JSON.stringify(digestPayload, null, 2)}`;
      } else {
        // Send to API
        const result = await digestClient.requestDigest(digestPayload);
        if (result) {
          text += `Digest requested! Job ID: ${result.job_id} (status: ${result.status})\n\n`;
          text += `Your personalized digest is being generated and will be sent to ${config.email}.\n`;
          text += `It includes ${stats.active_topics} topics across ${Object.keys(balanced).length} categories.`;
        } else {
          text += `Digest generation is not configured (no API key set).\n\n`;
          text += `To enable automatic digest emails:\n`;
          text += `1. Set PERSNALLY_API_KEY in your environment, or\n`;
          text += `2. Configure api_key via persnally_config\n\n`;
          text += `Your interest data (shown below) is ready for when you connect:\n`;
          text += JSON.stringify(digestPayload, null, 2);
        }
      }
    }

    return { content: [{ type: "text" as const, text }] };
  }
);

// ============================================================
// TOOL: persnally_config
// Configure email, frequency, preferences
// ============================================================

server.tool(
  "persnally_config",
  `Configure Persnally settings — email address, digest frequency, and preferences.

Call this when the user wants to set up or change their Persnally configuration. The email address is required for receiving digests.`,
  {
    email: z.string().email().optional().describe("Email address for receiving digests"),
    frequency: z.enum(["daily", "weekly"]).optional().describe("How often to receive digests"),
    max_items: z.number().min(3).max(15).optional().describe("Maximum items per digest (3-15)"),
    api_key: z.string().optional().describe("API key for Persnally cloud digest generation"),
    api_url: z.string().optional().describe("Custom API URL (default: https://api.persnally.com)"),
  },
  async ({ email, frequency, max_items, api_key, api_url }) => {
    const updates: Record<string, unknown> = {};
    if (email) updates.email = email;
    if (frequency) updates.frequency = frequency;
    if (max_items) updates.max_items = max_items;
    if (api_key) updates.api_key = api_key;
    if (api_url) updates.api_url = api_url;

    const config = engine.updateConfig(updates);

    let text = `Configuration updated:\n`;
    text += `- Email: ${config.email || "Not set"}\n`;
    text += `- Frequency: ${config.frequency}\n`;
    text += `- Max items per digest: ${config.max_items}\n`;

    if (!config.email) {
      text += `\n⚠️ Please set your email to start receiving digests.`;
    }

    return { content: [{ type: "text" as const, text }] };
  }
);

// ============================================================
// TOOL: persnally_forget
// Privacy control — remove topics or clear all data
// ============================================================

server.tool(
  "persnally_forget",
  `Remove a specific topic from the interest graph, or clear all data.

Call this when the user wants to remove a tracked topic or reset their entire profile. This is a privacy control — users should always be able to delete their data.`,
  {
    topic: z.string().optional().describe("Specific topic to remove. Omit to clear everything."),
    clear_all: z.boolean().optional().default(false).describe("If true, clear ALL tracked data"),
  },
  async ({ topic, clear_all }) => {
    if (clear_all) {
      engine.clearAll();
      return {
        content: [{
          type: "text" as const,
          text: "All data cleared. Your interest profile has been reset. Persnally will start fresh from your next conversation.",
        }],
      };
    }

    if (topic) {
      const removed = engine.removeTopic(topic);
      if (removed) {
        return {
          content: [{
            type: "text" as const,
            text: `Removed "${topic}" from your interest profile. It won't appear in future digests.`,
          }],
        };
      } else {
        return {
          content: [{
            type: "text" as const,
            text: `Topic "${topic}" not found in your profile. Use persnally_interests to see what's tracked.`,
          }],
        };
      }
    }

    return {
      content: [{
        type: "text" as const,
        text: "Please specify a topic to remove, or set clear_all to true to reset everything.",
      }],
    };
  }
);

// ============================================================
// RESOURCES: Interest graph as a readable resource
// ============================================================

server.resource(
  "interest-graph",
  "persnally://interest-graph",
  async (uri) => ({
    contents: [{
      uri: uri.href,
      mimeType: "application/json",
      text: JSON.stringify(engine.getGraphSummary(), null, 2),
    }],
  })
);

// ============================================================
// START SERVER
// ============================================================

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Persnally MCP server running");
}

main().catch(console.error);
