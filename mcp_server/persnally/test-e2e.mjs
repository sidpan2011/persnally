#!/usr/bin/env node
/**
 * End-to-end test for Persnally MCP server.
 * Simulates what Claude would do: track topics across multiple "conversations",
 * then check the interest graph and generate a digest payload.
 */

import { InterestEngine } from "./build/interest-engine.js";

const engine = new InterestEngine();

console.log("=== PERSNALLY E2E TEST ===\n");

// ── Simulate Conversation 1: User discussing Rust async programming ──
console.log("📝 Conversation 1: Rust async programming");
const r1 = engine.processSignals([
  {
    topic: "Rust async programming",
    weight: 0.9,
    intent: "building",
    sentiment: "positive",
    depth: "deep",
    category: "technology",
    entities: ["tokio", "async/await", "Rust"],
    timestamp: new Date().toISOString(),
  },
  {
    topic: "systems programming",
    weight: 0.5,
    intent: "discussing",
    sentiment: "positive",
    depth: "moderate",
    category: "technology",
    entities: ["memory safety", "zero-cost abstractions"],
    timestamp: new Date().toISOString(),
  },
]);
console.log(`   Tracked: ${r1.tracked} topics (${r1.topics.join(", ")})\n`);

// ── Simulate Conversation 2: User exploring AI/ML ──
console.log("📝 Conversation 2: AI/ML exploration");
const r2 = engine.processSignals([
  {
    topic: "LLM fine-tuning",
    weight: 0.8,
    intent: "learning",
    sentiment: "positive",
    depth: "deep",
    category: "technology",
    entities: ["Claude", "LoRA", "Hugging Face"],
    timestamp: new Date().toISOString(),
  },
  {
    topic: "AI startup ideas",
    weight: 0.6,
    intent: "researching",
    sentiment: "positive",
    depth: "moderate",
    category: "business",
    entities: ["YC", "seed funding", "AI agents"],
    timestamp: new Date().toISOString(),
  },
]);
console.log(`   Tracked: ${r2.tracked} topics (${r2.topics.join(", ")})\n`);

// ── Simulate Conversation 3: User mentions CSS (negative sentiment) ──
console.log("📝 Conversation 3: CSS frustration");
const r3 = engine.processSignals([
  {
    topic: "CSS layout",
    weight: 0.4,
    intent: "debugging",
    sentiment: "negative",
    depth: "moderate",
    category: "technology",
    entities: ["flexbox", "grid"],
    timestamp: new Date().toISOString(),
  },
]);
console.log(`   Tracked: ${r3.tracked} topics (${r3.topics.join(", ")})\n`);

// ── Simulate Conversation 4: Second mention of Rust (should boost it) ──
console.log("📝 Conversation 4: More Rust (reinforcement)");
const r4 = engine.processSignals([
  {
    topic: "Rust async programming",
    weight: 0.7,
    intent: "building",
    sentiment: "positive",
    depth: "moderate",
    category: "technology",
    entities: ["tokio", "axum", "tower"],
    timestamp: new Date().toISOString(),
  },
]);
console.log(`   Tracked: ${r4.tracked} topics (${r4.topics.join(", ")})\n`);

// ── Check Interest Profile ──
console.log("=== INTEREST PROFILE ===\n");
const stats = engine.getStats();
console.log(`Total: ${stats.total_topics} topics, ${stats.total_signals} signals, ${stats.total_conversations} conversations`);
console.log(`Active: ${stats.active_topics} topics`);
console.log(`Categories:`, stats.top_categories);

const interests = engine.getTopInterests(10);
console.log("\nTop Interests (sorted by weight):");
for (const i of interests) {
  const filled = Math.min(5, Math.round(i.current_weight * 5));
  const bar = "█".repeat(filled) + "░".repeat(5 - filled);
  console.log(`  ${i.topic.padEnd(25)} [${bar}] w=${i.current_weight.toFixed(3)} freq=${i.frequency} intent=${i.dominant_intent} sentiment=${i.sentiment_balance.toFixed(2)}`);
}

