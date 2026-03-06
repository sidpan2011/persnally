"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

interface Newsletter {
  id: string;
  subject: string;
  headline: string;
  status: string;
  quality_score: number | null;
  sent_at: string;
  items: Array<{ title: string; category?: string }>;
  item_count: number;
}

export default function DashboardPage() {
  const [token, setToken] = useState("");
  const [newsletters, setNewsletters] = useState<Newsletter[]>([]);
  const [generating, setGenerating] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setToken(session.access_token);
      }
    });
  }, []);

  const loadNewsletters = useCallback(async () => {
    if (!token) return;
    try {
      const data = await apiFetch("/newsletters?limit=5", token);
      setNewsletters(data);
    } catch (err) {
      console.error("Failed to load newsletters:", err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) loadNewsletters();
  }, [token, loadNewsletters]);

  const handleGenerate = async () => {
    if (!token) return;
    setGenerating(true);
    setJobStatus("pending");

    try {
      const data = await apiFetch("/newsletters/generate", token, {
        method: "POST",
      });
      setJobId(data.job_id);
      pollJob(data.job_id);
    } catch (err) {
      console.error("Generation error:", err);
      setGenerating(false);
    }
  };

  const pollJob = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const data = await apiFetch(`/newsletters/generate/${id}`, token);
        setJobStatus(data.status);

        if (data.status === "completed" || data.status === "failed") {
          clearInterval(interval);
          setGenerating(false);
          setJobId(null);
          if (data.status === "completed") {
            loadNewsletters();
          }
        }
      } catch {
        clearInterval(interval);
        setGenerating(false);
      }
    }, 3000);
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-black">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">
            Your personalized tech intelligence
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-2 bg-black text-white px-5 py-2.5 rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-300 cursor-pointer"
        >
          {generating ? (
            <>
              <svg
                className="w-4 h-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              {jobStatus === "running"
                ? "Generating..."
                : "Starting..."}
            </>
          ) : (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              Generate Newsletter
            </>
          )}
        </button>
      </div>

      {/* Generation status */}
      {generating && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            <div>
              <div className="text-sm font-medium text-blue-900">
                {jobStatus === "running"
                  ? "Crawling the internet & curating your feed..."
                  : "Starting generation engine..."}
              </div>
              <div className="text-xs text-blue-600 mt-0.5">
                This usually takes 30-60 seconds
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Newsletter list */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : newsletters.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-4xl mb-4">&#9889;</div>
          <h3 className="text-lg font-semibold text-black mb-2">
            No newsletters yet
          </h3>
          <p className="text-gray-500 text-sm mb-6">
            Generate your first personalized newsletter to get started.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {newsletters.map((nl) => (
            <Link
              key={nl.id}
              href={`/dashboard/newsletters?id=${nl.id}`}
              className="block bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-black truncate">
                    {nl.headline || nl.subject}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {nl.item_count} items &middot;{" "}
                    {new Date(nl.sent_at).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </div>
                </div>
                <span
                  className={`text-xs px-2 py-1 rounded-full font-medium ${
                    nl.status === "sent"
                      ? "bg-green-50 text-green-700"
                      : "bg-red-50 text-red-700"
                  }`}
                >
                  {nl.status}
                </span>
              </div>
            </Link>
          ))}

          {newsletters.length >= 5 && (
            <Link
              href="/dashboard/newsletters"
              className="block text-center text-sm text-gray-500 hover:text-black py-2"
            >
              View all newsletters
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
