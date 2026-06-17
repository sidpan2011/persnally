# Persnally — Project Guide (v2)

> **Locked vision lives in [docs/VISION.md](./docs/VISION.md) — the fixed reference; don't re-litigate it. Full strategy lives in [PIVOT.md](./PIVOT.md). Status lives in [PROGRESS.md](./PROGRESS.md) — update it on every meaningful step. This file is the always-loaded summary — keep it short.**

## What we're building (v2)

**Persnally is a local-first personal context engine.** It learns who you are from your AI activity and makes every AI tool and agent personally yours — without any single platform owning your data.

**Brand kit** (use the right line for the surface):
- Pitch (deck/positioning): *The giants build the intelligence. Persnally makes it yours.*
- Tagline (CLI/site hero/README): *So every AI finally knows you.*
- Descriptor (npm/GitHub/HN): *Your own context engine — local-first, across every AI.*
- Competitive contrast: *Everyone says your context is "yours." Persnally keeps it on your machine.* (Old "for agents vs for you" line retired — cross-vendor rivals (Plurality, Maximem) now say "for you" too; the real differentiator is **custody**: they hold it in their cloud, we keep it local + auditable + deletable. See [docs/VISION.md](./docs/VISION.md).)

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
6. **Trust product:** local-first, source-available (auditable), structured data only, inspectable, deletable. This is the credibility of neutrality — not optional.
7. **Cloud as amplifier, never as custodian.** Cloud services (sync, hosted compute, teams) may carry ciphertext and run opt-in stateless jobs — they never hold plaintext custody of user data. Crossing this line deletes our answer to "why not supermemory."

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
- **Phase 4 — Business:** hybrid cloud-as-amplifier. Free: full local engine (BYOK). Pro: zero-setup inference (we pay the model bill), agent relay (cloud agents + phones reach your context, E2E), reflection reports, encrypted backup, maintained connectors. Teams later. Licensing: FSL engine (auditable, fork-proof, →MIT after 2y) + open event-schema/MCP spec + closed cloud. Raise on Phase 2 retention or the Phase 3 demo.

**Current phase: 1 — The Mirror** (persnallyd built; validating — cold demos + capture-rate verdict — before Phase 2).

## Codebase map

The v1 Python/Supabase backend (FastAPI `api/`, the `src/` analyzers, `supabase/` migrations, Railway deploy) was **removed** — v2 is local-first TypeScript and used none of it; its salvage logic (repo→skill detection) already lives in `persnallyd/src/importers/git.ts`. Git history preserves it; Phase 4 cloud is rebuilt to the E2E doctrine, not revived from here. What's in the tree:

- `persnallyd/` — **the product** AND the published npm package (`persnally`, bins: `persnally`/`persnallyd`/`persnally-mcp`): SQLite event store, decay + profile extractors, importers (claude, claude-code, chatgpt, git), daemon + dashboard, and the thin MCP adapter at `src/mcp/` (no local state; the daemon is the single source of truth). All engine work lands here.
- `web/` — the marketing site (Next.js → Vercel). `web/src/lib/supabase/*` is kept as dormant auth scaffolding for Phase 4 sync; nothing imports it yet.
- `experiments/` — Phase-0 validation tooling (`capture_rate.py`, `describe_me.py`), standalone, stdlib + ad-hoc deps.
- `docs/` — [VISION.md](./docs/VISION.md) (locked), [EVENT_SCHEMA.md](./docs/EVENT_SCHEMA.md), [ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Deployment

- `persnally` → npm (the product). Marketing site (`web/`) → Vercel.
- The Railway-hosted FastAPI API was **removed** with the v1 backend; Phase 4 cloud is greenfield, built to the cloud-as-amplifier doctrine.
- Repo is **private** until the v2 launch. Keep PIVOT.md internal; publish a sanitized `ROADMAP.md` at Phase 1 launch.
