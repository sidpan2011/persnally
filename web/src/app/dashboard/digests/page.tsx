"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";

interface DigestItem {
  number?: number;
  title: string;
  content: string;
  source?: string;
  url?: string;
}

interface Digest {
  id: string;
  subject: string;
  headline: string;
  status: string;
  quality_score: number;
  sent_at: string;
  items: DigestItem[];
  item_count: number;
  html_snapshot?: string;
  source?: string;
}

export default function DigestsPage() {
  const [digests, setDigests] = useState<Digest[]>([]);
  const [selected, setSelected] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);

  const loadDigests = useCallback(async () => {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    try {
      const data = await apiFetch("/newsletters?limit=50", session.access_token);
      setDigests(data);
    } catch (e) {
      console.error("Failed to load digests:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDetail = useCallback(async (id: string) => {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    try {
      const data = await apiFetch(`/newsletters/${id}`, session.access_token);
      setSelected(data);
    } catch (e) {
      console.error("Failed to load digest detail:", e);
    }
  }, []);

  useEffect(() => {
    loadDigests();
  }, [loadDigests]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-400 text-sm">Loading digests...</div>
      </div>
    );
  }

  // Detail view
  if (selected) {
    const items = selected.items || [];
    return (
      <div className="space-y-6">
        <button
          onClick={() => setSelected(null)}
          className="text-sm text-gray-400 hover:text-black transition-colors"
        >
          &larr; Back to digests
        </button>

        <div>
          <h1 className="text-2xl font-bold text-black">{selected.headline || selected.subject}</h1>
          <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
            <span>{new Date(selected.sent_at).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</span>
            {selected.quality_score > 0 && (
              <span className="bg-green-50 text-green-700 px-2 py-0.5 rounded-full text-xs">
                Quality: {selected.quality_score}/100
              </span>
            )}
            {selected.source === "mcp_interest_graph" && (
              <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full text-xs">
                From interest graph
              </span>
            )}
          </div>
        </div>

        {/* HTML snapshot or items */}
        {selected.html_snapshot ? (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <iframe
              srcDoc={selected.html_snapshot}
              className="w-full min-h-[600px] border-0"
              title="Digest content"
            />
          </div>
        ) : (
          <div className="space-y-4">
            {items.map((item, idx) => (
              <div key={idx} className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center text-white text-sm font-bold shrink-0">
                    {item.number || idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-black">{item.title}</h3>
                    <p className="text-sm text-gray-600 mt-1 leading-relaxed">{item.content}</p>
                    <div className="flex items-center gap-3 mt-3">
                      {item.source && (
                        <span className="text-xs text-gray-400">{item.source}</span>
                      )}
                      {item.url && (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-500 hover:text-blue-700"
                        >
                          Read more &rarr;
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // List view
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-black">Your Digests</h1>
        <p className="text-sm text-gray-500 mt-1">
          {digests.length} digest{digests.length !== 1 ? "s" : ""} sent
        </p>
      </div>

      {digests.length === 0 ? (
        <div className="max-w-lg mx-auto text-center py-16">
          <h2 className="text-lg font-semibold text-black mb-2">No digests yet</h2>
          <p className="text-sm text-gray-500">
            Once your interest graph has enough data, Persnally will curate and send
            personalized digests to your email.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {digests.map((digest) => (
            <button
              key={digest.id}
              onClick={() => loadDetail(digest.id)}
              className="w-full bg-white rounded-xl border border-gray-200 p-5 text-left hover:border-gray-300 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <h3 className="font-medium text-black truncate">
                    {digest.headline || digest.subject}
                  </h3>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                    <span>
                      {new Date(digest.sent_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    </span>
                    <span>{digest.item_count} items</span>
                    {digest.quality_score > 0 && (
                      <span>Quality: {digest.quality_score}</span>
                    )}
                  </div>
                </div>
                <svg className="w-4 h-4 text-gray-300 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
