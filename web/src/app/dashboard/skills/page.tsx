"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";

interface SkillData {
  level: number;
  category: string;
  repos: number;
  recent: boolean;
  detected_from?: string;
}

interface LanguageData {
  percentage: number;
  repos: number;
  stars: number;
  recent: boolean;
}

interface SkillGap {
  id: string;
  skill_name: string;
  reason: string;
  category: string;
  gap_score: number;
  market_demand: number;
  status: string;
}

interface SkillSnapshot {
  id: string;
  snapshot_date: string;
  skills: Record<string, SkillData>;
  languages: Record<string, LanguageData>;
  frameworks: Array<{
    name: string;
    category: string;
    confidence: number;
    repos: string[];
  }>;
  domains: Record<string, number>;
  experience_level: string;
  career_stage: string;
  specialization: string;
  summary: string;
  strengths: string[];
  growth_areas: string[];
  raw_github_data: {
    repo_count: number;
    active_repo_count: number;
    top_repos: Array<{
      name: string;
      language: string;
      stars: number;
      description: string;
      updated_at: string;
    }>;
  };
}

const DOMAIN_COLORS: Record<string, string> = {
  frontend: "bg-electric",
  backend: "bg-volt",
  ai_ml: "bg-electric/70",
  data_science: "bg-volt/70",
  devops: "bg-electric/50",
  mobile: "bg-volt/50",
  database: "bg-electric/40",
  systems: "bg-volt/40",
  blockchain: "bg-electric/30",
  security: "bg-volt/30",
  general: "bg-mute",
};

const DOMAIN_LABELS: Record<string, string> = {
  frontend: "Frontend",
  backend: "Backend",
  ai_ml: "AI / ML",
  data_science: "Data Science",
  devops: "DevOps",
  mobile: "Mobile",
  database: "Database",
  systems: "Systems",
  blockchain: "Blockchain",
  security: "Security",
  general: "General",
};

const GAP_CATEGORY_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  critical: { bg: "bg-panel border border-volt/30", text: "text-volt", label: "Critical" },
  recommended: { bg: "bg-panel border border-line", text: "text-ink", label: "Recommended" },
  emerging: { bg: "bg-panel border border-volt/30", text: "text-volt", label: "Emerging" },
  complementary: { bg: "bg-panel border border-line", text: "text-mute", label: "Complementary" },
};

function SkillBar({ name, level, category, recent }: { name: string; level: number; category: string; recent: boolean }) {
  const width = Math.max(level * 100, 4);
  const categoryColor = category === "language" ? "bg-gradient-to-r from-electric to-volt" :
    category === "frontend" ? "bg-electric" :
    category === "backend" ? "bg-volt" :
    category === "ai_ml" ? "bg-electric/70" :
    category === "database" ? "bg-volt/70" :
    category === "devops" ? "bg-electric/50" :
    category === "testing" ? "bg-volt/50" :
    category === "mobile" ? "bg-electric/40" :
    "bg-mute";

  return (
    <div className="flex items-center gap-3 group">
      <div className="w-32 text-sm font-medium text-ink truncate" title={name}>
        {name}
        {recent && <span className="ml-1 text-volt text-xs" title="Used recently">*</span>}
      </div>
      <div className="flex-1 bg-line rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${categoryColor}`}
          style={{ width: `${width}%` }}
        />
      </div>
      <div className="w-10 font-mono text-xs text-mute text-right">
        {Math.round(level * 100)}
      </div>
    </div>
  );
}

