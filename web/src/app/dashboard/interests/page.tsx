"use client";

import { useCallback, useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";

interface Topic {
  topic: string;
  weight: number;
  category: string;
  intent: string;
  entities: string[];
  frequency?: number;
  sentiment_balance?: number;
}

interface InterestData {
  has_data: boolean;
  interest_graph: {
    topics: Topic[];
    categories: Record<string, number>;
    total_signals: number;
  };
  balanced_allocation: Record<string, { allocation: number; interests: Topic[] }>;
  synced_at: string | null;
}

const CATEGORY_COLORS: Record<string, string> = {
  technology: "bg-electric",
  business: "bg-volt",
  finance: "bg-electric",
  career: "bg-volt",
  health: "bg-electric",
  science: "bg-volt",
  creative: "bg-electric",
  education: "bg-volt",
  lifestyle: "bg-electric",
  news: "bg-faint",
  other: "bg-line",
};

const CATEGORY_BG = "border border-line bg-panel text-mute";

export default function InterestGraphPage() {
  const [data, setData] = useState<InterestData | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState<string>("all");

  const loadData = useCallback(async () => {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    try {
      const result = await apiFetch("/digest/interests", session.access_token);
      setData(result);
    } catch (e) {
      console.error("Failed to load interests:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-mute text-sm">Loading interest graph...</div>
      </div>
    );
  }

  if (!data?.has_data) {
    return (
      <div className="max-w-lg mx-auto text-center py-20">
        <h2 className="text-ink font-semibold tracking-tight text-xl mb-2">No interest data yet</h2>
        <p className="text-mute text-sm">
          Your interest graph will appear here once you start chatting with Claude
          and the MCP server syncs your data.
        </p>
      </div>
    );
  }

  const topics = data.interest_graph.topics || [];
  const categories = data.interest_graph.categories || {};
  const totalWeight = Object.values(categories).reduce((a, b) => a + b, 0);

  const filteredTopics = filterCategory === "all"
    ? [...topics].sort((a, b) => b.weight - a.weight)
    : [...topics].filter((t) => t.category === filterCategory).sort((a, b) => b.weight - a.weight);

  const maxWeight = topics.length > 0 ? Math.max(...topics.map((t) => t.weight)) : 1;

  // All entities across topics
  const allEntities: Record<string, number> = {};
  for (const t of topics) {
    for (const e of t.entities || []) {
      allEntities[e] = (allEntities[e] || 0) + t.weight;
    }
  }
  const topEntities = Object.entries(allEntities)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 20);

  return (
    <div className="space-y-6 bg-night text-ink">
      <div>
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt">Interest Graph</p>
        <h1 className="text-2xl text-ink font-semibold tracking-tight mt-1">Interest Graph</h1>
        <p className="text-sm text-mute mt-1">
          {topics.length} topics &middot; {data.interest_graph.total_signals} signals
          {data.synced_at && (
            <span> &middot; Synced {new Date(data.synced_at).toLocaleDateString()}</span>
          )}
        </p>
      </div>

      {/* Category Distribution */}
      <div className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="text-ink font-semibold tracking-tight mb-4">Category Distribution</h2>

        {/* Bar */}
        <div className="h-4 rounded-full overflow-hidden flex mb-4 bg-line">
          {Object.entries(categories)
            .sort(([, a], [, b]) => b - a)
            .map(([cat, weight]) => (
              <div
                key={cat}
                className={`${CATEGORY_COLORS[cat] || "bg-line"} transition-all duration-500`}
                style={{ width: `${(weight / totalWeight) * 100}%` }}
                title={`${cat}: ${Math.round((weight / totalWeight) * 100)}%`}
              />
            ))}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-3">
          {Object.entries(categories)
            .sort(([, a], [, b]) => b - a)
            .map(([cat, weight]) => (
              <button
                key={cat}
                onClick={() => setFilterCategory(filterCategory === cat ? "all" : cat)}
                className={`flex items-center gap-1.5 font-mono text-[12px] px-2.5 py-1 rounded-md border transition-colors ${
                  filterCategory === cat
                    ? "border-volt/40 bg-electric/15 text-volt"
                    : "border-line bg-panel text-mute hover:border-volt/30"
                }`}
              >
                <div className={`w-2 h-2 rounded-full ${CATEGORY_COLORS[cat] || "bg-line"}`} />
                <span className="capitalize">{cat}</span>
                <span className="text-faint">{Math.round((weight / totalWeight) * 100)}%</span>
              </button>
            ))}
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Topics List */}
        <div className="md:col-span-2 rounded-2xl border border-line bg-surface p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-ink font-semibold tracking-tight">
              {filterCategory === "all" ? "All Topics" : (
                <span className="capitalize">{filterCategory}</span>
              )}
              <span className="text-faint font-normal ml-2">({filteredTopics.length})</span>
            </h2>
            {filterCategory !== "all" && (
              <button
                onClick={() => setFilterCategory("all")}
                className="text-xs text-mute hover:text-volt transition-colors"
              >
                Show all
              </button>
            )}
          </div>

          <div className="space-y-3">
            {filteredTopics.map((topic) => (
              <div key={topic.topic} className="group">
                <div className="flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-ink truncate">
                        {topic.topic}
                      </span>
                      <span className={`rounded-md px-2.5 py-1 font-mono text-[12px] ${CATEGORY_BG}`}>
                        {topic.category}
                      </span>
                    </div>
                    <div className="h-1.5 bg-line rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-electric to-volt"
                        style={{ width: `${Math.min(100, (topic.weight / maxWeight) * 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-xs font-mono text-mute">{topic.weight.toFixed(2)}</div>
                    <div className="text-xs text-faint">{topic.intent}</div>
                  </div>
                </div>
                {/* Entities on hover */}
                {topic.entities && topic.entities.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {topic.entities.slice(0, 5).map((e) => (
                      <span key={e} className="rounded-md border border-line bg-panel px-2.5 py-1 font-mono text-[12px] text-mute">
                        {e}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Right: Entities Cloud */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="text-ink font-semibold tracking-tight mb-4">Top Entities</h2>
            <div className="flex flex-wrap gap-2">
              {topEntities.map(([entity, weight]) => {
                const maxEntityWeight = topEntities[0]?.[1] || 1;
                const size = 0.7 + (weight / maxEntityWeight) * 0.5;
                return (
                  <span
                    key={entity}
                    className="rounded-md border border-line bg-panel px-2.5 py-1 font-mono text-mute transition-colors hover:border-volt/30 hover:text-volt"
                    style={{ fontSize: `${size}rem` }}
                  >
                    {entity}
                  </span>
                );
              })}
            </div>
          </div>

          {/* Privacy Note */}
          <div className="rounded-2xl border border-volt/30 bg-panel p-5">
            <h3 className="text-sm font-medium text-ink mb-2">Your data, your control</h3>
            <p className="text-xs text-mute leading-relaxed">
              This graph is built from structured signals only — topic names, weights,
              and categories. Your raw conversations are never stored or transmitted.
            </p>
            <p className="text-xs text-faint mt-2">
              Use <code className="font-mono bg-night border border-line text-volt px-1 rounded">persnally_forget</code> in
              Claude to remove any topic.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
