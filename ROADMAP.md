# Roadmap

Where Persnally is going. The aim: a personal context engine you fully own, that makes every AI tool understand *you* — and eventually one that can reason and act from your perspective.

We build in stages, and each stage has to earn the next.

## Now — The Mirror ✅

Install it, point it at your AI history, and see yourself.

- Local daemon (`persnallyd`) with an append-only event store — your data, on your machine
- Importers: Claude export, ChatGPT export, git history
- Decay-weighted interest graph (recent interests outweigh stale ones)
- Synthesized profile where every claim cites its evidence
- Local dashboard — inspect everything, delete anything
- MCP server so any AI client can read your context

## Next — The Layer

Your context, in every tool you use.

- One-command connect for Claude, Cursor, Claude Code, and other MCP clients
- Per-client scopes — decide what each tool can see
- Nightly local consolidation: your engine reflects on the day's activity and updates itself while you sleep
- More importers and a graceful fallback when your history is thin

## Later — The Loop

Your context starts working *for* you.

- An agent can ask your engine "what would they want here?" instead of guessing or interrupting you
- A behavior model with a visible, measured fidelity score — earned, not claimed
- Every approval, edit, and veto teaches it, automatically

## Always

- **Local-first.** Custody of your data stays with you.
- **Cloud as amplifier, never custodian.** Optional paid services (sync, multi-device, hosted compute, teams) carry encrypted data and run on your behalf — they never hold your plaintext.
- **Source-available & inspectable.** Audit the engine; verify the claims.
- **Deletable for real.** Forgetting removes the data and everything derived from it.

---

Have a use case or a client you want supported? Open an issue.
