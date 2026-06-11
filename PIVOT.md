# Persnally — Pivot Plan

**From:** AI-conversation interest tracker → email digest
**To:** The personal context engine — a local daemon that learns who you are from your AI activity and makes every AI tool and agent personally yours.

**One-liner:** *The giants build the intelligence. Persnally makes it yours.*

---

## Strategic Foundation (decided)

| Decision | Choice |
|---|---|
| Position | Neutral, user-owned context layer **on top of** all AI platforms — never competing with them |
| Mechanism | MCP — the giants' own protocol; they can't close it without breaking their ecosystems |
| Category language | "Personal context engine" / "the context layer" — never "digital twin" publicly |
| Brand | Persnally everywhere: `persnally` CLI, `persnallyd` daemon, npm, GitHub, domain — one spelling, all surfaces |
| Form factor | Local **daemon** (the product) + MCP server (primary interface, consumed by AIs) + CLI (dev window) + local dashboard (trust surface) |
| Beachhead | Developers — densest machine-readable event streams, earliest agent adopters, MCP-native distribution |
| Trust posture | Local-first, source-available (auditable), structured data only, inspectable, deletable. Non-negotiable — it's the credibility of neutrality |
| Business model | Hybrid, cloud-as-amplifier (decided 2026-06-11): free local engine (FSL) → Pro cloud services (never plaintext custody) → teams. See Phase 4 |
| Licensing | FSL on the engine (auditable + fork-proof, converts to MIT after 2y, Sentry's model) · event schema + MCP interface genuinely open spec · cloud services closed. Decided 2026-06-12: licensor **0byte lab**; v1 npm (MIT) already shipped and stays MIT |
| Macro bet | A multi-model world. Every quarter the market stays plural, our data gravity grows |

### Operating principles

1. **Never build what a model vendor will bundle** (chat UIs, generic memory, model routing). Always build what their business models forbid (cross-vendor context, user-owned data, local execution).
2. **No new phase until the previous one has a retention curve.** This is platform-scale ambition; scope discipline is survival.
3. **The user's interaction budget is ~zero after day one.** Persnally wins by being in the default path — set once, consulted forever, invisible.
4. **Descriptive → predictive → prescriptive.** Earn each rung. Never promise prediction before description is eerily good.
5. **Solve cold start by import, not accrual.** The wow moment must happen within 5 minutes of install.

### The engine pipeline

The internal architecture of `persnallyd`, mapped to the phases that ship each stage:

```
[Event Stream] → [Structured Memory] → [Pattern Extraction] → [Behavior Model]
→ [Decision Engine] → [Action / Suggestion] → [Feedback Loop] ↺
```

| Stage | Ships in | Implementation |
|---|---|---|
| Event Stream | Phase 0–1 | Event schema (Phase 0's key artifact). Sources: MCP `record_event` from connected AI tools + importers (Claude/ChatGPT exports, git history) |
| Structured Memory | Phase 1 | SQLite event store + context graph, provenance-linked, inspectable, deletable |
| Pattern Extraction | Phase 1 | Extraction passes over the event log → descriptive profile. `interest-engine.ts` decay/sentiment logic survives as one extractor |
| Behavior Model | Phase 3 | Preferences, tendencies, approval patterns, style constants. Descriptive → predictive, in that order |
| Decision Engine | Phase 3 | `ask_user_model(question)` with confidence thresholds; below threshold → "ask the human" |
| Action / Suggestion | Phase 3 | Agents first (answers degrade gracefully), proactive human suggestions last (wrong = Clippy) |
| Feedback Loop ↺ | Phase 3 | Every approval/edit/veto flows back as a labeled event — closes itself, no manual labeling |

Two deliberate deviations from the raw pipeline:
1. **Phase 2 (The Layer) sits between Structured Memory and Behavior Model** — raw context read-back via MCP. No modeling, but it's where daily retention comes from, funding the patience the later stages need.
2. **Stages ship demand-side, not top-down** — stages 4–7 are gated behind Phase 2's retention curve. Building the whole pipeline before users feel stage 2 is the failure mode operating principle #2 guards against.

---

## Phase 0 — Validate Before Building (2–3 weeks)

**Goal:** Kill the riskiest assumptions with evidence, not code.

### Workstreams

1. **Capture-rate test.** Instrument the existing MCP server across Claude Desktop, Claude Code, and Cursor for 2 weeks of real personal usage. Measure: what % of conversations produce signals passively? Do tool-approval prompts break the "ambient" promise per client?
2. **Import prototype (throwaway code).** Parse a Claude export + ChatGPT export. Feed to Claude API with a "describe this person: how they work, decide, communicate" prompt. Question: is the output *startling* or merely accurate? This is the entire Phase 1 bet in one experiment.
3. **Event schema design.** Define the foundational data model — generic `Event` (source, type, payload, timestamp, provenance), not just interest signals. Everything downstream is a view over the event log. This is the most important technical artifact of the pivot.
4. **Landscape check.** One honest week: what do Mem0/OpenMemory, screenpipe, Letta actually ship *for end users* today? Where exactly is the gap we claim?

### Exit criteria (go/no-go)

- Import demo produces a "holy shit" reaction from ≥3 of 5 developer friends shown it cold.
- A viable passive-capture path exists in at least 2 major clients (even if it needs a hook/instructions file).
- Written event schema + 1-page architecture doc.

**If the import demo is merely "neat" — stop and rethink. Everything depends on it.**

---

## Phase 1 — The Mirror (6–8 weeks)

**Goal:** Ship the descriptive engine. Install → import → "it knows me better than my LinkedIn does" in 5 minutes.

### Build

- **`persnallyd`** — local daemon: event store (SQLite), context graph builder, local HTTP for dashboard. Evolve the existing interest engine into the event-sourced model (decay/weighting/sentiment logic carries over as one extractor among several).
- **Importers** — Claude export, ChatGPT export, git history (`~/.gitconfig` + repo log mining). Browser history as stretch.
- **Pattern extraction v1 (descriptive)** — local-or-API LLM passes over events → structured profile: interests, projects, working patterns, communication style, decision tendencies. Confidence-scored, provenance-linked.
- **Dashboard (localhost)** — the trust surface and the screenshot moment: profile visualization, "why does it think this?" provenance view, per-item delete, full export.
- **CLI** — `persnally init | import | show | forget | export | status`. One-command install (`npm i -g persnally` / `brew`).

### Repo transition

- Email + digest → **cut entirely**: email sender, templates, Resend MCP submodule, scheduler send loop, and the whole content-sourcing pipeline (`fresh_content_generator`, `content_validator`, `data_sources/`) that existed to fill it. Email may return later as a re-engagement tactic (e.g. monthly "what Persnally learned" note) — a marketing feature, never architecture.
- Vercel web app → becomes marketing site + docs. Product UI moves to the local dashboard.
- Railway API → out of the critical path entirely. Parked for Phase 4 (sync).
- npm package keeps the `persnally` name — continuity of installs.

### Launch

Open-source launch: Show HN + X thread. The hook: **"I imported my ChatGPT history and this is what it knows about me."** The dashboard screenshot is the viral artifact.

### Metrics / exit criteria

- 1,000+ installs in first month post-launch.
- ≥40% of installers complete an import (funnel health).
- Organic screenshot-shares happening without prompting.
- **Kill signal:** installs spike but imports don't complete → the wow isn't landing; fix or halt.

---

## Phase 2 — The Layer (8–10 weeks)

**Goal:** Persnally in the default path. Every AI tool the user touches reads their context. This is where the retention curve must appear.

### Build

- **MCP context server** — `get_context(scope)`, `search_context(query)`, `record_event(...)`. Any MCP client connects; conversations both consume and feed the graph (solves passive capture: reading context *is* the session, writing back is part of the protocol).
- **Scoping & permissions** — per-client grants (Cursor gets work context, not health). Permission UI in the dashboard. This is a trust product; granularity is a feature, not overhead.
- **Context packs** — pre-composed bundles: "who I am," "current projects," "my stack & conventions," "writing voice." Optimized for system-prompt injection.
- **One-command client setup** — `persnally connect claude|cursor|...` writes the MCP config. Friction here is fatal.

### Metrics / exit criteria

- **North star: context reads per user per week** (proxy for "in the default path").
- 30-day retention of connected users ≥40%.
- Median user has ≥2 connected clients (the cross-tool moat becoming real).
- **Kill signal:** users install, connect one client, reads decay to zero in two weeks → the context isn't improving their AI outputs enough. Fix quality before building Phase 3.

---

## Phase 3 — The Loop (10–12 weeks)

**Goal:** One agent-facing decision loop, precision-obsessed. Persnally answers questions *about you* so agents stop guessing and stop interrupting.

### Build

- **The loop (one, for developers):** agents query `ask_user_model(question)` — "would they want tests with this?", "what tone for this email?", "approve this dependency?" Persnally answers from the behavior model with confidence; below threshold it returns "ask the human."
- **Behavior model v1** — preference/tendency extraction over the event log: approval patterns, style constants, risk tolerance, schedule rhythms. Descriptive→predictive on this narrow slice only.
- **Feedback loop, structurally free:** every agent action the user approves/edits/vetoes is a labeled example flowing back as events. No manual labeling asked of users, ever.
- **Precision dashboard** — public-facing honesty about how often Persnally's answers were right. Trust products earn the right to act by showing their error rate.

### Metrics / exit criteria

- Answer precision ≥90% on high-confidence responses (below that = Clippy; agents/users disable it).
- Measurable interruption reduction in an agent workflow (the demo: same agent task with/without Persnally, count the questions).
- **Rule:** no proactive *suggestions to the human* until this agent-facing loop holds precision. Acting on humans is the last rung, not the next one.

---

## Phase 4 — The Business (parallel from late Phase 2)

**Goal:** Convert position into a company. **Doctrine (2026-06-11): hybrid — cloud as amplifier, never as custodian.** The cloud may carry ciphertext and run opt-in stateless jobs; it never holds plaintext custody. Template: Tailscale (private data plane, paid coordination layer).

**Free forever (the flywheel):** the full local engine — import, graph, profile, MCP serving, dashboard, deletion — BYOK for inference. Never crippled: every free user compounds data gravity (switching cost) and never has the wow paywalled.

**Pro (~$8–15/mo) — value ladder, in conversion order:**
1. **Zero-setup inference** — we carry the model bill; no API key. The funnel-killer remover; converts "works if technical" → "works." (Day-one viable)
2. **Agent relay** — E2E, scoped per-client tokens: cloud agents, CI runners, and phones reach your context beyond loopback. Where the orthogonality thesis cashes out as revenue. (Phase 2)
3. **Reflection service** — scheduled consolidation upgraded to self-knowledge reports: "what changed about you," behavior patterns over time. The WHOOP-for-your-mind product. (Phase 2–3)
4. **The behavior model** — `ask_user_model`, drafting in your voice, with a visible fidelity score from the eval harness. The eventual flagship. (Phase 3)
5. **Continuity insurance** — encrypted backup + point-in-time restore of the db that is, by month six, your accumulated self. Lowest-churn purchase in consumer software. (Day-one viable)
6. **Maintained connectors** — continuous one-click importers that keep working when export formats break. Maintenance is a service.

**Never paid:** local MCP serving, dashboard, deletion/privacy controls, the core graph. Charging for privacy is brand suicide; crippling the local loop kills the flywheel.

- **Teams (later, deliberate):** org context layer — "how does this team decide/build/communicate" — fed by individual opt-in; org sees derived views, never raw events. Big-market slide; do not start before Phase 3 holds.
- **Licensing:** FSL on the engine (read/audit/run free; can't be resold as a competing service; converts to MIT after 2 years — "everything we ship becomes fully open on a delay"). Event schema + MCP interface: genuinely open spec (the standard others build against). Cloud services: closed. Precedents: Sentry (FSL), Tailscale, 1Password and Obsidian (closed, local-first, trusted) — auditability is what trust requires, not OSI purity.
- **Fundraise timing:** raise on Phase 2 traction (retention curve + north-star growth) or early Phase 3 (the agent-loop demo is the strongest artifact: *watch this agent stop asking me questions*). Deck arc: wedge (Mirror) → layer (default path) → loop (agents) → the context layer for all AI. "Twin" appears nowhere; the vision slide is the category: **the personal context engine**.

---

## Risk Register

| Risk | Mitigation |
|---|---|
| Platforms bundle memory features | Neutrality + cross-vendor span + local ownership — structurally unavailable to any single vendor. Track quarterly, answer in deck |
| Import demo underwhelms | Phase 0 kills this for $0 before any real build |
| Tool-approval friction breaks ambient capture | Phase 2's read-path makes capture part of normal MCP usage; hooks/instruction files as fallback |
| Misspelled-brand search leakage | Own adjacent domains/spellings; dev audience meets the brand in written form (npm/GitHub/configs) |
| Privacy incident = existential | Local-first by default, structured data only, provenance + delete everywhere, security review before each launch |
| Solo-founder scope drift | Operating principle #2: no new phase without a retention curve. This file is the contract |

---

## Timeline (aggressive but honest, solo + AI leverage)

| Phase | Duration | Cumulative |
|---|---|---|
| 0 — Validate | 2–3 wks | ~3 wks |
| 1 — The Mirror | 6–8 wks | ~3 mo |
| 2 — The Layer | 8–10 wks | ~5–6 mo |
| 3 — The Loop | 10–12 wks | ~8–9 mo |
| 4 — Business | parallel | — |

Two launch moments: **Phase 1** (Show HN, the screenshot) and **Phase 3** (the agent demo, the raise).
