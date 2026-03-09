# Contributing to Persnally

Thanks for your interest in contributing! Persnally is an open-source project and we welcome contributions of all kinds.

## Getting Started

### Prerequisites

- Node.js >= 18
- Python >= 3.11
- A Supabase project (free tier works)
- npm account (if publishing MCP server changes)

### Local Development Setup

**1. Clone the repo**

```bash
git clone https://github.com/sidpan2011/persnally.git
cd persnally
```

**2. MCP Server** (the core product)

```bash
cd mcp_server/persnally
npm install
npm run build
npm test        # runs E2E test
```

**3. API** (digest generation backend)

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
cd api && uvicorn main:app --reload
```

**4. Web** (dashboard frontend)

```bash
cd web
npm install
cp .env.example .env.local   # fill in your keys
npm run dev
```

## Project Structure

```
mcp_server/persnally/   # TypeScript MCP server (published to npm as "persnally")
api/                    # FastAPI backend (digest generation, scheduling)
web/                    # Next.js frontend (dashboard, onboarding)
src/                    # Python intelligence engine (AI curation, content sourcing)
templates/              # Email HTML templates
```

## How to Contribute

### Reporting Bugs

Open an issue using the **Bug Report** template. Include:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your environment (OS, Node version, Claude Desktop version)

### Suggesting Features

Open an issue using the **Feature Request** template. Describe the problem you're trying to solve, not just the solution you want.

### Submitting Code

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Run tests: `cd mcp_server/persnally && npm test`
4. Ensure TypeScript compiles: `npm run build`
5. Open a PR with a clear description of what changed and why

### What Makes a Good PR

- **Small and focused** — one feature or fix per PR
- **Tests included** — if you add logic, add a test case to `test-e2e.mjs`
- **No unrelated changes** — don't refactor code you didn't need to touch
- **Clear commit messages** — describe the "why", not just the "what"

## Code Style

### TypeScript (MCP Server)

- Strict mode enabled
- Use `const` over `let` where possible
- Explicit return types on public methods
- No `any` unless absolutely necessary

### Python (API / Engine)

- Type hints on function signatures
- Docstrings on public functions
- f-strings over `.format()`
- Keep functions under 50 lines where practical

## Areas Where Help is Needed

- **More MCP client support** — testing with ChatGPT, Cursor, and other MCP clients
- **Interest engine improvements** — better topic normalization, cross-topic relationships
- **Content sources** — adding new data sources for digest curation
- **Email templates** — better digest email designs
- **Tests** — unit tests for the interest engine and API endpoints
- **Documentation** — guides, tutorials, examples

## Questions?

Open a discussion on GitHub or reach out in issues. We're happy to help you get started.
