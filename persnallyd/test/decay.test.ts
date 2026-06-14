import assert from "node:assert/strict";
import { test } from "node:test";
import { topicWeight } from "../src/decay.js";

const NOW = Date.parse("2026-06-11T00:00:00Z");
const daysAgo = (n: number) => new Date(NOW - n * 86_400_000).toISOString();
const sig = (ts: string, weight = 1, depth = "deep", sentiment = "neutral", intent = "building") =>
  ({ ts, weight, depth, sentiment, intent });

test("a signal halves in weight after one half-life (7 days)", () => {
  const fresh = topicWeight([sig(daysAgo(0))], NOW).weight;
  const week = topicWeight([sig(daysAgo(7))], NOW).weight;
  assert.ok(Math.abs(week - fresh / 2) < 1e-9);
});

test("frequency is not double-counted: N old signals never outweigh N fresh ones", () => {
  const old = topicWeight(Array.from({ length: 10 }, () => sig(daysAgo(30))), NOW).weight;
  const fresh = topicWeight([sig(daysAgo(0)), sig(daysAgo(1))], NOW).weight;
  assert.ok(old < fresh, `10 month-old signals (${old}) must decay below 2 fresh ones (${fresh})`);
});

test("an unparseable timestamp is skipped, never turning the weight into NaN", () => {
  const w = topicWeight([sig("not-a-date"), sig(daysAgo(0))], NOW).weight;
  assert.ok(Number.isFinite(w), "weight must stay finite");
  assert.equal(w, topicWeight([sig(daysAgo(0))], NOW).weight, "bad signal contributes nothing");
});

test("negative sentiment deprioritizes but never zeroes", () => {
  const neutral = topicWeight([sig(daysAgo(0))], NOW).weight;
  const negative = topicWeight([sig(daysAgo(0), 1, "deep", "negative")], NOW).weight;
  assert.ok(negative < neutral);
  assert.ok(negative >= neutral * 0.2);
});

test("dominant intent is most frequent, not latest", () => {
  const result = topicWeight([
    sig(daysAgo(2), 1, "deep", "neutral", "learning"),
    sig(daysAgo(1), 1, "deep", "neutral", "learning"),
    sig(daysAgo(0), 1, "deep", "neutral", "debugging"),
  ], NOW);
  assert.equal(result.dominant_intent, "learning");
});

test("depth scales the contribution", () => {
  const deep = topicWeight([sig(daysAgo(0), 1, "deep")], NOW).weight;
  const mention = topicWeight([sig(daysAgo(0), 1, "mention")], NOW).weight;
  assert.ok(Math.abs(mention - deep * 0.3) < 1e-9);
});

test("weight is capped at 10", () => {
  const many = Array.from({ length: 100 }, () => sig(daysAgo(0)));
  assert.equal(topicWeight(many, NOW).weight, 10);
});
