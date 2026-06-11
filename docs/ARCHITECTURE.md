# Persnally v2 — Architecture of Record

> The product wins through structural properties, not features. Every PR should be
> auditable against the invariants below. Schema detail: [EVENT_SCHEMA.md](./EVENT_SCHEMA.md).
> Strategy: [../PIVOT.md](../PIVOT.md). Status: [../PROGRESS.md](../PROGRESS.md).

## Why architecture is the moat

| Property | Why incumbents structurally can't copy it |
|---|---|
| Local-first | Memory-layer companies are cloud businesses; going local deletes their revenue model |
| Cross-vendor | Platform memory exists *to* lock in; vendors won't share user context with rivals |
| Provenance-complete | Memory trained into weights or summarized into blobs can never answer "why do you think this?" |
| Truly unlearnable | Hard-delete + re-derive requires an event-sourced core; retrofitting it is a rewrite |

A feature-clone built on a cloud aggregation store is a different product that loses
every trust argument. Boring technology, radical properties.

## Target topology

```
  AI clients (Claude, Cursor, agents...)        importers (claude, chatgpt, git...)
        │  MCP: get_context / record_event            │  parse (pure) → extract (LLM) → events
        ▼                                              ▼
  ┌─────────────────────────── persnallyd ─────────────────────────────┐
  │   EVENT LOG (SQLite/WAL) ──── the only source of truth             │
  │        │                                                           │
  │        ▼ extractors (decay, assertions, skills, behavior model)    │
  │   DERIVED VIEWS (topics, profile, …) ── always re-derivable        │
  │        ▲                                                           │
  │   hard-delete walks the provenance graph, then re-derives          │
  └───────────────┬────────────────────────────────────────────────────┘
                  │ loopback HTTP — the single access path
        dashboard · CLI · (Phase 4: E2E-encrypted sync; cloud never sees plaintext)
```

## The eight invariants

1. **The event log is the single source of truth.** Views are cattle; events are sacred.
   This makes unlearning, schema migration (drop-and-rederive), and audit free, not features.
2. **Every derived claim cites its evidence.** Provenance is a walkable graph; "why does
   it think this?" is a lookup, never an LLM guess.
3. **Deletion is first-class and total** — matching events plus derived descendants, then
   rebuild. No tombstones carrying content.
4. **One write path.** The daemon owns the database. MCP server, CLI, and dashboard are
   clients of the daemon, never of the file.
5. **Protocols are adapters, not foundations.** MCP is a thin edge file; if the protocol
   landscape shifts, the edge is re-skinned in days and the core never knows.
6. **Deterministic core, LLM at the edges.** Models run only at ingest (extraction) and
   synthesis (profile/reflection). Every read is deterministic, instant, free, offline —
   agents consulting context cannot pay model latency per consult.
7. **Closed, versioned event types.** Unknown types fail loudly. Payload changes bump
   versions; migrations re-derive views.
8. **Minimal dependency surface.** Runtime deps: `better-sqlite3`, `zod`, `@anthropic-ai/sdk`.
   Each absent dependency is supply-chain risk and upgrade tax we don't pay.

## How it learns (agentic / RAG / feedback / "daily training")

- **Agents consume us; the core is not agentic.** We serve agents (`get_context`,
  Phase 3 `ask_user_model`); we use bounded LLM passes at the edges; reads never think.
- **RAG: we are the R.** From every client's perspective Persnally is the retrieval layer
  for the user. Structured retrieval (weights, kinds, time) is built; embeddings arrive as
  a derived view only when `search_context` needs fuzzy lookup — re-derivable, local,
  deletable like everything else.
- **The feedback loop is first-class in the schema:** `feedback.signal`
  (approved/edited/vetoed), `user.correction` (highest authority — outranks any inference),
  `context.read` (what actually gets consumed). Phase 3 makes it self-closing: every
  approval or veto of an agent action is a labeled example, recorded as an event.
- **Learning happens in data space, never weight space.** No fine-tuning on user data:
  trained weights can't cite evidence (breaks #2) or unlearn (breaks #3). Instead the
  engine learns by re-derivation — new events in, extractors re-run, decay shifts,
  corrections override, profile re-synthesizes. Same "trained daily" outcome; inspectable,
  reversible, cheap.
- **Nightly consolidation (roadmap):** a scheduled daemon pass that ingests the day's
  events, re-derives views, emits `signal.assertion` events of kind `behavior` for
  detected patterns, re-synthesizes the profile when enough changed, and prunes.
  Sleep consolidation, locally, while the user sleeps.

## The behavioral model trajectory

The north star: a model of the user faithful enough to guide — and eventually act — from
*their* lens. It is built out of this architecture, not beside it:

- **Descriptive (rung 1, shipping):** the synthesized profile — characterizes how the user
  works and decides, with evidence.
- **Predictive (rung 2):** "what would they do?" — answered from accumulated decision
  events. Requires data only Phases 2–3 can collect: `context.read`, `feedback.signal`,
  `user.correction` at decision granularity. **The behavior model is downstream of
  distribution.**
- **Prescriptive (rung 3):** acts on the user's behalf. Gated behind measured fidelity.
- **The eval harness (Phase 3 deliverable):** hold out real decisions the user made; the
  model predicts them blind; agreement is scored. "Realistic like me" must be a number
  that goes up, or it's marketing.

Capture rule that protects this future: **record at decision granularity** — a choice
made, an option rejected — not only topic summaries. Over-aggregation at ingest is the
one mistake the future model cannot undo.

## Current state vs target (2026-06-11)

**Standing, tested, CI-gated:** event log (UUIDv7, closed type set v1) · Claude importer
with provenance · decay extraction (v1 double-count bug fixed) · profile synthesis with
evidence citations · rederivable versioned views · loopback daemon + dashboard + CLI.

**Known gaps, in order of architectural urgency:**

1. **Dual source of truth (worst debt):** the v1 MCP server still writes
   `~/.persnally/interest-graph.json` while v2 owns `persnally.db` — violates invariant #1
   on live data. Fix = MCP v2 rewrite as a thin daemon client + one-time migration.
2. **Daemon lifecycle is manual:** no pidfile / `stop` / autostart. "Always-on" is the
   form-factor promise; today it's "process you remember to run."
3. **Rebuild is O(all events) in memory:** fine to ~100k events; incremental derivation
   needed before the event log gets large. Don't build features that assume rebuilds stay cheap.
4. **No encryption at rest:** acceptable pre-launch; Phase 4 sync requires E2E encryption
   with user-held keys (cloud never sees plaintext).
5. **CLI opens the db directly** (acceptable while single-user/local; converge on the
   daemon as the only writer when lifecycle work lands).
