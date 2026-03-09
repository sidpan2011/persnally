/**
 * Interest Engine — The core intelligence layer.
 *
 * Manages a local interest graph that evolves over time.
 * Key design decisions:
 *
 * 1. DECAY: Interests lose weight over time. Last week's Kubernetes deep-dive
 *    shouldn't dominate forever. Half-life = 7 days.
 *
 * 2. DEPTH vs FREQUENCY: A 2-hour conversation about Rust > 10 one-liners about it.
 *    We track both "mentions" and "depth" separately.
 *
 * 3. INTENT MATTERS: "I hate React" shouldn't boost React. We track sentiment.
 *    Negative sentiment = deprioritize, not remove.
 *
 * 4. CATEGORIES: Topics are classified into domains so we can balance the digest.
 *    A user interested in tech + finance should get both, not just whichever has more signal.
 *
 * 5. NO RAW MESSAGES: We only store structured signals. Privacy by architecture.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";
import { homedir } from "os";

// ============================================================
// TYPES
// ============================================================

export interface TopicSignal {
  topic: string;
  weight: number; // 0-1 how important in this conversation
  intent: "learning" | "building" | "researching" | "deciding" | "discussing" | "debugging";
  sentiment: "positive" | "negative" | "neutral";
  depth: "mention" | "moderate" | "deep"; // how deeply they engaged
  category: string; // technology, business, finance, career, health, etc.
  entities: string[]; // specific things: "Next.js", "S&P 500", "YC"
  timestamp: string;
}

export interface InterestNode {
  topic: string;
  category: string;
  // Aggregated scores
  current_weight: number; // decayed weight
  raw_weight: number; // sum of all signals
  frequency: number; // how many times mentioned
  avg_depth: number; // average depth score
  dominant_intent: string;
  sentiment_balance: number; // -1 to 1
  // Tracking
  first_seen: string;
  last_seen: string;
  entities: string[]; // unique entities associated
  signals: number; // total signal count
}

export interface InterestGraph {
  user_email: string;
  created_at: string;
  updated_at: string;
  nodes: Record<string, InterestNode>;
  // Summary stats
  total_signals: number;
  total_conversations: number;
  top_categories: Record<string, number>;
}

export interface DigestPreferences {
  email: string;
  frequency: "daily" | "weekly";
  max_items: number;
  categories_enabled: string[]; // empty = all
  quiet_hours: { start: number; end: number }; // 22-7 = no emails 10pm-7am
}

// ============================================================
// CONSTANTS
// ============================================================

const DEPTH_SCORES: Record<string, number> = {
  mention: 0.3,
  moderate: 0.6,
  deep: 1.0,
};

const HALF_LIFE_DAYS = 7; // Interest weight halves every 7 days
const DECAY_FACTOR = Math.LN2 / HALF_LIFE_DAYS;

const DATA_DIR = join(homedir(), ".persnally");
const GRAPH_FILE = join(DATA_DIR, "interest-graph.json");
const CONFIG_FILE = join(DATA_DIR, "config.json");

// ============================================================
// INTEREST ENGINE
// ============================================================

export class InterestEngine {
  private graph: InterestGraph;
  private config: DigestPreferences;

  constructor() {
    this.ensureDataDir();
    this.graph = this.loadGraph();
    this.config = this.loadConfig();
  }

  // ──────────────────────────────────────────
  // SIGNAL PROCESSING
  // ──────────────────────────────────────────

  /**
   * Process a batch of signals from a conversation.
   * This is called when Claude invokes the persnally_track tool.
   */
  processSignals(signals: TopicSignal[]): { tracked: number; topics: string[] } {
    const trackedTopics: string[] = [];

    for (const signal of signals) {
      const key = this.normalizeKey(signal.topic);
      if (!key) continue;

      if (this.graph.nodes[key]) {
        this.updateNode(this.graph.nodes[key], signal);
      } else {
        this.graph.nodes[key] = this.createNode(signal);
      }
      trackedTopics.push(signal.topic);
    }

    this.graph.total_signals += signals.length;
    this.graph.total_conversations += 1;
    this.graph.updated_at = new Date().toISOString();
    this.recalculateCategories();
    this.save();

    return { tracked: trackedTopics.length, topics: trackedTopics };
  }

  private createNode(signal: TopicSignal): InterestNode {
    const depthScore = DEPTH_SCORES[signal.depth] || 0.3;
    return {
      topic: signal.topic,
      category: signal.category,
      current_weight: signal.weight * depthScore,
      raw_weight: signal.weight * depthScore,
      frequency: 1,
      avg_depth: depthScore,
      dominant_intent: signal.intent,
      sentiment_balance: signal.sentiment === "positive" ? 0.5 :
                         signal.sentiment === "negative" ? -0.5 : 0,
      first_seen: signal.timestamp,
      last_seen: signal.timestamp,
      entities: [...new Set(signal.entities)],
      signals: 1,
    };
  }

  private updateNode(node: InterestNode, signal: TopicSignal): void {
    const depthScore = DEPTH_SCORES[signal.depth] || 0.3;
    const signalWeight = signal.weight * depthScore;

    node.raw_weight += signalWeight;
    node.frequency += 1;
    node.signals += 1;
    node.avg_depth = (node.avg_depth * (node.signals - 1) + depthScore) / node.signals;
    node.last_seen = signal.timestamp;

    // Update sentiment balance (running average)
    const sentimentValue = signal.sentiment === "positive" ? 0.5 :
                           signal.sentiment === "negative" ? -0.5 : 0;
    node.sentiment_balance = (node.sentiment_balance * (node.signals - 1) + sentimentValue) / node.signals;

    // Update dominant intent (most frequent)
    node.dominant_intent = signal.intent;

    // Merge entities
    const entitySet = new Set(node.entities);
    signal.entities.forEach(e => entitySet.add(e));
    node.entities = [...entitySet].slice(0, 20); // cap at 20

    // Recalculate decayed weight
    node.current_weight = this.calculateDecayedWeight(node);
  }

  // ──────────────────────────────────────────
  // DECAY & WEIGHTING
  // ──────────────────────────────────────────

  private calculateDecayedWeight(node: InterestNode): number {
    const now = Date.now();
    const lastSeen = new Date(node.last_seen).getTime();
    const daysSinceLastSeen = (now - lastSeen) / (1000 * 60 * 60 * 24);

    // Exponential decay based on last seen
    const decayMultiplier = Math.exp(-DECAY_FACTOR * daysSinceLastSeen);

    // Frequency bonus: more mentions = slower decay
    const frequencyBonus = Math.min(Math.log2(node.frequency + 1) / 3, 0.5);

    // Depth bonus: deeper engagement = stronger signal
    const depthBonus = node.avg_depth * 0.3;

    // Sentiment penalty: negative sentiment reduces weight
    const sentimentMultiplier = node.sentiment_balance < -0.3 ? 0.3 :
                                 node.sentiment_balance < 0 ? 0.7 : 1.0;

    const weight = node.raw_weight * decayMultiplier * sentimentMultiplier + frequencyBonus + depthBonus;
    return Math.min(Math.max(weight, 0), 10); // cap at 10
  }

  // ──────────────────────────────────────────
  // INTEREST GRAPH QUERIES
  // ──────────────────────────────────────────

  /**
   * Get the current interest graph, sorted by weight.
   * Used by the digest generator to know what to curate.
   */
  getTopInterests(limit: number = 20): InterestNode[] {
    // Recalculate all weights with decay
    for (const node of Object.values(this.graph.nodes)) {
      node.current_weight = this.calculateDecayedWeight(node);
    }

    return Object.values(this.graph.nodes)
      .filter(n => n.current_weight > 0.05) // prune near-zero interests
      .sort((a, b) => b.current_weight - a.current_weight)
      .slice(0, limit);
  }

  /**
   * Get interests grouped by category for balanced digest generation.
   * Returns proportional allocation: if 60% tech, 30% business, 10% finance,
   * a 10-item digest should have ~6 tech, 3 business, 1 finance.
   */
  getBalancedInterests(totalItems: number = 7): Record<string, { interests: InterestNode[]; allocation: number }> {
    const allInterests = this.getTopInterests(50);
    const categoryWeights: Record<string, number> = {};

    for (const interest of allInterests) {
      const cat = interest.category;
      categoryWeights[cat] = (categoryWeights[cat] || 0) + interest.current_weight;
    }

    const totalWeight = Object.values(categoryWeights).reduce((a, b) => a + b, 0) || 1;
    const result: Record<string, { interests: InterestNode[]; allocation: number }> = {};

    for (const [cat, weight] of Object.entries(categoryWeights)) {
      const rawAllocation = (weight / totalWeight) * totalItems;
      // Every category with signal gets at least 1 item
      const allocation = Math.max(1, Math.round(rawAllocation));
      const catInterests = allInterests
        .filter(i => i.category === cat)
        .slice(0, allocation * 2); // give 2x candidates for quality selection

      result[cat] = { interests: catInterests, allocation };
    }

    return result;
  }

  /**
   * Get a summary suitable for sending to the curation API.
   * This is what gets synced — no raw conversations, just the graph.
   */
  getGraphSummary(): {
    topics: Array<{ topic: string; weight: number; category: string; intent: string; entities: string[] }>;
    categories: Record<string, number>;
    total_signals: number;
  } {
    const interests = this.getTopInterests(30);
    return {
      topics: interests.map(n => ({
        topic: n.topic,
        weight: Math.round(n.current_weight * 100) / 100,
        category: n.category,
        intent: n.dominant_intent,
        entities: n.entities.slice(0, 5),
      })),
      categories: this.graph.top_categories,
      total_signals: this.graph.total_signals,
    };
  }

  // ──────────────────────────────────────────
  // CONFIGURATION
  // ──────────────────────────────────────────

  getConfig(): DigestPreferences {
    return this.config;
  }

  updateConfig(updates: Partial<DigestPreferences>): DigestPreferences {
    this.config = { ...this.config, ...updates };
    this.saveConfig();
    return this.config;
  }

  getStats(): {
    total_topics: number;
    total_signals: number;
    total_conversations: number;
    active_topics: number;
    top_categories: Record<string, number>;
    data_since: string;
  } {
    const activeTopics = Object.values(this.graph.nodes)
      .filter(n => this.calculateDecayedWeight(n) > 0.05).length;

    return {
      total_topics: Object.keys(this.graph.nodes).length,
      total_signals: this.graph.total_signals,
      total_conversations: this.graph.total_conversations,
      active_topics: activeTopics,
      top_categories: this.graph.top_categories,
      data_since: this.graph.created_at,
    };
  }

  /**
   * Remove a topic from the graph (user requested).
   */
  removeTopic(topic: string): boolean {
    const key = this.normalizeKey(topic);
    if (key && this.graph.nodes[key]) {
      delete this.graph.nodes[key];
      this.recalculateCategories();
      this.save();
      return true;
    }
    return false;
  }

  /**
   * Clear all data.
   */
  clearAll(): void {
    this.graph = this.emptyGraph();
    this.save();
  }

  // ──────────────────────────────────────────
  // PERSISTENCE
  // ──────────────────────────────────────────

  private ensureDataDir(): void {
    if (!existsSync(DATA_DIR)) {
      mkdirSync(DATA_DIR, { recursive: true });
    }
  }

  private loadGraph(): InterestGraph {
    try {
      if (existsSync(GRAPH_FILE)) {
        const data = readFileSync(GRAPH_FILE, "utf-8");
        return JSON.parse(data);
      }
    } catch (e) {
      console.error("Failed to load interest graph, starting fresh:", e);
    }
    return this.emptyGraph();
  }

  private emptyGraph(): InterestGraph {
    return {
      user_email: "",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      nodes: {},
      total_signals: 0,
      total_conversations: 0,
      top_categories: {},
    };
  }

  private save(): void {
    try {
      writeFileSync(GRAPH_FILE, JSON.stringify(this.graph, null, 2));
    } catch (e) {
      console.error("Failed to save interest graph:", e);
    }
  }

  private loadConfig(): DigestPreferences {
    try {
      if (existsSync(CONFIG_FILE)) {
        const data = readFileSync(CONFIG_FILE, "utf-8");
        return JSON.parse(data);
      }
    } catch (e) {
      console.error("Failed to load config:", e);
    }
    return {
      email: "",
      frequency: "daily",
      max_items: 7,
      categories_enabled: [],
      quiet_hours: { start: 22, end: 7 },
    };
  }

  private saveConfig(): void {
    try {
      writeFileSync(CONFIG_FILE, JSON.stringify(this.config, null, 2));
    } catch (e) {
      console.error("Failed to save config:", e);
    }
  }

  // ──────────────────────────────────────────
  // HELPERS
  // ──────────────────────────────────────────

  private normalizeKey(topic: string): string {
    return topic.toLowerCase().trim().replace(/[^a-z0-9\s\-\.\/\+#]/g, "").replace(/\s+/g, "_");
  }

  private recalculateCategories(): void {
    const cats: Record<string, number> = {};
    for (const node of Object.values(this.graph.nodes)) {
      const weight = this.calculateDecayedWeight(node);
      if (weight > 0.05) {
        cats[node.category] = (cats[node.category] || 0) + weight;
      }
    }
    this.graph.top_categories = cats;
  }
}
