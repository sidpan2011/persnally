# Changelog

All notable changes to Persnally will be documented in this file.

## [2.1.0] - 2026-06-20

### Added
- `persnally context [--full|--hook]` — emits your profile + interests for AI injection and records a context read (the serving path for the SessionStart hook).
- Auto-install of a Claude Code SessionStart hook on `connect` / `setup`, so every session injects your context automatically. Idempotent; leaves other tools' hooks untouched.

### Fixed
- Atomic config writes (temp file + rename) when registering MCP clients and installing the Claude Code hook — a crash mid-write can no longer corrupt a user's config.

> 2.0.0 (June 2026) was the v2 local-first rewrite — SQLite event store, loopback daemon, importers, embedded dashboard, daemon-backed MCP. The v1 entry below predates it.

## [1.0.0] - 2026-03-10

### Added
- MCP server with 5 tools: `persnally_track`, `persnally_interests`, `persnally_digest`, `persnally_config`, `persnally_forget`
- Interest graph engine with exponential decay (7-day half-life)
- Sentiment-aware topic weighting (negative sentiment deprioritizes)
- Depth scoring (mention, moderate, deep)
- Intent tracking (learning, building, researching, deciding, discussing, debugging)
- Topic normalization ("React.js" / "React JS" / "ReactJS" merge to single node)
- Balanced allocation across interest categories
- Atomic file writes with .tmp + rename pattern
- Backup recovery from .bak files
- Stale node pruning (every 50 signals)
- Digest API with background job processing
- API key and Supabase JWT authentication
- Interest graph → user profile conversion for curation engine
- Automated digest scheduler (hourly check, daily/weekly sends)
- Fresh content sourcing from GitHub Search API and HackerNews
- Synonym-aware relevance validation (46-domain synonym map)
- 120s pipeline timeout to prevent hung jobs
- TTL caching on external API calls (1-hour default)
- Web dashboard with onboarding, skill DNA, newsletters, preferences
- Landing page with MCP-native messaging
- Published to npm as `persnally`
