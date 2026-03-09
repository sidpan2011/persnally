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
  technology: "bg-blue-500",
  business: "bg-purple-500",
  finance: "bg-green-500",
  career: "bg-orange-500",
  health: "bg-red-500",
  science: "bg-cyan-500",
  creative: "bg-pink-500",
  education: "bg-yellow-500",
  lifestyle: "bg-indigo-500",
  news: "bg-gray-500",
  other: "bg-gray-400",
};

const CATEGORY_BG: Record<string, string> = {
  technology: "bg-blue-50 text-blue-700",
  business: "bg-purple-50 text-purple-700",
  finance: "bg-green-50 text-green-700",
  career: "bg-orange-50 text-orange-700",
  health: "bg-red-50 text-red-700",
  science: "bg-cyan-50 text-cyan-700",
  creative: "bg-pink-50 text-pink-700",
  education: "bg-yellow-50 text-yellow-700",
  lifestyle: "bg-indigo-50 text-indigo-700",
  news: "bg-gray-100 text-gray-700",
  other: "bg-gray-100 text-gray-600",
};

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
        <div className="text-gray-400 text-sm">Loading interest graph...</div>
      </div>
    );
  }

  if (!data?.has_data) {
    return (
      <div className="max-w-lg mx-auto text-center py-20">
        <h2 className="text-xl font-bold text-black mb-2">No interest data yet</h2>
        <p className="text-gray-500 text-sm">
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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-black">Interest Graph</h1>
        <p className="text-sm text-gray-500 mt-1">
          {topics.length} topics &middot; {data.interest_graph.total_signals} signals
          {data.synced_at && (
            <span> &middot; Synced {new Date(data.synced_at).toLocaleDateString()}</span>
          )}
        </p>
      </div>

      {/* Category Distribution */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-black mb-4">Category Distribution</h2>

        {/* Bar */}
        <div className="h-4 rounded-full overflow-hidden flex mb-4">
          {Object.entries(categories)
            .sort(([, a], [, b]) => b - a)
            .map(([cat, weight]) => (
              <div
                key={cat}
                className={`${CATEGORY_COLORS[cat] || "bg-gray-300"} transition-all duration-500`}
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
                className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-full transition-colors ${
                  filterCategory === cat
                    ? "bg-black text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <div className={`w-2 h-2 rounded-full ${CATEGORY_COLORS[cat] || "bg-gray-300"}`} />
                <span className="capitalize">{cat}</span>
                <span className="text-gray-400">{Math.round((weight / totalWeight) * 100)}%</span>
              </button>
            ))}
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Topics List */}
        <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-black">
              {filterCategory === "all" ? "All Topics" : (
                <span className="capitalize">{filterCategory}</span>
              )}
              <span className="text-gray-400 font-normal ml-2">({filteredTopics.length})</span>
            </h2>
            {filterCategory !== "all" && (
              <button
                onClick={() => setFilterCategory("all")}
                className="text-xs text-gray-400 hover:text-black"
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
                      <span className="text-sm font-medium text-black truncate">
                        {topic.topic}
                      </span>
                      <span className={`text-xs px-1.5 py-0.5 rounded-full ${CATEGORY_BG[topic.category] || "bg-gray-100 text-gray-600"}`}>
                        {topic.category}
                      </span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${CATEGORY_COLORS[topic.category] || "bg-gray-400"}`}
                        style={{ width: `${Math.min(100, (topic.weight / maxWeight) * 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-xs font-mono text-gray-500">{topic.weight.toFixed(2)}</div>
                    <div className="text-xs text-gray-400">{topic.intent}</div>
                  </div>
                </div>
                {/* Entities on hover */}
                {topic.entities && topic.entities.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {topic.entities.slice(0, 5).map((e) => (
                      <span key={e} className="text-xs bg-gray-50 text-gray-500 rounded px-1.5 py-0.5">
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
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-black mb-4">Top Entities</h2>
            <div className="flex flex-wrap gap-2">
              {topEntities.map(([entity, weight]) => {
                const maxEntityWeight = topEntities[0]?.[1] || 1;
                const size = 0.7 + (weight / maxEntityWeight) * 0.5;
                return (
                  <span
                    key={entity}
                    className="bg-gray-100 text-gray-700 rounded-full px-2.5 py-1 transition-colors hover:bg-gray-200"
                    style={{ fontSize: `${size}rem` }}
                  >
                    {entity}
                  </span>
                );
              })}
            </div>
          </div>

          {/* Privacy Note */}
          <div className="bg-gray-50 rounded-xl border border-gray-100 p-5">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Your data, your control</h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              This graph is built from structured signals only — topic names, weights,
              and categories. Your raw conversations are never stored or transmitted.
            </p>
            <p className="text-xs text-gray-400 mt-2">
              Use <code className="bg-gray-200 px-1 rounded">persnally_forget</code> in
              Claude to remove any topic.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
