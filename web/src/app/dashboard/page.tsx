"use client";

import { useCallback, useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

interface Stats {
  total_topics: number;
  total_signals: number;
  total_digests: number;
  avg_quality: number;
  last_synced: string | null;
  last_digest: string | null;
  frequency: string;
  top_categories: { name: string; weight: number }[];
  intent_breakdown: Record<string, number>;
  sentiment: { positive: number; negative: number; neutral: number };
}

interface InterestData {
  has_data: boolean;
  interest_graph: {
    topics: {
      topic: string;
      weight: number;
      category: string;
      intent: string;
      entities: string[];
    }[];
    categories: Record<string, number>;
    total_signals: number;
  };
  synced_at: string | null;
}

export default function DashboardOverview() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [interests, setInterests] = useState<InterestData | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) return;

    try {
      const [statsData, interestData] = await Promise.all([
        apiFetch("/digest/stats", session.access_token),
        apiFetch("/digest/interests", session.access_token),
      ]);
      setStats(statsData);
      setInterests(interestData);
    } catch (e) {
      console.error("Failed to load dashboard:", e);
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
        <div className="text-gray-400 text-sm">Loading your dashboard...</div>
      </div>
    );
  }

  const hasData = interests?.has_data && stats && stats.total_topics > 0;
  const topics = interests?.interest_graph?.topics || [];
  const topTopics = [...topics]
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 8);
  const maxWeight = topTopics.length > 0 ? topTopics[0].weight : 1;

  if (!hasData) {
    return (
      <div className="max-w-lg mx-auto text-center py-20">
        <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-8 h-8 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
            />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-black mb-2">
          No interests tracked yet
        </h2>
        <p className="text-gray-500 text-sm leading-relaxed mb-6">
          Install the Persnally MCP server and start chatting with Claude. Your
          interest graph will build automatically as you discuss topics you care
          about.
        </p>
        <div className="bg-gray-950 rounded-lg p-4 text-left font-mono text-sm text-gray-300 mb-4">
          <span className="text-green-400">$</span> npm install -g persnally
        </div>
        <p className="text-xs text-gray-400">
          Then add it to your Claude Desktop config and start chatting.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-black">Your Interest Pulse</h1>
        <p className="text-sm text-gray-500 mt-1">
          Built from your conversations with Claude
          {stats?.last_synced && (
            <span>
              {" "}&middot; Last synced{" "}
              {new Date(stats.last_synced).toLocaleDateString()}
            </span>
          )}
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Topics Tracked", value: stats?.total_topics || 0, sub: "active interests" },
          { label: "Signals", value: stats?.total_signals || 0, sub: "from conversations" },
          { label: "Digests Sent", value: stats?.total_digests || 0, sub: stats?.frequency || "daily" },
          { label: "Avg Quality", value: stats?.avg_quality || 0, sub: "out of 100" },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl font-bold text-black">{stat.value}</div>
            <div className="text-sm font-medium text-gray-700 mt-1">{stat.label}</div>
            <div className="text-xs text-gray-400">{stat.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Top Interests */}
        <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-black">Top Interests</h2>
            <Link href="/dashboard/interests" className="text-xs text-gray-400 hover:text-black transition-colors">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {topTopics.map((topic) => (
              <div key={topic.topic} className="flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-black truncate">{topic.topic}</span>
                    <span className="text-xs text-gray-400 ml-2 shrink-0">{topic.intent}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-black rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, (topic.weight / maxWeight) * 100)}%` }}
                    />
                  </div>
                </div>
                <span className="text-xs font-mono text-gray-400 w-12 text-right">
                  {topic.weight.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Categories */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-black mb-4">Categories</h2>
            <div className="space-y-2">
              {stats?.top_categories.map((cat) => (
                <div key={cat.name} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 capitalize">{cat.name}</span>
                  <span className="text-xs font-mono text-gray-400">{cat.weight}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Intent Breakdown */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-black mb-4">What You&apos;re Doing</h2>
            <div className="space-y-2">
              {stats?.intent_breakdown &&
                Object.entries(stats.intent_breakdown)
                  .sort(([, a], [, b]) => b - a)
                  .map(([intent, count]) => (
                    <div key={intent} className="flex items-center justify-between">
                      <span className="text-sm text-gray-700 capitalize">{intent}</span>
                      <span className="text-xs bg-gray-100 rounded-full px-2 py-0.5 text-gray-600">{count}</span>
                    </div>
                  ))}
            </div>
          </div>

          {/* Sentiment */}
          {stats?.sentiment && stats.total_topics > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="font-semibold text-black mb-4">Sentiment</h2>
              <div className="flex gap-2">
                {stats.sentiment.positive > 0 && (
                  <div className="bg-green-100 rounded-lg px-3 py-2 text-center" style={{ flex: stats.sentiment.positive }}>
                    <div className="text-lg font-bold text-green-700">{stats.sentiment.positive}</div>
                    <div className="text-xs text-green-600">positive</div>
                  </div>
                )}
                {stats.sentiment.neutral > 0 && (
                  <div className="bg-gray-100 rounded-lg px-3 py-2 text-center" style={{ flex: stats.sentiment.neutral }}>
                    <div className="text-lg font-bold text-gray-700">{stats.sentiment.neutral}</div>
                    <div className="text-xs text-gray-500">neutral</div>
                  </div>
                )}
                {stats.sentiment.negative > 0 && (
                  <div className="bg-red-50 rounded-lg px-3 py-2 text-center" style={{ flex: stats.sentiment.negative }}>
                    <div className="text-lg font-bold text-red-600">{stats.sentiment.negative}</div>
                    <div className="text-xs text-red-500">negative</div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
