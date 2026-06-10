# Persnally v2 — Progress

> Living tracker. Update on every meaningful step: what shipped, what was learned, what's next.
> Strategy: [PIVOT.md](./PIVOT.md) · Standards: [CLAUDE.md](./CLAUDE.md) · Schema: [docs/EVENT_SCHEMA.md](./docs/EVENT_SCHEMA.md)

**Current phase: 0 — Validate** (started 2026-06-11)

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

## Next up

1. **Show the describe-me output to 3–5 developer friends** (cold) — the real exit-criterion test.
2. **~June 25:** run capture-rate analysis (fresh Claude export needed for the Desktop denominator) → Phase 0 verdict: is passive accrual a complement or does import carry v2 alone?
3. **Phase 1 prep** (only after Phase 0 closes): `persnallyd` skeleton — SQLite event store per schema, Claude-export importer as first event producer, `persnally` CLI (`init|import|show|forget`).

## Known issues / carry-forward

- Interest decay double-counts frequency in `interest-engine.ts` (`raw_weight` unbounded + frequency bonus) — fix when porting to event-log extractor.
- `dominant_intent` takes latest signal, not most-frequent.
- No real test harness yet (one manual `.mjs` e2e); v2 code gets tests from day one per CLAUDE.md standards.
- npm `persnally` v1.0.0 still live with old digest description — republish at Phase 1 launch.
