# Changelog

All notable changes to Persnally will be documented in this file.

## [2.4.0] - 2026-06-25

### Added
- **Mobile dashboard.** The interest constellation is now fully touch-driven (single-finger drag, pinch-to-zoom, tap-to-inspect, via pointer events), the layout reflows for phones, and narrow screens open to the topic list with the map one tap away. The trust surface is now usable on the device most launch traffic arrives on — it was inert on touch before.
- **Real provenance in the dashboard's "why?".** Each piece of evidence now names where it actually came from — the conversation it was imported from, the live client + session that recorded it, or the repo — instead of collapsing everything to a bare `mcp`/filename label.

### Fixed
- **Re-import is idempotent.** `persnallyd import claude|chatgpt|claude-code` now dedupes by conversation id and `import git` by repo, so re-running an import only adds genuinely new items instead of doubling every interest weight. (`setup` and the daemon auto-import were already safe; the explicit one-shot commands were not.)
- **Large exports fail clearly, not catastrophically.** An import file over 400 MB is refused with an actionable message instead of an opaque out-of-memory crash during `readFileSync`/`JSON.parse`.
- The dashboard footer now shows the running daemon version (was a permanently blank slot).
- Docs: corrected stale `get_context`/`record_event` tool names to `persnally_context`/`persnally_track` in `ARCHITECTURE.md` and `CONTEXT_DEPTH.md`; the README importer diagram now lists `claude-code`.

## [2.3.2] - 2026-06-21

### Added
- **Automatic capture of new chats** — the daemon now ingests new Claude Code sessions on its background loop (every 30 min, plus an immediate pass on startup), so your context keeps growing with zero action and no dependence on the model remembering to call `persnally_track`. Incremental: sessions already in the store are skipped by conversation id, so nothing is re-imported or duplicated.

### Fixed
- Import extraction is now resilient per conversation — a single malformed model response (e.g. an out-of-enum value) is skipped and retried on the next pass instead of aborting the entire import batch.

## [2.3.1] - 2026-06-20

### Fixed
- SessionStart hook now instructs Claude to call `persnally_track` at end-of-session — fixes 0% live capture rate where the model had context injected but no prompt to track signals back.

## [2.3.0] - 2026-06-21

> Note: `2.2.0` was published to npm but its release commit (version bump + this
> changelog entry) never landed on `dev` — a branch got abandoned mid-rework and
> the bump went with it. This entry covers everything shipped since `2.1.0`,
> including what `2.2.0` actually contained, so the record here matches reality.

### Added
- **Voice & convention layer** — a deterministic, zero-token stylometry pass over your own prose (repeated phrases, sentence tone, hedging, format) plus live capture as you chat via `persnally_track`'s `style[]`, distilled into a "voice" pack that `persnally_context` injects so connected tools answer in your style. New `signal.style` event type, `GET /voice`, `persnallyd voice` (offline refresh).
- **Deletable, for real** — forgetting a voice/style pattern (`DELETE /voice/:dimension/:pattern`, `persnally_forget`'s `style` param, `persnallyd forget --style`, or the `×` on a dashboard voice chip) writes a permanent correction so it stays forgotten even if stylometry or live capture would otherwise re-derive it. Nightly consolidation now also prunes the style backlog so live capture can't grow unbounded.
- **Redesigned local dashboard** — hero self-portrait, "since you last looked" deltas, "what your AIs read about you" receipts, reflections, a "How you write" voice section, and an interactive interest constellation.

### Fixed
- Import pipeline strips pasted paths/URLs/logs and injected blocks before extraction — cleaner topics and profile.
- A zip export that fails to read (missing `unzip`, corrupt archive, permission denied) during `persnally setup` is now surfaced, not silently treated as "no conversations found."

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
