/**
 * Interest weighting, ported from v1's interest-engine with the double-count fix:
 * v1 summed raw weights per signal AND multiplied a frequency bonus on top, defeating
 * the half-life for repeated topics. Here each signal decays individually and
 * frequency emerges from the decayed sum alone.
 */

const HALF_LIFE_DAYS = 7;
const LAMBDA = Math.LN2 / HALF_LIFE_DAYS;
const MS_PER_DAY = 86_400_000;
const MAX_WEIGHT = 10;

const DEPTH_SCORES: Record<string, number> = { mention: 0.3, moderate: 0.6, deep: 1.0 };
const SENTIMENT_VALUES: Record<string, number> = { positive: 0.5, negative: -0.5, neutral: 0 };

export interface WeightSignal {
  ts: string;
  weight: number;
  depth: string;
  sentiment: string;
  intent: string;
}

export interface TopicWeight {
  weight: number;
  sentiment_balance: number;
  dominant_intent: string;
}

export function topicWeight(signals: WeightSignal[], now: number = Date.now()): TopicWeight {
  let sum = 0;
  let sentiment = 0;
  const intents = new Map<string, number>();

  for (const s of signals) {
    const parsed = Date.parse(s.ts);
    if (!Number.isFinite(parsed)) continue; // an unparseable ts must not turn the sum into NaN
    const days = Math.max((now - parsed) / MS_PER_DAY, 0);
    sum += s.weight * (DEPTH_SCORES[s.depth] ?? 0.3) * Math.exp(-LAMBDA * days);
    sentiment += SENTIMENT_VALUES[s.sentiment] ?? 0;
    intents.set(s.intent, (intents.get(s.intent) ?? 0) + 1);
  }

  const balance = signals.length ? sentiment / signals.length : 0;
  // Negative sentiment deprioritizes (floor 0.2), never boosts.
  const sentimentMultiplier = Math.max(0.2, 1 + Math.min(balance, 0) * 0.8);
  // Most-frequent intent — v1 documented this but actually took the latest.
  const dominant = [...intents.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? "discussing";

  return {
    weight: Math.min(sum * sentimentMultiplier, MAX_WEIGHT),
    sentiment_balance: balance,
    dominant_intent: dominant,
  };
}
