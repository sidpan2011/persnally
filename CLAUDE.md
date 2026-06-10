# Persnally — Project Guide (v2)

> **Full strategy lives in [PIVOT.md](./PIVOT.md). Status lives in [PROGRESS.md](./PROGRESS.md) — update it on every meaningful step. This file is the always-loaded summary — keep it short.**

## What we're building (v2)

**Persnally is a local-first personal context engine.** It learns who you are from your AI activity and makes every AI tool and agent personally yours — without any single platform owning your data.

**One-liner (pitch):** *The giants build the intelligence. Persnally makes it yours.*
**Tagline (product):** *So every AI finally knows you.*

We are **not** competing with Claude/ChatGPT/Cursor. We sit **on top of them** via MCP (their own protocol) as the neutral, user-owned context layer they structurally can't build for each other.

## Form factor

| Surface | Role |
|---|---|
| `persnallyd` (daemon) | The product. Always-on local process: event store, context graph, behavior model, feedback loop. |
| MCP server | Primary interface — **consumed by AIs** (Claude/Cursor/agents read context + write events). |
| `persnally` CLI | Developer window: `init`, `import`, `show`, `forget`, `export`, `status`. |
| Local dashboard | Trust surface (`localhost`): inspect what it knows, provenance, delete. The shareable "wow" artifact. |

Distribution: CLI-installed · daemon-architected · MCP-consumed · dashboard-trusted.

## Non-negotiable principles

1. **Never build what a model vendor will bundle** (chat UIs, generic memory, routing). Build what their business models forbid: cross-vendor context, user-owned data, local execution.
2. **No new phase until the previous one shows a retention curve.** Scope discipline = survival.
3. **User interaction budget ≈ zero after day one.** Win by being in the default path, invisible.
4. **Descriptive → predictive → prescriptive.** Earn each rung. No prediction before description is eerily good.
5. **Cold start by import, not accrual.** The wow moment must land within 5 minutes of install.
6. **Trust product:** local-first, open source, structured data only, inspectable, deletable. This is the credibility of neutrality — not optional.

## Engineering standards (non-negotiable)

We're building the best-engineered product in this market. Every change is held to this bar:

**Code**
- Industry best practices, always. Performant, robust, prod-ready from the first commit — no "fix it later" code.
- **Minimal and simple beats clever.** Smallest design that solves the problem; delete code aggressively; no speculative abstractions.
- Maintainability is a feature: clear naming, small functions, single responsibility, obvious data flow.
- **Comments only where code can't speak** — a constraint, an invariant, a non-obvious why. Never narrate what code does. Human-readable, short, to the point: max 2–3 lines per block. No changelog/attribution comments.
- Errors handled deliberately: no bare `except` / silent swallowing (the old codebase died of this). Fail loud or degrade gracefully on purpose, never by accident.

**Process — before every commit / PR**
1. **Test first.** Run relevant tests; write them for new behavior. Unverified code doesn't get pushed.
2. **Self-audit the diff.** Re-read every changed line: security (auth, injection, secrets), correctness (edge cases, async/await, None-handling), leftovers (debug prints, dead code, stray comments).
3. **Lint/type-check clean:** ruff (Python), strict `tsc --noEmit` (TypeScript). Zero warnings shipped.
4. Small, focused PRs with honest descriptions: what changed, why, how it was verified, known risks.

## Roadmap (see PIVOT.md for detail)

- **Phase 0 — Validate:** capture-rate test + import "describe me" prototype + event schema. Go/no-go on the wow moment.
- **Phase 1 — The Mirror:** `persnallyd` + importers + descriptive profile + dashboard. Show HN launch.
- **Phase 2 — The Layer:** MCP context server (`get_context`/`record_event`) + per-client permissions. North star: **context reads/user/week**.
- **Phase 3 — The Loop:** one agent-facing decision loop (`ask_user_model`), ≥90% precision gate. Feedback closes itself via approvals/vetoes.
- **Phase 4 — Business:** encrypted sync paid tier → teams later. Raise on Phase 2 retention or the Phase 3 demo.

**Current phase: 0 (pre-build) — pivoting off the digest product.**

## Codebase map (post-teardown)

The old digest product (email/curation/content-sourcing, ~8.9k LOC) was **removed** in the v2 teardown (PR #11). What remains:

**KEEP & EVOLVE**
- `mcp_server/persnally/src/interest-engine.ts` — the crown jewel; decay/weighting/sentiment logic becomes one extractor over the v2 event log.
- `mcp_server/persnally/src/index.ts` — MCP scaffolding; `track`/`interests`/`forget` → `record_event`/`get_context`/delete.
- `src/skill_analyzer.py` + `src/repo_analyzer.py` — GitHub analysis = import-based cold start (Phase 1 importer, ~80% built).
- `src/topic_utils.py`, `src/cache.py` — generic infra, no upward deps.
- `api/routers/digest.py` — gutted to interest-graph `/sync` + `/interests` + `/stats` only; rename prefix to `/context` in Phase 1.
- Supabase auth (`api/middleware/auth_middleware.py`, `api/services/supabase_client.py`, `web/src/lib/supabase/*`) — for Phase 4 sync.
- `src/behavior_analyzer.py` — salvage the extraction approach for Phase 3 (currently GitHub-only; rewrite I/O).

**Reference (closed PR branches on remote, not merged):** `feat/cloudflare-real-content`, `feat/digest-feedback-loop`, `feat/github-seed-onboarding` (its repo→topic-category mapping feeds the Phase 1 git importer).

**Greenfield (does not exist yet)** — the hardest gaps: the `persnallyd` daemon, the CLI, the local dashboard, and the production importers. The event schema is designed: [docs/EVENT_SCHEMA.md](./docs/EVENT_SCHEMA.md) — append-only event log, derived views, provenance graph. All v2 persistence work builds on it.

## Deployment (current, pre-pivot)

- Web (Next.js) → Vercel · API (FastAPI) → Railway (nixpacks, not Dockerfile) · MCP → npm as `persnally`.
- Repo is **private** until the v2 launch. Keep PIVOT.md internal; publish a sanitized `ROADMAP.md` at Phase 1 launch.

## Known issues (from audit — fix or carry-forward into v2)

- Interest decay double-counts frequency (`interest-engine.ts` `raw_weight` grows unbounded + frequency bonus) — fix when porting to the event log.
- `dominant_intent` takes latest signal, not most-frequent (comment says otherwise).
- Zero Python tests; only one manual `.mjs` MCP test. v2 needs a real test harness.
