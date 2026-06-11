# Persnally v2 — Progress

> Living tracker. Update on every meaningful step: what shipped, what was learned, what's next.
> Strategy: [PIVOT.md](./PIVOT.md) · Standards: [CLAUDE.md](./CLAUDE.md) · Schema: [docs/EVENT_SCHEMA.md](./docs/EVENT_SCHEMA.md)

**Current phase: 1 — The Mirror** (build started 2026-06-11; Phase 0 capture-rate verdict still pending ~June 25)

## Phase 0 scoreboard

| Workstream | Status | Verdict / Notes |
|---|---|---|
| Import "describe-me" prototype | ✅ Done (2026-06-11) | **GO** — cleared the "startling" bar on a 9-conversation export. See findings below |
| Capture-rate test | 🟡 Running (started 2026-06-11) | Instrumented MCP server live in Claude Code, Claude Desktop, Cursor. Analyze ~June 25: `python experiments/capture_rate.py --since 2026-06-11 --export <fresh-export>` |
| Event schema | ✅ Done (2026-06-11) | [docs/EVENT_SCHEMA.md](./docs/EVENT_SCHEMA.md) — append-only log, derived views, provenance graph, hard-delete privacy |
| Competitive landscape check | ✅ Done (2026-06-11) | Mem0 $24M/AWS-exclusive (dev infra), Rewind→Meta exit, screenpipe YC S26 (capture). Open seat: user-owned cross-vendor context layer |

### Phase 0 exit criteria (from PIVOT.md)
- [x] Import demo produces a "holy shit" reaction — *self-test passed; show 3–5 developer friends cold for the full gate*
- [ ] Viable passive-capture path in ≥2 major clients — *capture-rate test running, verdict ~June 25*
- [x] Written event schema + architecture doc

## Phase 1 scoreboard

| Deliverable | Status | Notes |
|---|---|---|
| `persnallyd` skeleton | ✅ Done (2026-06-11) | Event store (SQLite/WAL per EVENT_SCHEMA.md), Claude importer, CLI, loopback HTTP daemon. 13 tests green. E2E-verified against the real export: 79 events, topics view correct |
| Decay/extraction port from interest-engine | ✅ Done (2026-06-11) | `decay.ts`: per-signal decay (fixes raw_weight double-count + dominant-intent bug). Verified on real data: stale March topics correctly decayed below fresh June ones |
| Descriptive profile synthesis | ✅ Done (2026-06-11) | `persnallyd profile` → Fable 5 via structured outputs → `view_profile`, each section evidence-linked to event ids. Served at `GET /profile`. Real run produced a startling profile from structured events alone |
| ChatGPT + git importers | ✅ Done (2026-06-11) | Shared extraction pipeline (`extract.ts`). ChatGPT: mapping-tree parser, fixture-tested (no real export on hand — verify on first real one). Git: fully deterministic/offline, repos→topics + manifests→skills, batch-undoable; real-run verified (persnally repo, 58 commits → top of graph at 0.73) |
| Local dashboard | ✅ Done (2026-06-11) | Single static page served by the daemon at `localhost:4983` — profile with per-section "why does it think this?" provenance walk, decayed topic bars, per-topic hard-delete, re-synthesize button. No framework, no second app. 28 tests (daemon HTTP layer now covered) |
| Signal-density floor | 🟡 Mostly done | Git importer (offline, key-free) covers the developer case; `setup` auto-imports ~/Projects. Remaining: 1–2 question fallback when everything is thin |

## Phase 2 scoreboard (started early — entrance via MCP v2)

| Deliverable | Status | Notes |
|---|---|---|
| MCP server as daemon client | ✅ Done (2026-06-11) | v2 rewrite: 4 tools (`track`/`context`/`interests`/`forget`), daemon is single source of truth, v1 graph auto-migration, protocol e2e vs mock daemon + live round-trip verified. Dual-source-of-truth debt eliminated |
| `persnally_context` read loop | ✅ Live | Any MCP client now gets the real profile + decayed topics |
| Per-client permission scoping | ⬜ | All clients currently see everything |
| `persnally connect <client>` one-command setup | ✅ Done (2026-06-12) | `persnallyd connect [client\|--all]` + full `persnallyd setup` onboarding (find exports → import → synthesize → connect → open dashboard) |
| Nightly consolidation pass | ⬜ | From ARCHITECTURE.md — reflection + behavior assertions |

## Key findings log

**2026-06-11 — Describe-me experiment (GO):**
- Output inferred unstated behavioral patterns (idea generation accelerating when the main bet stalls; optionality hoarding across finances and focus) — synthesis, not summary. This is the product's wow moment, evidenced.
- `memories.json` + project metadata are **S-tier signal** (highest value per byte). Importers must treat platform-memory exports as first-class.
- **Signal-density floor needed:** thin/low-signal histories will produce flat portraits. Phase 1 requires a fallback (git history, more sources, or 1–2 questions) so the demo never degrades to a LinkedIn summary.
- claude.ai exports do NOT include Claude Code sessions — local `~/.claude/projects` transcripts are a separate, often richer corpus for developers.

