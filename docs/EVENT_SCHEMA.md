# Persnally v2 — Event Schema

> Phase 0 design artifact. Everything downstream — context graph, profile, behavior model —
> is a **derived view over the event log**. Views can always be deleted and re-derived;
> events are the only source of truth.

## Design principles

1. **Append-only, with hard delete.** Events are never mutated. The one exception to purity:
   user deletion is a *hard* delete (privacy trumps event-sourcing), followed by view re-derivation.
2. **Structured signals only.** Payloads carry extracted structure, never raw conversation text.
   Provenance *points* at the source; it doesn't copy it.
3. **Every claim is traceable.** The dashboard's "why does it think this?" resolves any profile
   assertion → extraction event(s) → provenance → original source location.
4. **Closed type set, versioned.** Unknown event types are rejected, not silently stored.
   New types require a schema version bump.

## Storage

SQLite at `~/.persnally/persnally.db` (WAL mode). One write path: the daemon. Readers (CLI,
dashboard, MCP server) go through the daemon's API, never the file directly.

```sql
CREATE TABLE events (
  id          TEXT PRIMARY KEY,   -- UUIDv7: time-ordered, globally unique
  ts          TEXT NOT NULL,      -- ISO 8601 UTC, when the event occurred
  recorded_at TEXT NOT NULL,      -- when the daemon persisted it (differs for imports)
  source      TEXT NOT NULL,      -- see Sources
  type        TEXT NOT NULL,      -- see Event types
  payload     TEXT NOT NULL,      -- JSON, shape fixed per type
  provenance  TEXT NOT NULL,      -- JSON pointer to origin (see Provenance)
  schema_ver  INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_events_ts   ON events (ts);
CREATE INDEX idx_events_type ON events (type, ts);
CREATE INDEX idx_events_src  ON events (source, ts);
```

Derived state (context graph, profile) lives in separate tables prefixed `view_`,
each carrying the `event_id`s it was derived from. `persnally rebuild` drops and
re-derives all views from the log.

## Sources

`source` identifies who produced the event:

| Source | Meaning |
|---|---|
| `mcp:<client>` | Live MCP session (`mcp:claude-code`, `mcp:claude-desktop`, `mcp:cursor`, ...) — client name from the MCP handshake |
| `import:claude` | Claude data export importer |
| `import:claude-code` | Claude Code local transcripts importer (`~/.claude/projects`) |
| `import:chatgpt` | ChatGPT data export importer |
| `import:git` | Git history importer |
| `cli` | User action via `persnally` CLI |
| `dashboard` | User action via local dashboard |
| `system` | Daemon itself (migrations, rebuilds) |

## Event types (v1)

### `signal.topic` — extracted interest/topic signal
The workhorse. Produced by live MCP tracking and by importers. Payload mirrors the
proven `TopicSignal` shape from v1's interest engine:

```jsonc
{
  "topic": "rust async programming",   // normalized key is derived, not stored
  "weight": 0.8,                       // 0–1, centrality to the source conversation
  "intent": "debugging",               // learning|building|researching|deciding|discussing|debugging
  "sentiment": "negative",             // positive|negative|neutral
  "depth": "deep",                     // mention|moderate|deep
  "category": "technology",
  "entities": ["tokio", "axum"]
}
```

### `signal.assertion` — extracted claim about the person
Produced by importers and profile synthesis (the describe-me pipeline). The unit of the
descriptive profile.

```jsonc
{
  "claim": "ships V1s fast across domains but stalls before customer contact",
  "kind": "behavior",        // fact|preference|behavior|skill|context
  "confidence": 0.7,         // extractor's confidence, 0–1
  "evidence": "pattern across 8 abandoned project artifacts"
}
```

### `signal.skill` — detected technical skill
From the git/GitHub importer (v1 `skill_analyzer` logic).

```jsonc
{ "skill": "fastapi", "domain": "backend", "proficiency": 0.6, "basis": "repo-activity" }
```

### `context.read` — an AI client consumed context (Phase 2)
```jsonc
{ "scope": "projects", "client_purpose": "system-prompt injection", "items": 12 }
```

### `agent.question` / `agent.answer` — decision loop (Phase 3)
```jsonc
// agent.question
{ "question": "would the user want tests included?", "asker": "mcp:cursor" }
// agent.answer
{ "question_id": "<event id>", "answer": "yes", "confidence": 0.92, "deferred": false }
```

### `feedback.signal` — the loop closes (Phase 3)
```jsonc
{ "subject_id": "<event id of answer/suggestion>", "verdict": "approved" }  // approved|edited|vetoed
```

### `user.correction` — user edited/contradicted the profile
From dashboard/CLI. Highest-authority signal; extractors must weight it above inference.

```jsonc
{ "target_id": "<event id or view assertion id>", "action": "delete", "reason": "wrong" }
```

### `system.import` — import batch marker
```jsonc
{ "importer": "claude", "batch": "<uuid>", "events": 412, "source_span": ["2024-10-01", "2026-06-11"] }
```

## Provenance

Every event answers "where did this come from?" without copying content:

```jsonc
// Live MCP
{ "kind": "mcp", "client": "claude-code", "session": "<mcp session id if available>" }

// Import — points into the user's own export file
{ "kind": "import", "batch": "<uuid>", "file": "conversations.json",
  "conversation_uuid": "...", "message_uuid": "..." }

// Git
{ "kind": "git", "repo": "github.com/sidpan2011/persnally", "ref": "commit|file" }

// Derived (synthesis over other events)
{ "kind": "derived", "from": ["<event id>", "<event id>"] }
```

`kind: derived` is what makes "why does it think this?" a graph walk instead of a guess.

## Deletion semantics

- **Forget a topic:** hard-delete all events whose payload references it (+ derived events
  whose `from` chain includes them), then rebuild views.
- **Forget a source:** delete by `source` or import `batch` (one bad import is fully reversible).
- **Forget everything:** drop the database. No cloud copy exists unless Phase 4 sync is opted into.

Deletion never leaves tombstones with content; the count of deleted events may be logged
to `system.import`-style audit events, content never.

## Versioning

`schema_ver` is per-event. Readers must handle all historical versions or trigger
`persnally rebuild` after a migration. Payload shape changes = new version, never
in-place reinterpretation. The type set is closed per version: an event with an
unknown `type` for its claimed version fails ingestion loudly.

## What v1 deliberately leaves out

- **Raw message text** — even locally, until there's a concrete feature that needs it *and*
  a UI that makes the storage visible. Re-derive from the user's own exports instead.
- **Embeddings** — derived data; belongs in a view table when search needs them.
- **Multi-device identity** — Phase 4 concern; UUIDv7 ids merge cleanly when it arrives.
- **An `entities` table** — entity normalization stays inside extractors until we see
  real-world collision rates from imports.