export default function SkillsPage() {
  const [token, setToken] = useState("");
  const [snapshot, setSnapshot] = useState<SkillSnapshot | null>(null);
  const [gaps, setGaps] = useState<SkillGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
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
    } catch (err) {
      console.error("Failed to load skills:", err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) loadData();
  }, [token, loadData]);

  const handleAnalyze = async () => {
    if (!token) return;
    setAnalyzing(true);
    setJobStatus("pending");
    try {
      const data = await apiFetch("/skills/analyze", token, { method: "POST" });
      setJobId(data.job_id);
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
          setJobId(null);
          if (data.status === "completed") loadData();
        }
      } catch {
        clearInterval(interval);
        setAnalyzing(false);
      }
    }, 2000);
  };

  // Sort skills by level for display
  const sortedSkills = snapshot
    ? Object.entries(snapshot.skills)
        .sort(([, a], [, b]) => b.level - a.level)
    : [];

  const languageSkills = sortedSkills.filter(([, s]) => s.category === "language");
  const frameworkSkills = sortedSkills.filter(([, s]) => s.category !== "language");

  return (
    <div className="bg-night text-ink">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt mb-2">
            Skill DNA
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">Skill DNA</h1>
          <p className="text-mute text-sm mt-1">
            Your technical identity, analyzed from your GitHub activity
          </p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="flex items-center gap-2 rounded-lg bg-electric px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-volt disabled:opacity-50 cursor-pointer"
        >
          {analyzing ? (
            <>
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {jobStatus === "running" ? "Analyzing GitHub..." : "Starting..."}
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {snapshot ? "Refresh Analysis" : "Analyze My GitHub"}
            </>
          )}
        </button>
      </div>

      {/* Analyzing state */}
      {analyzing && (
        <div className="rounded-2xl border border-volt/30 bg-surface p-6 mb-8">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-panel border border-line rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 animate-spin text-volt" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
            <div>
              <div className="font-semibold text-ink">
                {jobStatus === "running"
                  ? "Scanning your repositories..."
                  : "Initializing skill analyzer..."}
              </div>
              <div className="text-sm text-mute mt-0.5">
                Detecting frameworks from dependency files, analyzing code patterns, and building your skill profile
              </div>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-16 text-mute">Loading...</div>
      ) : !snapshot ? (
        /* Empty state — first time user */
        <div className="text-center py-20">
          <div className="w-20 h-20 bg-panel border border-line rounded-2xl flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-volt" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold tracking-tight text-ink mb-2">Discover Your Skill DNA</h3>
          <p className="text-mute text-sm mb-8 max-w-md mx-auto">
            We&apos;ll scan your repos, detect frameworks from actual dependency files, and build a
            comprehensive map of your technical abilities.
          </p>
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="rounded-lg bg-electric px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-volt cursor-pointer"
          >
            Run First Analysis
          </button>
        </div>
      ) : (
        /* Full skill dashboard */
        <div className="space-y-8">
          {/* Career identity card */}
          <div className="rounded-2xl border border-line bg-surface p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-volt mb-1">
                  Your Technical Identity
                </div>
                <div className="text-xl font-semibold tracking-tight text-ink">
                  {snapshot.specialization || "Developer"}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-[12px] px-2.5 py-1 rounded-md border border-line bg-panel text-mute capitalize">
                  {snapshot.career_stage?.replace("_", " ")}
                </span>
                <span className="font-mono text-[12px] px-2.5 py-1 rounded-md border border-line bg-panel text-mute capitalize">
                  {snapshot.experience_level}
                </span>
              </div>
            </div>
            <p className="text-mute text-sm leading-relaxed">
              {snapshot.summary}
            </p>

            {/* Stats row */}
            <div className="flex gap-6 mt-5 pt-5 border-t border-line">
              <div>
                <div className="font-mono text-2xl font-bold text-ink">
                  {Object.keys(snapshot.skills).length}
                </div>
                <div className="text-xs text-faint">Skills Detected</div>
              </div>
              <div>
                <div className="font-mono text-2xl font-bold text-ink">
                  {snapshot.raw_github_data?.repo_count || 0}
                </div>
                <div className="text-xs text-faint">Repositories</div>
              </div>
              <div>
                <div className="font-mono text-2xl font-bold text-ink">
                  {snapshot.raw_github_data?.active_repo_count || 0}
                </div>
                <div className="text-xs text-faint">Active (30d)</div>
              </div>
              <div>
                <div className="font-mono text-2xl font-bold text-ink">
                  {Object.keys(snapshot.languages).length}
                </div>
                <div className="text-xs text-faint">Languages</div>
              </div>
            </div>
          </div>

          {/* Domain radar */}
          <div className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="font-semibold tracking-tight text-ink mb-4">Domain Expertise</h2>
            <div className="space-y-3">
              {Object.entries(snapshot.domains).map(([domain, score]) => (
                <div key={domain} className="flex items-center gap-3">
                  <div className="w-24 text-sm text-mute">
                    {DOMAIN_LABELS[domain] || domain}
                  </div>
                  <div className="flex-1 bg-line rounded-full h-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${DOMAIN_COLORS[domain] || "bg-mute"}`}
                      style={{ width: `${Math.max(score * 100, 3)}%` }}
                    />
                  </div>
                  <div className="w-10 font-mono text-xs text-mute text-right">
                    {Math.round(score * 100)}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Two columns: Languages + Frameworks */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Languages */}
            <div className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="font-semibold tracking-tight text-ink mb-4">
                Languages
                <span className="text-faint font-normal text-sm ml-2">
                  {languageSkills.length}
                </span>
              </h2>
              <div className="space-y-2.5">
                {languageSkills.slice(0, 12).map(([name, data]) => (
                  <SkillBar
                    key={name}
                    name={name}
                    level={data.level}
                    category={data.category}
                    recent={data.recent}
                  />
                ))}
              </div>
            </div>

            {/* Frameworks & Tools */}
            <div className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="font-semibold tracking-tight text-ink mb-4">
                Frameworks & Tools
                <span className="text-faint font-normal text-sm ml-2">
                  {frameworkSkills.length}
                </span>
              </h2>
              <div className="space-y-2.5">
                {frameworkSkills.slice(0, 12).map(([name, data]) => (
                  <SkillBar
                    key={name}
                    name={name}
                    level={data.level}
                    category={data.category}
                    recent={data.recent}
                  />
                ))}
                {frameworkSkills.length === 0 && (
                  <div className="text-sm text-faint py-4 text-center">
                    No frameworks detected yet. Add dependency files to your repos for better detection.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Strengths */}
          {snapshot.strengths && snapshot.strengths.length > 0 && (
            <div className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="font-semibold tracking-tight text-ink mb-4">Key Strengths</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {snapshot.strengths.map((strength, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 bg-panel border border-line rounded-lg"
                  >
                    <div className="w-5 h-5 bg-electric rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className="text-sm text-ink">{strength}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skill Gaps */}
          {gaps.length > 0 && (
            <div className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="font-semibold tracking-tight text-ink mb-1">Skill Gaps</h2>
              <p className="text-xs text-faint mb-4">
                Technologies worth learning based on your stack and market trends
              </p>
              <div className="space-y-3">
                {gaps.map((gap) => {
                  const style = GAP_CATEGORY_STYLES[gap.category] || GAP_CATEGORY_STYLES.recommended;
                  return (
                    <div
                      key={gap.id}
                      className="flex items-center justify-between p-3 border border-line rounded-lg hover:border-mute transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className={`font-mono text-[12px] px-2 py-0.5 rounded-md font-medium ${style.bg} ${style.text}`}>
                          {style.label}
                        </span>
                        <div>
                          <div className="font-medium text-sm text-ink">{gap.skill_name}</div>
                          <div className="text-xs text-faint mt-0.5">{gap.reason}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-line rounded-full h-1.5">
                          <div
                            className="h-full bg-gradient-to-r from-electric to-volt rounded-full"
                            style={{ width: `${gap.gap_score * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Growth Areas */}
          {snapshot.growth_areas && snapshot.growth_areas.length > 0 && (
            <div className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="font-semibold tracking-tight text-ink mb-4">Growth Recommendations</h2>
              <div className="space-y-3">
                {snapshot.growth_areas.map((area, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 bg-panel border border-line rounded-lg"
                  >
                    <div className="w-5 h-5 bg-electric rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 text-white text-xs font-bold font-mono">
                      {i + 1}
                    </div>
                    <span className="text-sm text-ink">{area}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Active repos */}
          {snapshot.raw_github_data?.top_repos?.length > 0 && (
            <div className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="font-semibold tracking-tight text-ink mb-4">Most Active Repositories</h2>
              <div className="space-y-2">
                {snapshot.raw_github_data.top_repos.map((repo, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-line last:border-0">
                    <div>
                      <span className="font-medium text-sm text-ink">{repo.name}</span>
                      {repo.description && (
                        <span className="text-xs text-faint ml-2">{repo.description}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-mute">
                      {repo.language && (
                        <span className="font-mono px-2 py-0.5 border border-line bg-panel rounded-md">{repo.language}</span>
                      )}
                      {repo.stars > 0 && <span className="font-mono">{repo.stars} stars</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="text-center text-xs text-faint pb-4">
            Last analyzed: {new Date(snapshot.snapshot_date).toLocaleDateString("en-US", {
              month: "long",
              day: "numeric",
              year: "numeric",
            })}
            {" "}&middot; Skill scores are relative, not absolute
          </div>
        </div>
      )}
    </div>
  );
}
