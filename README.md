# Persnally

**Your AI conversations already know what you care about. Persnally turns that into a personalized daily digest.**

An open-source MCP server that plugs into Claude, ChatGPT, or any MCP-compatible client. It passively learns your interests from natural conversation — no forms, no onboarding, no manual tagging — and delivers curated content straight to your inbox via Resend.

## The Insight

Every day you chat with AI about the things that matter to you — the framework you're debugging, the startup idea you're exploring, the investment thesis you're researching. That context is incredibly valuable, but it disappears when you close the tab.

Persnally captures structured signals from those conversations (never raw messages) and builds an evolving interest graph that gets smarter over time. Then it curates a daily digest of content matched to what you *actually* care about right now — not what you said you liked 6 months ago on a settings page.

## How It Works

```
You chat with Claude/ChatGPT as normal
        ↓
AI calls persnally_track with structured topic signals
        ↓
Local interest graph builds (decays, learns, balances)
        ↓
You trigger persnally_digest (or it runs on schedule)
        ↓
API curates fresh content matched to your interests
        ↓
Personalized digest arrives via Resend
```

**Zero onboarding.** The AI chat IS the preference engine.

## Quick Start

### 1. Install the MCP Server

```bash
npm install -g persnally-mcp
```

### 2. Add to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "persnally": {
      "command": "persnally-mcp"
    }
  }
}
```

### 3. Chat Naturally

Just talk to Claude. Persnally tracks topics in the background. When you're ready:

> "Set my Persnally email to alice@example.com"

> "Show me my Persnally interests"

> "Send me my digest"

That's it. No signup, no configuration wizard, no preference forms.

## MCP Tools

| Tool | What It Does |
|------|-------------|
| `persnally_track` | Extracts structured topic signals from conversation (called automatically by AI) |
| `persnally_interests` | Shows your current interest profile with weights, categories, and sentiment |
| `persnally_digest` | Generates and sends a personalized digest based on your interest graph |
| `persnally_config` | Configure email, digest frequency, API key |
| `persnally_forget` | Remove specific topics or clear all data (privacy control) |

## Interest Engine

The engine is designed to mirror how human interests actually work:

- **Exponential decay** (7-day half-life) — last week's Kubernetes deep-dive shouldn't dominate forever
- **Depth over frequency** — a 2-hour conversation about Rust outweighs 10 one-liner mentions
- **Sentiment awareness** — "I hate CSS" deprioritizes CSS in your digest, doesn't boost it
- **Balanced allocation** — if you're 60% tech, 30% business, 10% finance, your digest reflects that exact ratio
- **Intent classification** — learning vs building vs researching vs debugging produces different content
- **Entity extraction** — tracks specific tools, companies, and concepts, not just vague categories

## Privacy by Architecture

This isn't "we promise we don't read your messages." This is **structurally impossible** for raw conversations to leak:

- Only structured signals are stored: `{ topic, weight, category, intent, sentiment, entities }`
- Raw messages never touch disk, never leave your machine, never hit any API
- Interest graph lives locally at `~/.persnally/`
- Cloud sync is opt-in and only sends the structured graph
- Fully open source — verify it yourself

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Your AI Client (Claude Desktop / ChatGPT / etc.)       │
│                                                         │
│  You chat naturally. AI calls persnally_track when it   │
│  notices topics you care about. Zero extra AI cost —    │
│  Claude IS the NLP engine.                              │
└──────────────────────┬──────────────────────────────────┘
                       │ MCP Protocol (stdio)
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Persnally MCP Server (runs locally)                    │
│                                                         │
│  Interest Engine:                                       │
│  - Signal processing (weight × depth × sentiment)       │
│  - Exponential decay (half-life: 7 days)                │
│  - Category balancing (proportional allocation)         │
│  - Local persistence (~/.persnally/)                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS (opt-in)
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Persnally API (FastAPI on Railway)                     │
│                                                         │
│  - Receives interest graph                              │
│  - Multi-source research (GitHub, HN, news)             │
│  - AI curation (Claude Sonnet 4)                        │
│  - Quality validation (URL check, freshness, dedup)     │
│  - Email delivery via Resend                            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Web Dashboard (Next.js on Vercel)                      │
│                                                         │
│  - Skill DNA analysis (GitHub framework detection)      │
│  - Interest profile visualization                       │
│  - Digest history and preferences                       │
│  - GitHub OAuth (Supabase Auth)                         │
└─────────────────────────────────────────────────────────┘
```

