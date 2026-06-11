/**
 * Git history importer — fully deterministic, no LLM, works offline.
 * Repos become project topics; manifest dependencies become skill signals.
 * Carries forward the v1 skill_analyzer's framework-detection approach.
 */

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { basename, join } from "node:path";
import { newEvent, uuidv7, type PersnallyEvent } from "../events.js";

export interface RepoSummary {
  repo: string;
  path: string;
  commits: number;
  firstCommit: string;
  lastCommit: string;
  frameworks: string[];
}

const FRAMEWORKS: Record<string, string> = {
  // js/ts
  react: "frontend", next: "frontend", vue: "frontend", svelte: "frontend", "solid-js": "frontend",
  tailwindcss: "frontend", express: "backend", fastify: "backend", hono: "backend", nestjs: "backend",
  "better-sqlite3": "backend", prisma: "backend", drizzle: "backend", zod: "backend",
  "@modelcontextprotocol/sdk": "ai_ml", "@anthropic-ai/sdk": "ai_ml", openai: "ai_ml", langchain: "ai_ml",
  electron: "desktop", "react-native": "mobile", expo: "mobile",
  // python
  fastapi: "backend", django: "backend", flask: "backend", sqlalchemy: "backend", pydantic: "backend",
  torch: "ai_ml", tensorflow: "ai_ml", transformers: "ai_ml", anthropic: "ai_ml", pandas: "data",
  numpy: "data", "scikit-learn": "data",
  // other ecosystems (manifest presence)
  cargo: "systems", "go.mod": "backend",
};

/** Pure: manifest filename → content → detected framework names. */
export function detectFrameworks(manifests: Record<string, string>): string[] {
  const found = new Set<string>();
  for (const [name, content] of Object.entries(manifests)) {
    if (name === "package.json") {
      try {
        const pkg = JSON.parse(content) as { dependencies?: Record<string, string>; devDependencies?: Record<string, string> };
        for (const dep of Object.keys({ ...pkg.dependencies, ...pkg.devDependencies })) {
          if (FRAMEWORKS[dep]) found.add(dep);
        }
      } catch { /* unparseable manifest — skip, not fatal */ }
    }
    if (name === "requirements.txt" || name === "pyproject.toml") {
      for (const fw of Object.keys(FRAMEWORKS)) {
        if (new RegExp(`\\b${fw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(content)) found.add(fw);
      }
    }
    if (name === "Cargo.toml") found.add("cargo");
    if (name === "go.mod") found.add("go.mod");
  }
  return [...found];
}

function git(repoPath: string, args: string[]): string {
  return execFileSync("git", ["-C", repoPath, ...args], { encoding: "utf-8", stdio: ["ignore", "pipe", "ignore"] }).trim();
}

export function summarizeRepo(repoPath: string, authorEmail?: string): RepoSummary | null {
  if (!existsSync(join(repoPath, ".git"))) return null;
  const author = authorEmail ?? git(repoPath, ["config", "user.email"]);
  if (!author) return null;

  const log = git(repoPath, ["log", `--author=${author}`, "--format=%aI", "--no-merges"]);
  if (!log) return null;
  const dates = log.split("\n");

  const manifests: Record<string, string> = {};
  for (const name of ["package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod"]) {
    const p = join(repoPath, name);
    if (existsSync(p)) manifests[name] = readFileSync(p, "utf-8");
  }

  return {
    repo: basename(repoPath),
    path: repoPath,
    commits: dates.length,
    firstCommit: dates[dates.length - 1]!,
    lastCommit: dates[0]!,
    frameworks: detectFrameworks(manifests),
  };
}

/** A path is either a repo or a directory of repos — resolve to repo summaries. */
export function scanRepos(path: string, authorEmail?: string): RepoSummary[] {
  const direct = summarizeRepo(path, authorEmail);
  if (direct) return [direct];
  return readdirSync(path, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => { try { return summarizeRepo(join(path, d.name), authorEmail); } catch { return null; } })
    .filter((s): s is RepoSummary => s !== null);
}

export function gitEvents(summaries: RepoSummary[]): { events: PersnallyEvent[]; batch: string } {
  const batch = uuidv7();
  const events: PersnallyEvent[] = [];
  const activity = (commits: number) => Math.min(Math.log2(commits + 1) / 8, 1);

  for (const s of summaries) {
    events.push(newEvent("signal.topic", "import:git", {
      topic: s.repo,
      weight: Math.max(activity(s.commits), 0.1),
      intent: "building",
      sentiment: "neutral",
      depth: s.commits > 50 ? "deep" : s.commits > 10 ? "moderate" : "mention",
      category: "technology",
      entities: s.frameworks.slice(0, 10),
    }, { kind: "git", repo: s.repo, batch }, s.lastCommit));

    for (const fw of s.frameworks) {
      events.push(newEvent("signal.skill", "import:git", {
        skill: fw,
        domain: FRAMEWORKS[fw] ?? "other",
        proficiency: activity(s.commits),
        basis: `repo-activity:${s.repo}`,
      }, { kind: "git", repo: s.repo, batch }, s.lastCommit));
    }
  }

  events.push(newEvent("system.import", "system", {
    importer: "git",
    batch,
    events: events.length,
  }, { kind: "import", batch, file: summaries.map((s) => s.repo).join(",") }));

  return { events, batch };
}