// ── Verify CSS is deprioritized ──
const cssNode = interests.find(i => i.topic.toLowerCase().includes("css"));
if (cssNode) {
  const rustNode = interests.find(i => i.topic.toLowerCase().includes("rust"));
  if (rustNode && rustNode.current_weight > cssNode.current_weight) {
    console.log("\n✅ PASS: Rust (positive, deep, 2x) outweighs CSS (negative, moderate, 1x)");
  } else {
    console.log("\n❌ FAIL: CSS should be lower than Rust");
  }
} else {
  console.log("\n⚠️  CSS was pruned (below threshold) — that's acceptable");
}

// ── Check Balanced Allocation ──
console.log("\n=== BALANCED ALLOCATION (7 items) ===\n");
const balanced = engine.getBalancedInterests(7);
for (const [cat, data] of Object.entries(balanced)) {
  console.log(`${cat}: ${data.allocation} items`);
  for (const interest of data.interests) {
    console.log(`  - ${interest.topic} (w=${interest.current_weight.toFixed(3)})`);
  }
}

// ── Generate Digest Payload ──
console.log("\n=== DIGEST PAYLOAD ===\n");
const config = engine.getConfig();
const summary = engine.getGraphSummary();

const digestPayload = {
  email: config.email || "test@example.com",
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
  preferences: { max_items: config.max_items, frequency: config.frequency },
};

console.log(`Topics in graph: ${summary.topics.length}`);
console.log(`Categories: ${Object.keys(summary.categories).join(", ")}`);
console.log(`Total signals: ${summary.total_signals}`);
console.log(`\nPayload size: ${JSON.stringify(digestPayload).length} bytes`);

// Validate the payload structure
const requiredKeys = ["email", "interest_graph", "balanced_allocation", "preferences"];
const missing = requiredKeys.filter(k => !(k in digestPayload));
if (missing.length === 0) {
  console.log("✅ PASS: Digest payload has all required keys");
} else {
  console.log(`❌ FAIL: Missing keys: ${missing.join(", ")}`);
}

if (summary.topics.length >= 4) {
  console.log("✅ PASS: Interest graph has enough topics for a digest");
} else {
  console.log(`❌ FAIL: Only ${summary.topics.length} topics — need at least 3-4`);
}

// ── Test Topic Normalization ──
console.log("\n=== TOPIC NORMALIZATION TEST ===\n");
engine.processSignals([
  {
    topic: "React.js",
    weight: 0.5,
    intent: "learning",
    sentiment: "positive",
    depth: "mention",
    category: "technology",
    entities: ["React"],
    timestamp: new Date().toISOString(),
  },
]);
engine.processSignals([
  {
    topic: "React JS",
    weight: 0.3,
    intent: "discussing",
    sentiment: "neutral",
    depth: "mention",
    category: "technology",
    entities: ["React"],
    timestamp: new Date().toISOString(),
  },
]);

const allInterests = engine.getTopInterests(20);
const reactNodes = allInterests.filter(i => i.topic.toLowerCase().includes("react"));
if (reactNodes.length === 1) {
  console.log(`✅ PASS: "React.js" and "React JS" merged into single node (freq=${reactNodes[0].frequency})`);
} else if (reactNodes.length > 1) {
  console.log(`❌ FAIL: Found ${reactNodes.length} separate React nodes — normalization issue`);
  reactNodes.forEach(n => console.log(`   - "${n.topic}" (freq=${n.frequency})`));
} else {
  console.log("⚠️  No React nodes found (possibly below threshold)");
}

// ── Test Forget ──
console.log("\n=== PRIVACY TEST (forget) ===\n");
const beforeCount = engine.getTopInterests(20).length;
const removed = engine.removeTopic("CSS layout");
console.log(`Remove "CSS layout": ${removed ? "✅ removed" : "⚠️ not found"}`);
const afterCount = engine.getTopInterests(20).length;
console.log(`Topics before: ${beforeCount}, after: ${afterCount}`);

// ── Clean up test data ──
engine.clearAll();
console.log("\n✅ Cleared all test data");

console.log("\n=== TEST COMPLETE ===");
