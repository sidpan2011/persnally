# Contributing to Persnally

Thanks for your interest! Persnally is source-available and contributions are welcome.

## Getting started

### Prerequisites

- Node.js >= 20
- (Optional) [Ollama](https://ollama.com) or an Anthropic API key — only if you're working on extraction/synthesis (imports run fully local with Ollama, or via your own key).

### Local development

```bash
git clone https://github.com/sidpan2011/persnally.git
cd persnally/persnallyd
npm install
npm run build
npm test          # node:test unit suite + protocol e2e
```

Run the daemon locally:

```bash
node build/src/cli.js setup
```

The marketing site lives in `web/` (Next.js):

```bash
cd web && npm install && npm run dev
```

## Project structure

```
persnallyd/   # the product + the published npm package (`persnally`):
              #   SQLite event store, extractors, importers, daemon, dashboard, MCP adapter
web/          # marketing site (Next.js -> Vercel)
docs/         # EVENT_SCHEMA.md, ARCHITECTURE.md
experiments/  # Phase-0 validation scripts (standalone)
```

## Submitting code

1. Fork and branch from the default branch.
2. Make focused changes — one feature or fix per PR.
3. Verify: `cd persnallyd && npm test && npm run build` (strict `tsc --noEmit` must be clean).
4. Open a PR with a clear description: what changed, why, how it was verified, known risks.

## Code style (TypeScript)

- Strict mode; no `any` unless unavoidable; explicit return types on public functions.
- Small, single-responsibility functions; obvious data flow.
- Comments only where code can't speak — a constraint, an invariant, a non-obvious *why*. Never narrate what the code does.
- Errors handled deliberately — no silent `catch`.

See [`CLAUDE.md`](./CLAUDE.md) for the full engineering bar.

## Reporting bugs / requesting features

Open an issue using the **Bug Report** or **Feature Request** template.

## Questions?

Open a GitHub discussion or an issue — happy to help you get started.
