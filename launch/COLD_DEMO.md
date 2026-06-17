# Cold-demo runbook

> Internal launch kit. **Goal:** in one sitting, get a developer to say *"I want this
> running on my machine"* — not *"neat."* That sentence is the Phase-0/1 exit gate.

## The framing (locked by the 2026-06 validation)

Lead with the **self-portrait**, not "it learns as you chat." Passive capture measured
~0% organic, and "the agent remembers facts across sessions" is now a free Markdown
extension (pi-mem et al.). The wow that's *yours* and can't be gotten free: **a
startling, evidence-linked model of who you are, in 5 minutes, that every tool reads.**

## Pre-flight (never do this live)

- Confirm you're on the current build: `persnally --version` + `curl -s http://127.0.0.1:4983/health`.
- Pre-open your dashboard (`http://127.0.0.1:4983`) and read your profile cold. If a
  section is flat or embarrassing, `persnallyd forget <topic>` or re-synthesize
  **before** showing. A LinkedIn-grade profile kills the wow.
- If installing on their machine: have them export Claude/ChatGPT data to `~/Downloads`
  **ahead of time** (the export takes minutes). For 3–5 friends, show *yours* first;
  let the eager ones install after.
- Decide the mode: live-install (riskier, more convincing) vs. show-your-dashboard (safer).

## The 5-minute script

1. **Hook (15s):** "Every AI forgets you. I built something that learns who I am from my
   own history and feeds it to all of them. Watch." No architecture talk.
2. **Wow beat (90s):** open the dashboard. Read 2–3 *startling* lines aloud — the
   **inferences**, not the facts. Let them react. *This is the demo.*
3. **Trust beat (60s):** click *"why does it think this?"* → show the evidence events.
   "Not guessing — every line traces to something I actually did, all local, and here's
   the delete button."
4. **Cross-tool beat (45s):** "and now Claude, Cursor, my agents all read this — set
   once, every tool knows me." Show `persnally_context` returning the profile in a
   connected client.
5. **Close (15s):** "Want it on yours?" → a yes is the GO.

## Don'ts (these tank it)

- Don't lead with "it learns as you chat" — it mostly doesn't (~0% organic). Lead with import.
- Don't show a thin/flat profile — pre-check and fix it first.
- Don't explain the event log / MCP / architecture before the wow. Wow first, mechanism only if asked.
- Don't claim "nothing leaves your machine" unqualified — say "stored only on your
  machine; extraction runs through your own key, or fully local with Ollama."
- Don't demo on a stale install — verify `persnally --version` before every demo.

## The verdict

- **GO:** ≥3 of 5 install, or ask "can it do X for my workflow."
- **Soft:** "neat" with no install intent → the wow isn't deep enough; the fix is the
  person-model / receipts, not more features.
- **Always:** write down the exact reactions — they pick which deepening move to build next.
