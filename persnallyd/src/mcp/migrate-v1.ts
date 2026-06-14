/**
 * One-time migration of the v1 aggregated interest graph into the event store.
 * v1 nodes are lossy aggregates, so each becomes a single representative
 * signal.topic event; the original file is renamed, never deleted.
 */

import { existsSync, readFileSync, renameSync } from "fs";
import { homedir } from "os";
import { join } from "path";
import { safeIso } from "../events.js";
import { daemonPost } from "./daemon-client.js";

const GRAPH_FILE = join(homedir(), ".persnally", "interest-graph.json");

interface V1Node {
  topic: string;
  category: string;
  current_weight: number;
  avg_depth: number;
  dominant_intent: string;
  sentiment_balance: number;
  last_seen: string;
  entities: string[];
}

const INTENTS = new Set(["learning", "building", "researching", "deciding", "discussing", "debugging"]);
const CATEGORIES = new Set([
  "technology", "business", "finance", "career", "health",
  "science", "creative", "education", "lifestyle", "news", "other",
]);

export async function migrateV1Graph(): Promise<number> {
  if (!existsSync(GRAPH_FILE)) return 0;

  let nodes: Record<string, V1Node>;
  try {
    nodes = JSON.parse(readFileSync(GRAPH_FILE, "utf-8")).nodes ?? {};
  } catch {
    // Corrupt v1 file — move it aside so we don't reparse it on every session.
    try { renameSync(GRAPH_FILE, GRAPH_FILE + ".v1-corrupt"); } catch { /* leave it */ }
    return 0;
  }
  const entries = Object.values(nodes);

  if (entries.length > 0) {
    const batch = `v1-migration-${Date.now()}`;
    const events = entries.map((n) => ({
      type: "signal.topic",
      source: "system",
      ts: safeIso(n.last_seen),
      payload: {
        topic: n.topic,
        weight: Math.min(Math.max(n.current_weight, 0.05), 1),
        intent: INTENTS.has(n.dominant_intent) ? n.dominant_intent : "discussing",
        sentiment: n.sentiment_balance > 0.2 ? "positive" : n.sentiment_balance < -0.2 ? "negative" : "neutral",
        depth: n.avg_depth >= 0.8 ? "deep" : n.avg_depth >= 0.45 ? "moderate" : "mention",
        category: CATEGORIES.has(n.category) ? n.category : "other",
        entities: (n.entities ?? []).slice(0, 20),
      },
      provenance: { kind: "import", batch, file: "interest-graph.json" },
    }));
    await daemonPost("/events", events);
  }

  renameSync(GRAPH_FILE, GRAPH_FILE + ".v1-migrated");
  return entries.length;
}