## Shipped

| Date | What |
|---|---|
| 2026-06-11 | Pivot decided + PIVOT.md (PR #7) · repo private until launch |
| 2026-06-11 | Codebase audit (security/correctness/architecture, 3 agents) |
| 2026-06-11 | v2 teardown: −8.9k LOC email/digest/curation, Resend submodule removed, deps pruned (PR #11) · old feature PRs #8/#9/#10 closed with salvage notes |
| 2026-06-11 | CLAUDE.md: v2 concept + engineering standards (PR #12) |
| 2026-06-11 | `experiments/describe_me.py` — proto-importer (export dir/json/zip → profile) |
| 2026-06-11 | MCP telemetry (`telemetry.ts`) + `experiments/capture_rate.py` · local build registered in 3 clients |
| 2026-06-11 | Event schema designed (`docs/EVENT_SCHEMA.md`) + this tracker |
| 2026-06-11 | `persnallyd` skeleton: event store + Claude importer + CLI + daemon, 13 tests, e2e on real export (PR #13, merged) |
| 2026-06-11 | Brand kit locked: pitch / tagline ("So every AI finally knows you") / descriptor ("The context engine for you") / competitive contrast — applied to CLI, packages, GitHub about |
| 2026-06-11 | The Mirror loop complete: decay port + profile synthesis (`persnallyd profile`, `GET /profile`), 22 tests (PR #14, merged). Key learning: Fable 5 rejects forced tool_choice — moved all extraction to structured outputs (`messages.parse` + `zodOutputFormat`), deleting the hand-rolled schema converter |
| 2026-06-11 | CI overhauled for v2: persnallyd job added (was zero CI), dead Docker job + Dockerfiles/compose deleted, API boot smoke check, concurrency cancellation. Full pipeline <1 min |
| 2026-06-11 | docs/ARCHITECTURE.md: eight invariants, learning model, behavioral-model trajectory + eval harness |
| 2026-06-11 | Business doctrine locked: hybrid cloud-as-amplifier (never plaintext custody), FSL licensing + open spec, Pro value ladder (zero-setup inference → agent relay → reflection → behavior model). PIVOT.md Phase 4 + CLAUDE.md principle 7 |
| 2026-06-12 | Importers complete: ChatGPT (mapping-tree parser) + git (deterministic/offline, repos→topics, manifests→skills), shared extraction pipeline (PR #17) |
| 2026-06-12 | Daemon lifecycle: start/stop/pidfile/launchd autostart (PR #18). Live on machine #1 — launchd-owned, KeepAlive verified. Dogfooding caught the RunAtLoad-vs-running-daemon retry loop; autostart now hands over. Known gap: launchd daemon has no ANTHROPIC_API_KEY → config file needed (launch prep) |
| 2026-06-12 | Key wall killed (PR #19): local Ollama extraction (chooser: key → local → guidance; live-verified on real export via llama3.2, zero bytes left machine), `config set-key` (mode-600 file) for the launchd daemon |
| 2026-06-12 | One-command onboarding (PR #19): `persnallyd setup` (auto-detect exports incl. zips, import, git, synthesize, connect clients, open dashboard, idempotent) + `connect [client\|--all]` |
| 2026-06-12 | FSL-1.1-MIT license under **0byte lab**; README rewritten for v2; public ROADMAP.md (PR #19) |
| 2026-06-12 | One npm package: `persnally@2.0.0` — MCP server folded into `persnallyd/src/mcp/`, bins `persnally`/`persnallyd`/`persnally-mcp`, `mcp_server/` deleted, CI folded. Dry-run clean. **Publish blocked by npm 24h unpublish cooldown until 2026-06-12 19:54 UTC (01:25 IST Jun 13)** — auth/2FA already verified |
| 2026-06-12 | ⚠️ GitHub Actions stopped queuing runs repo-wide (~19:41 UTC) — likely private-repo minutes/billing; check github.com/settings/billing. Local suite is the gate meanwhile |

## Next up

1. **Publish `persnally@2.0.0`** after the npm cooldown lifts (2026-06-12 19:54 UTC / 01:25 IST Jun 13): `cd persnallyd && PATH="$HOME/.nvm/versions/node/v22.19.0/bin:$PATH" npm publish --otp=CODE`
2. **Merge PR #19**; restore GitHub Actions (billing check).
3. **Cold demos to 3–5 developers** — `npm i -g persnally && persnally setup` is now the whole script. The real Phase 0/1 exit gate.
4. **~June 25:** capture-rate analysis (needs fresh Claude export) → passive-accrual verdict.
5. **Build:** density-floor question fallback · per-client permission scoping · nightly consolidation pass.

## Known issues / carry-forward

- Interest decay double-counts frequency in `interest-engine.ts` (`raw_weight` unbounded + frequency bonus) — fix when porting to event-log extractor.
- `dominant_intent` takes latest signal, not most-frequent.
- No real test harness yet (one manual `.mjs` e2e); v2 code gets tests from day one per CLAUDE.md standards.
- npm `persnally` v1.0.0 still live with old digest description — republish at Phase 1 launch.
