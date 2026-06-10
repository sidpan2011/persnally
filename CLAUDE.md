# Persnally — Project Guide (v2)

> **Full strategy lives in [PIVOT.md](./PIVOT.md). This file is the always-loaded summary — keep it short.**

## What we're building (v2)

**Persnally is a local-first personal context engine.** It learns who you are from your AI activity and makes every AI tool and agent personally yours — without any single platform owning your data.

**One-liner:** *The giants build the intelligence. Persnally makes it yours.*

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

## Roadmap (see PIVOT.md for detail)

- **Phase 0 — Validate:** capture-rate test + import "describe me" prototype + event schema. Go/no-go on the wow moment.
- **Phase 1 — The Mirror:** `persnallyd` + importers + descriptive profile + dashboard. Show HN launch.
- **Phase 2 — The Layer:** MCP context server (`get_context`/`record_event`) + per-client permissions. North star: **context reads/user/week**.
- **Phase 3 — The Loop:** one agent-facing decision loop (`ask_user_model`), ≥90% precision gate. Feedback closes itself via approvals/vetoes.
- **Phase 4 — Business:** encrypted sync paid tier → teams later. Raise on Phase 2 retention or the Phase 3 demo.

**Current phase: 0 (pre-build) — pivoting off the digest product.**

## Codebase map: KEEP vs CUT

The repo is mid-pivot from the old product (AI-conversation interest tracker → daily email digest). When working here:

**KEEP & EVOLVE**
- `mcp_server/persnally/src/interest-engine.ts` — the crown jewel; decay/weighting/sentiment logic becomes one extractor over the v2 event log.
- `mcp_server/persnally/src/index.ts` — MCP scaffolding; `track`/`interests`/`forget` → `record_event`/`get_context`/delete.
- `src/skill_analyzer.py` + `src/repo_analyzer.py` — GitHub analysis = import-based cold start (Phase 1 importer, ~80% built).
- `src/topic_utils.py`, `src/cache.py` — generic infra, no upward deps.
- Supabase auth (`api/middleware/auth_middleware.py`, `api/services/supabase_client.py`, `web/src/lib/supabase/*`) — for Phase 4 sync.
- `src/behavior_analyzer.py` — salvage the extraction approach for Phase 3 (currently GitHub-only; rewrite I/O).

**CUT (email/digest/curation — being removed)**
- Email: `src/email_sender.py`, `templates/`, `mcp_server/resend/` (submodule), `src/mcp_clients/`, `src/image_fetcher.py`, `src/content_formatter.py`.
- Curation: `src/ai_engine.py`, `content_curator.py`, `content_validator.py`, `opportunity_matcher.py`, `web_opportunity_finder.py`, `smart_user_analyzer.py`, `system_prompts.py`.
- Content sourcing: all of `data_sources/`.
- Digest API: `api/routers/digest.py`, `api/routers/newsletters.py`, `api/services/scheduler.py`, `api/services/engine_bridge.py`, `src/main.py`.

**Greenfield (does not exist yet)** — the hardest gaps: the event-log schema, the `persnallyd` daemon, the CLI, the local dashboard, and the Claude/ChatGPT export importers.

## Deployment (current, pre-pivot)

- Web (Next.js) → Vercel · API (FastAPI) → Railway (nixpacks, not Dockerfile) · MCP → npm as `persnally`.
- Repo is **private** until the v2 launch. Keep PIVOT.md internal; publish a sanitized `ROADMAP.md` at Phase 1 launch.

## Known issues (from audit — fix or carry-forward into v2)

- Interest decay double-counts frequency (`interest-engine.ts` `raw_weight` grows unbounded + frequency bonus) — fix when porting to the event log.
- `dominant_intent` takes latest signal, not most-frequent (comment says otherwise).
- Zero Python tests; only one manual `.mjs` MCP test. v2 needs a real test harness.
