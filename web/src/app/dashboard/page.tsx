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
        <div className="text-faint text-sm">Loading your dashboard...</div>
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
        <div className="w-16 h-16 bg-panel border border-volt/30 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-8 h-8 text-volt"
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
        <h2 className="text-xl text-ink font-semibold tracking-tight mb-2">
          No interests tracked yet
        </h2>
        <p className="text-mute text-sm leading-relaxed mb-6">
          Install the Persnally MCP server and start chatting with Claude. Your
          interest graph will build automatically as you discuss topics you care
          about.
        </p>
        <div className="bg-panel border border-line rounded-lg p-4 text-left font-mono text-sm text-ink mb-4">
          <span className="text-volt">$</span> npm install -g persnally
        </div>
        <p className="text-xs text-faint">
          Then add it to your Claude Desktop config and start chatting.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt mb-2">
          Overview
        </p>
        <h1 className="text-2xl text-ink font-semibold tracking-tight">Your Interest Pulse</h1>
        <p className="text-sm text-mute mt-1">
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
          <div key={stat.label} className="rounded-2xl border border-line bg-surface p-6">
            <div className="text-2xl text-ink font-semibold">{stat.value}</div>
            <div className="font-mono text-[11px] uppercase tracking-wider text-faint mt-2">{stat.label}</div>
            <div className="text-xs text-mute mt-1">{stat.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Top Interests */}
        <div className="md:col-span-2 rounded-2xl border border-line bg-surface p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-ink font-semibold tracking-tight">Top Interests</h2>
            <Link href="/dashboard/interests" className="text-xs text-mute hover:text-ink transition-colors">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {topTopics.map((topic) => (
              <div key={topic.topic} className="flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-ink truncate">{topic.topic}</span>
                    <span className="text-xs text-faint ml-2 shrink-0">{topic.intent}</span>
                  </div>
                  <div className="h-2 bg-line rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-electric to-volt rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, (topic.weight / maxWeight) * 100)}%` }}
                    />
                  </div>
                </div>
                <span className="text-xs font-mono text-faint w-12 text-right">
                  {topic.weight.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Categories */}
          <div className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="text-ink font-semibold tracking-tight mb-4">Categories</h2>
            <div className="space-y-2">
              {stats?.top_categories.map((cat) => (
                <div key={cat.name} className="flex items-center justify-between">
                  <span className="text-sm text-mute capitalize">{cat.name}</span>
                  <span className="text-xs font-mono text-faint">{cat.weight}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Intent Breakdown */}
          <div className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="text-ink font-semibold tracking-tight mb-4">What You&apos;re Doing</h2>
            <div className="space-y-2">
              {stats?.intent_breakdown &&
                Object.entries(stats.intent_breakdown)
                  .sort(([, a], [, b]) => b - a)
                  .map(([intent, count]) => (
                    <div key={intent} className="flex items-center justify-between">
                      <span className="text-sm text-mute capitalize">{intent}</span>
                      <span className="text-xs font-mono bg-panel border border-line rounded-full px-2 py-0.5 text-volt">{count}</span>
                    </div>
                  ))}
            </div>
          </div>

          {/* Sentiment */}
          {stats?.sentiment && stats.total_topics > 0 && (
            <div className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="text-ink font-semibold tracking-tight mb-4">Sentiment</h2>
              <div className="flex gap-2">
                {stats.sentiment.positive > 0 && (
                  <div className="bg-electric/20 border border-volt/30 rounded-lg px-3 py-2 text-center" style={{ flex: stats.sentiment.positive }}>
                    <div className="text-lg font-semibold text-volt">{stats.sentiment.positive}</div>
                    <div className="font-mono text-[11px] uppercase tracking-wider text-volt">positive</div>
                  </div>
                )}
                {stats.sentiment.neutral > 0 && (
                  <div className="bg-panel border border-line rounded-lg px-3 py-2 text-center" style={{ flex: stats.sentiment.neutral }}>
                    <div className="text-lg font-semibold text-ink">{stats.sentiment.neutral}</div>
                    <div className="font-mono text-[11px] uppercase tracking-wider text-mute">neutral</div>
                  </div>
                )}
                {stats.sentiment.negative > 0 && (
                  <div className="bg-panel border border-line rounded-lg px-3 py-2 text-center" style={{ flex: stats.sentiment.negative }}>
                    <div className="text-lg font-semibold text-mute">{stats.sentiment.negative}</div>
                    <div className="font-mono text-[11px] uppercase tracking-wider text-faint">negative</div>
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
