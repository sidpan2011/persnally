"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

interface SkillSnapshot {
  snapshot_date: string;
  skills: Record<string, { level: number; category: string }>;
  languages: Record<string, { percentage: number; repos: number }>;
  domains: Record<string, number>;
  specialization: string;
  career_stage: string;
  experience_level: string;
  summary: string;
  strengths: string[];
  growth_areas: string[];
  raw_github_data: {
    repo_count: number;
    active_repo_count: number;
  };
}

interface SkillGap {
  id: string;
  skill_name: string;
  reason: string;
  category: string;
  gap_score: number;
}

const DOMAIN_COLORS: Record<string, string> = {
  frontend: "bg-blue-500",
  backend: "bg-green-500",
  ai_ml: "bg-purple-500",
  devops: "bg-orange-500",
  mobile: "bg-pink-500",
  database: "bg-yellow-500",
  systems: "bg-red-500",
};

export default function DashboardPage() {
  const [token, setToken] = useState("");
  const [snapshot, setSnapshot] = useState<SkillSnapshot | null>(null);
  const [gaps, setGaps] = useState<SkillGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [jobStatus, setJobStatus] = useState("");

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) setToken(session.access_token);
    });
  }, []);

  const loadData = useCallback(async () => {
    if (!token) return;
    try {
      const [snap, gapData] = await Promise.all([
        apiFetch("/skills/snapshot", token),
        apiFetch("/skills/gaps", token),
      ]);
      setSnapshot(snap);
      setGaps(gapData || []);

      // Auto-trigger analysis if no snapshot exists
      if (!snap) {
        triggerAnalysis();
      }
    } catch (err) {
      console.error("Failed to load:", err);
      // If 404/error on first load, trigger analysis
      triggerAnalysis();
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) loadData();
  }, [token, loadData]);

  const triggerAnalysis = async () => {
    if (!token || analyzing) return;
    setAnalyzing(true);
    setJobStatus("pending");
    try {
      const data = await apiFetch("/skills/analyze", token, { method: "POST" });
      pollJob(data.job_id);
    } catch (err) {
      console.error("Analysis error:", err);
      setAnalyzing(false);
    }
  };

  const pollJob = (id: string) => {
    const interval = setInterval(async () => {
      try {
        const data = await apiFetch(`/skills/analyze/${id}`, token);
        setJobStatus(data.status);
        if (data.status === "completed" || data.status === "failed") {
          clearInterval(interval);
          setAnalyzing(false);
          if (data.status === "completed") loadData();
        }
      } catch {
        clearInterval(interval);
        setAnalyzing(false);
      }
    }, 2000);
  };

  const topSkills = snapshot
    ? Object.entries(snapshot.skills)
        .sort(([, a], [, b]) => b.level - a.level)
        .slice(0, 6)
    : [];

  if (loading) {
    return <div className="text-center py-16 text-gray-400">Loading...</div>;
  }

  // First-time analyzing state
  if (analyzing && !snapshot) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 mx-auto mb-6 relative">
            <div className="absolute inset-0 bg-blue-500 rounded-2xl opacity-20 animate-ping" />
            <div className="relative w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          </div>
          <h2 className="text-xl font-bold text-black mb-2">Building Your Skill DNA</h2>
          <p className="text-gray-500 text-sm mb-4">
            {jobStatus === "running"
              ? "Scanning repositories, detecting frameworks, analyzing patterns..."
              : "Connecting to GitHub..."}
          </p>
          <div className="flex items-center justify-center gap-2 text-xs text-gray-400">
            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
            This takes about 10-15 seconds
          </div>
        </div>
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-bold text-black mb-2">Welcome to Persnally</h2>
        <p className="text-gray-500 text-sm mb-6">
          Something went wrong loading your profile. Try refreshing.
        </p>
        <button
          onClick={triggerAnalysis}
          className="bg-black text-white px-6 py-2.5 rounded-lg font-medium hover:bg-gray-800 cursor-pointer"
        >
          Retry Analysis
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Welcome header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-black">Career Intelligence</h1>
        <p className="text-gray-500 text-sm mt-1">{snapshot.specialization}</p>
      </div>

      {/* Summary card */}
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 mb-8 text-white">
        <p className="text-sm leading-relaxed text-gray-300">{snapshot.summary}</p>
        <div className="flex gap-8 mt-5 pt-4 border-t border-gray-700">
          <div>
            <div className="text-2xl font-bold">{Object.keys(snapshot.skills).length}</div>
            <div className="text-xs text-gray-400">Skills</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{snapshot.raw_github_data?.repo_count || 0}</div>
            <div className="text-xs text-gray-400">Repos</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{gaps.length}</div>
            <div className="text-xs text-gray-400">Growth Areas</div>
          </div>
          <div>
            <div className="text-2xl font-bold capitalize">{snapshot.experience_level}</div>
            <div className="text-xs text-gray-400">Level</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Top skills */}
        <Link
          href="/dashboard/skills"
          className="bg-white border border-gray-200 rounded-xl p-6 hover:border-gray-300 transition-colors"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-black">Top Skills</h2>
            <span className="text-xs text-gray-400">View all &rarr;</span>
          </div>
          <div className="space-y-2.5">
            {topSkills.map(([name, data]) => (
              <div key={name} className="flex items-center gap-3">
                <div className="w-24 text-sm text-gray-600 truncate">{name}</div>
                <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-gray-800 rounded-full"
                    style={{ width: `${Math.max(data.level * 100, 4)}%` }}
                  />
                </div>
                <div className="w-8 text-xs text-gray-400 text-right">
                  {Math.round(data.level * 100)}
                </div>
              </div>
            ))}
          </div>
        </Link>

        {/* Domains */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="font-semibold text-black mb-4">Domain Expertise</h2>
          <div className="space-y-3">
            {Object.entries(snapshot.domains).slice(0, 5).map(([domain, score]) => (
              <div key={domain} className="flex items-center gap-3">
                <div className="w-24 text-sm text-gray-600 capitalize">
                  {domain.replace("_", " ")}
                </div>
                <div className="flex-1 bg-gray-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${DOMAIN_COLORS[domain] || "bg-gray-500"}`}
                    style={{ width: `${Math.max(score * 100, 3)}%` }}
                  />
                </div>
                <div className="w-10 text-xs text-gray-400 text-right">
                  {Math.round(score * 100)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Skill gaps preview */}
      {gaps.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-black">Recommended Skills to Learn</h2>
            <Link href="/dashboard/skills" className="text-xs text-gray-400 hover:text-black">
              View all &rarr;
            </Link>
          </div>
          <div className="flex flex-wrap gap-2">
            {gaps.slice(0, 5).map((gap) => (
              <div
                key={gap.id}
                className="px-3 py-2 bg-blue-50 rounded-lg text-sm"
                title={gap.reason}
              >
                <span className="font-medium text-blue-800">{gap.skill_name}</span>
                <span className="text-blue-500 ml-1 text-xs">{gap.category}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Strengths */}
      {snapshot.strengths && snapshot.strengths.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="font-semibold text-black mb-4">Your Strengths</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {snapshot.strengths.map((s, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <svg className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                {s}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
