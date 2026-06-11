import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, test } from "node:test";
import { validateEvent } from "../src/events.js";
import { detectFrameworks, gitEvents, scanRepos, summarizeRepo } from "../src/importers/git.js";

test("detectFrameworks reads package.json deps and python manifests", () => {
  const found = detectFrameworks({
    "package.json": JSON.stringify({ dependencies: { react: "^18", "better-sqlite3": "^11" }, devDependencies: { zod: "^4" } }),
    "requirements.txt": "fastapi==0.110\nnumpy>=1.0\n",
  });
  assert.deepEqual(found.sort(), ["better-sqlite3", "fastapi", "numpy", "react", "zod"]);
});

test("detectFrameworks survives unparseable package.json", () => {
  assert.deepEqual(detectFrameworks({ "package.json": "{not json" }), []);
});

// ── real repo e2e ──
const dir = mkdtempSync(join(tmpdir(), "git-import-"));
const repo = join(dir, "myproject");

before(() => {
  execFileSync("git", ["init", "-q", repo]);
  const g = (...args: string[]) => execFileSync("git", ["-C", repo, ...args], { env: { ...process.env, GIT_AUTHOR_DATE: "2026-06-01T00:00:00Z", GIT_COMMITTER_DATE: "2026-06-01T00:00:00Z" } });
  g("config", "user.email", "test@example.com");
  g("config", "user.name", "Test");
  writeFileSync(join(repo, "package.json"), JSON.stringify({ dependencies: { react: "^18" } }));
  g("add", "-A");
  g("commit", "-qm", "init");
  writeFileSync(join(repo, "a.txt"), "x");
  g("add", "-A");
  g("commit", "-qm", "more");
});
after(() => rmSync(dir, { recursive: true, force: true }));

test("summarizeRepo counts the author's commits and detects frameworks", () => {
  const s = summarizeRepo(repo)!;
  assert.equal(s.repo, "myproject");
  assert.equal(s.commits, 2);
  assert.deepEqual(s.frameworks, ["react"]);
  assert.match(s.lastCommit, /^2026-06-01/);
});

test("scanRepos finds repos one level down from a parent folder", () => {
  const found = scanRepos(dir);
  assert.equal(found.length, 1);
  assert.equal(found[0]!.repo, "myproject");
});

test("gitEvents emits valid events: topic + skill with batch-undoable provenance", () => {
  const { events, batch } = gitEvents(scanRepos(dir));
  for (const e of events) validateEvent(e);
  const topic = events.find((e) => e.type === "signal.topic")!;
  assert.equal(topic.payload.topic, "myproject");
  assert.equal((topic.provenance as { batch?: string }).batch, batch);
  const skill = events.find((e) => e.type === "signal.skill")!;
  assert.equal(skill.payload.skill, "react");
  assert.equal(events.filter((e) => e.type === "system.import").length, 1);
});
