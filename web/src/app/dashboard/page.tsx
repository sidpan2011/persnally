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
  const [generating, setGenerating] = useState(false);
  const [generateJobId, setGenerateJobId] = useState<string | null>(null);

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
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-black">Welcome to Persnally</h1>
          <p className="text-sm text-gray-500 mt-1">
            We&apos;re analyzing your GitHub to build your initial interest profile...
          </p>
        </div>

        {/* GitHub Seeding Status */}
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
          <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-gray-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-black mb-2">
            Building your interest profile
          </h2>
          <p className="text-sm text-gray-500 mb-6 max-w-sm mx-auto">
            We&apos;re analyzing your GitHub repos, stars, and languages to create your initial profile. This usually takes a few seconds.
          </p>
          <button
            onClick={() => loadData()}
            className="px-4 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 transition-colors cursor-pointer"
          >
            Refresh
          </button>
        </div>

        {/* MCP Upsell */}
        <div className="bg-gray-50 rounded-xl border border-gray-100 p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-black text-sm">Make it smarter with Claude</h3>
              <p className="text-sm text-gray-500 mt-1 mb-3">
                Install the MCP server to let Persnally learn from your Claude conversations. Your profile gets more accurate every day.
              </p>
              <div className="bg-gray-950 rounded-lg p-3 font-mono text-sm text-gray-300 inline-block">
                <span className="text-green-400">$</span> npm install -g persnally
              </div>
            </div>
          </div>
        </div>
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

      {/* Quick Actions */}
      <div className="flex gap-3">
        <button
          onClick={async () => {
            setGenerating(true);
            try {
              const supabase = createClient();
              const { data: { session } } = await supabase.auth.getSession();
              if (session) {
                const result = await apiFetch("/newsletters/generate", session.access_token, { method: "POST" });
                setGenerateJobId(result.job_id);
              }
            } catch (e) {
              console.error("Generate failed:", e);
            } finally {
              setGenerating(false);
            }
          }}
          disabled={generating}
          className="px-4 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 transition-colors disabled:bg-gray-300 cursor-pointer"
        >
          {generating ? "Generating..." : "Generate Digest"}
        </button>
        {generateJobId && (
          <span className="text-sm text-gray-500 self-center">
            Digest queued! Check your email shortly.
          </span>
        )}
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