## Skill DNA

Connect your GitHub and Persnally analyzes your actual code — not just stars or followers:

- **Framework detection** from dependency files (package.json, requirements.txt, Cargo.toml, go.mod)
- **Proficiency scoring** based on repo activity, recency, and code volume
- **Domain classification** across 10 categories (frontend, backend, AI/ML, DevOps, etc.)
- **Skill gap analysis** from starred repos and adjacent technologies
- **AI synthesis** via Claude for career narrative and growth areas

## Content Curation Pipeline

When you trigger a digest, the API runs a multi-stage pipeline:

1. **Interest graph analysis** — weighted, decayed, sentiment-adjusted topic extraction
2. **Multi-source research** — GitHub trending, HackerNews, tech news, opportunities
3. **AI matching** — Claude Sonnet 4 matches content to your specific interest signals
4. **Quality validation** — real URL verification, date freshness, spam detection, dedup
5. **Balanced allocation** — content distributed proportionally across your interest categories
6. **Email delivery** — clean, mobile-responsive HTML via Resend MCP

## Project Structure

```
persnally/
├── mcp_server/persnally/        # Open-source MCP server (npm package)
│   └── src/
│       ├── index.ts             # MCP tools (track, interests, digest, config, forget)
│       ├── interest-engine.ts   # Interest graph with decay + balancing
│       └── digest-client.ts     # API client for digest generation
├── api/                         # FastAPI backend (Railway)
│   ├── routers/
│   │   ├── digest.py            # Digest generation from interest graph
│   │   ├── skills.py            # Skill DNA analysis
│   │   ├── newsletters.py       # Newsletter management
│   │   └── ...
│   └── services/
│       ├── engine_bridge.py     # Curation engine integration
│       └── career_bridge.py     # Skill analyzer integration
├── src/                         # Core intelligence engine
│   ├── ai_engine.py             # AI curation with Claude Sonnet 4
│   ├── behavior_analyzer.py     # GitHub behavioral analysis
│   ├── content_validator.py     # Quality validation
│   ├── skill_analyzer.py        # Skill DNA framework detection
│   └── email_sender.py          # Resend email delivery
├── web/                         # Next.js frontend (Vercel)
│   └── src/app/
│       └── dashboard/
│           ├── page.tsx          # Career intelligence overview
│           └── skills/page.tsx   # Skill DNA visualization
└── templates/                   # Email HTML templates
```

## Tech Stack

- **MCP Server**: TypeScript, `@modelcontextprotocol/sdk`, Zod
- **API**: FastAPI, Python 3.11+
- **Frontend**: Next.js 16, Tailwind CSS
- **AI**: Claude Sonnet 4 (Anthropic API)
- **Email**: Resend MCP
- **Auth**: Supabase (GitHub OAuth)
- **Database**: Supabase PostgreSQL with RLS
- **Deploy**: Railway (API), Vercel (Web)

## Development

```bash
# MCP Server
cd mcp_server/persnally
npm install && npm run build
npm start

# API
cd api
pip install -r requirements.txt
uvicorn main:app --reload

# Web
cd web
npm install && npm run dev
```

## Environment Variables

### API (.env)
```bash
ANTHROPIC_API_KEY=       # Required — Claude API
RESEND_API_KEY=          # Required — email delivery
SUPABASE_URL=            # Required — database
SUPABASE_ANON_KEY=       # Required — client auth
SUPABASE_SERVICE_ROLE_KEY= # Required — server operations
GITHUB_TOKEN=            # Optional — higher rate limits
FRONTEND_URL=            # Production frontend URL
```

### MCP Server (environment or ~/.persnally/config.json)
```bash
PERSNALLY_API_URL=       # API endpoint (default: https://api.persnally.com)
PERSNALLY_API_KEY=       # API key for digest generation
```

## Built For

Resend MCP Hackathon — Built with Anthropic Claude API + Resend MCP for email delivery.

## License

MIT
