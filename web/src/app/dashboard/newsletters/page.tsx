"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

interface NewsletterDetail {
  id: string;
  subject: string;
  headline: string;
  items: Array<{ title: string; content: string; category?: string; source?: string; url?: string }>;
  full_content: Record<string, unknown>;
  html_snapshot: string | null;
  status: string;
  quality_score: number | null;
  sent_at: string;
}

interface NewsletterListItem {
  id: string;
  subject: string;
  headline: string;
  status: string;
  sent_at: string;
  item_count: number;
}

function NewslettersContent() {
  const searchParams = useSearchParams();
  const selectedId = searchParams.get("id");

  const [token, setToken] = useState("");
  const [newsletters, setNewsletters] = useState<NewsletterListItem[]>([]);
  const [selected, setSelected] = useState<NewsletterDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) setToken(session.access_token);
    });
  }, []);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const data = await apiFetch("/newsletters?limit=50", token);
      setNewsletters(data);

      if (selectedId) {
        const detail = await apiFetch(`/newsletters/${selectedId}`, token);
        setSelected(detail);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [token, selectedId]);

  useEffect(() => {
    if (token) load();
  }, [token, load]);

  const viewNewsletter = async (id: string) => {
    try {
      const detail = await apiFetch(`/newsletters/${id}`, token);
      setSelected(detail);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-400">Loading...</div>;

  if (selected) {
    return (
      <div>
        <button
          onClick={() => setSelected(null)}
          className="text-sm text-gray-500 hover:text-black mb-6 flex items-center gap-1 cursor-pointer"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to list
        </button>

        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-xl font-bold text-black">{selected.headline}</h2>
            <div className="text-sm text-gray-500 mt-1">
              {new Date(selected.sent_at).toLocaleDateString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
              {selected.quality_score && (
                <span className="ml-3 text-gray-400">
                  Quality: {Math.round(selected.quality_score)}/100
                </span>
              )}
            </div>
          </div>

          {selected.html_snapshot ? (
            <iframe
              srcDoc={selected.html_snapshot}
              className="w-full border-0"
              style={{ minHeight: "800px" }}
              title="Newsletter preview"
            />
          ) : (
            <div className="p-6 space-y-6">
              {selected.items.map((item, i) => (
                <div key={i} className="border-b border-gray-100 pb-6 last:border-0">
                  <div className="text-xs text-gray-400 mb-1">#{i + 1}</div>
                  <h3 className="font-semibold text-black mb-2">{item.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{item.content}</p>
                  {item.source && (
                    <div className="text-xs text-gray-400 mt-2">Source: {item.source}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-black mb-6">All Newsletters</h1>

      {newsletters.length === 0 ? (
        <div className="text-center py-12 text-gray-400">No newsletters yet.</div>
      ) : (
        <div className="space-y-2">
          {newsletters.map((nl) => (
            <button
              key={nl.id}
              onClick={() => viewNewsletter(nl.id)}
              className="w-full text-left bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-black">{nl.headline || nl.subject}</div>
                  <div className="text-sm text-gray-500 mt-0.5">
                    {nl.item_count} items &middot;{" "}
                    {new Date(nl.sent_at).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </div>
                </div>
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
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

export default function NewslettersPage() {
  return (
    <Suspense fallback={<div className="text-center py-12 text-gray-400">Loading...</div>}>
      <NewslettersContent />
    </Suspense>
  );
}
