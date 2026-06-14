# Show HN — launch kit

> Post Tue–Thu, ~8–10am US Eastern (catches the US morning + EU afternoon). Be in the thread all day; the founder answering hard questions live is half the value of a Show HN.

## Title (pick one)

HN titles reward plain description over hype. Recommended first:

1. **Show HN: Persnally – a local-first context engine so every AI knows you** *(recommended: descriptive, leads with local-first — the differentiator HN cares about)*
2. Show HN: Persnally – own your AI context across Claude, ChatGPT, and Cursor
3. Show HN: Persnally – I imported my ChatGPT history and it described me from the data

Avoid superlatives ("best", "revolutionary") — they invite the cynics first.

## Post body

```
Persnally is a local-first personal context engine. You point it at your AI
history — Claude/ChatGPT exports, your Claude Code sessions, your git repos —
and it builds a structured, evidence-linked model of who you are, then serves
that to any AI tool over MCP so they stop treating you like a stranger.

Why I built it: every AI I use is brilliant and amnesiac. ChatGPT doesn't know
what I told Claude. My coding agent relearns my stack every session, or
interrupts me to ask. The fix isn't a smarter model — it's a layer underneath
all of them that holds *me*, that I own. The model vendors won't build this:
they can't share your context with each other, and their business is keeping
you inside their walls. So it has to be neutral, and it has to be yours.

How it works:
- An append-only SQLite event log on your machine is the single source of
  truth. Your profile and interest graph are *derived views* — re-derivable,
  and deletable for real (forgetting a topic removes its events and everything
  inferred from them, then rebuilds; no tombstones).
- Every claim in your profile links to the exact events behind it. The
  dashboard's "why does it think this?" is a lookup, not an LLM guess.
- Reads never call a model — serving context to an AI is an instant, offline,
  free SQLite query. Models run only at import and synthesis (bring your own
  key, or run fully local via Ollama — nothing leaves the machine).
- A loopback-only daemon; an MCP server any client connects to.

Try it:
  npm i -g persnally && persnally setup

It finds your exports, reads your local Claude Code sessions and git repos,
synthesizes a profile, wires up your AI clients, and opens a local dashboard.

What it is NOT yet: the behavior model. Today it's descriptive — it characterizes
how you work and decide, with evidence. The next stage is an agent being able to
ask "what would they want here?" instead of guessing — but I'm not claiming that
before it's earned. It's source-available (FSL, converts to MIT in 2y); the event
schema and MCP interface are an open spec.

I'd genuinely like the teardown: the data model, the privacy boundary, the
"is this just a memory file?" question. Fire away.
```

## The anchoring first comment (post immediately after, as OP)

This sets the technical tone and preempts the four questions that will come regardless:

```
A few things I expect to come up, so let me get ahead of them:

**"Isn't this just Mem0 / a memory file?"** Memory products are dev infra —
an app developer bolts memory onto *their* agent, in *their* cloud, scoped to
*their* app. Persnally inverts that: one store the user owns, N clients with
scoped, revocable views into it. And the data model is different — it's not a
key-value fact store, it's an event log with intent/sentiment/decay/decisions
over time, because the goal is eventually "what would this person do?", which
you can't answer from a pile of facts. A fact store is one `SELECT` away from
this; this is not one query away from a fact store.

**"What actually leaves my machine?"** Only the text you send to your own LLM
during import/synthesis (BYOK), and you can avoid even that by running Ollama
locally. Serving context to your AI tools is a local SQLite read — no network.
The daemon binds 127.0.0.1 only. I did a full security pass before launching
(CSRF/DNS-rebinding hardening, the key file is mode-0600, dashboard output is
escaped, 0 dependency CVEs) — happy to go deep on any of it.

**"Why now / why MCP?"** MCP is the model vendors' own protocol, so this rides
their ecosystems instead of fighting them. And as agents multiply, every new
agent needs to know its user — the neutral context layer gets more useful as
the world gets more plural, not less.

**Honest limitations:** single machine today (no sync yet — that's a Phase 4,
E2E-encrypted, never-plaintext-in-our-cloud thing). MCP client identity is
self-reported, so per-client scoping assumes honest local clients for now. The
behavior model is roadmap, not shipped. Profile quality scales with how much AI
history you have — there's a fallback for thin histories so it never degrades to
a LinkedIn summary, but more data = sharper mirror.
```

## Rebuttal bank (keep handy for the thread — don't post unless asked)

- **"Privacy theater — it still sends my data to Anthropic."** Only at import/synthesis, only the text you choose, BYOK — and the Ollama path sends nothing off-machine. Serving (the thing that happens constantly) is local. The boundary is documented in the README.
- **"Local-first is a liability — I'll lose it if my laptop dies."** Correct, today. Encrypted backup + multi-device is the first paid service on the roadmap, E2E so we never hold plaintext. The free local engine is never crippled to push it.
- **"The giants will just build this."** They structurally can't build the *cross-vendor* version — Anthropic won't serve OpenAI's agents your context. Every tool they ship makes fragmentation worse, which is the problem this solves.
- **"How is the profile not just horoscope-general?"** Every sentence cites the events it's derived from — click through in the dashboard. If it can't point to evidence, it doesn't say it. (If someone's demo profile *is* generic, that's the thin-history case — say so honestly.)
- **"Self-reported client identity means scoping is fake."** Fair for a hostile local process; the threat model today is "your own machine, honest clients." Per-client tokens land with the agent relay. Not oversold in the docs.

## Pre-flight checklist (the morning of)

- [ ] Public repo is live and clean (no PIVOT.md / internal docs in its history) — see DEMO_KIT shot list note
- [ ] README "Repository" link on npm resolves (currently 404s while private)
- [ ] CI badge restored in the public repo's README
- [ ] `npm i -g persnally && persnally setup` works on a clean machine (re-verify the day of)
- [ ] Dashboard screenshot + setup GIF ready (shot list in DEMO_KIT.md)
- [ ] Cold-demo gate passed (≥3/5 startled) — do NOT launch otherwise
- [ ] Security review (this kit) linkable for the "is it safe?" question
- [ ] Founder blocked out the full day to answer the thread
```
