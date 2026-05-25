# Persnally

An MCP server that learns from your conversations with Claude and sends you personalized digests.

**Your AI already knows what you care about.** Persnally gives it a way to remember.

## How It Works

1. You install Persnally as an MCP server in Claude Desktop
2. As you chat, Claude calls `persnally_track` to note what you're interested in
3. Persnally builds a local interest graph (no raw messages stored)
4. Daily/weekly, it curates a personalized digest and emails it via Resend

## Install

```bash
npm install -g persnally
```

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "persnally": {
      "command": "persnally",
      "args": []
    }
  }
}
```

Restart Claude Desktop, then tell Claude:

> "Set my Persnally email to me@example.com"

That's it. Start chatting — Persnally learns automatically.

## MCP Tools

| Tool | Description |
|------|-------------|
| `persnally_track` | Extracts topics, intent, and sentiment from conversations. Called automatically by Claude. |
| `persnally_interests` | Shows your current interest profile grouped by category. |
| `persnally_digest` | Generates and sends your personalized digest email. |
| `persnally_config` | Set email, frequency (daily/weekly), API preferences. |
| `persnally_forget` | Remove a topic or clear all data. Full privacy control. |

## Interest Graph

Persnally doesn't just store a flat list of interests. It builds a weighted graph with:

- **Exponential decay** — 7-day half-life keeps the graph fresh
- **Sentiment awareness** — "I hate CSS" deprioritizes CSS content
- **Depth scoring** — A brief mention scores differently than a deep dive
- **Intent tracking** — Learning, building, researching, debugging shape content selection
- **Topic normalization** — "React.js", "React JS", "ReactJS" all merge to one node
- **Balanced allocation** — Digest covers multiple categories proportionally

## Privacy

Only structured signals are stored:

```
+ Topic name (e.g., "Rust async programming")
+ Weight (0.1 to 1.0)
+ Category, intent, sentiment
+ Entity names (e.g., "tokio", "axum")
```

**Never stored:** your messages, Claude's responses, code snippets, personal information.

Your interest graph is a JSON file at `~/.persnally/interest-graph.json`. Read it, edit it, or delete it anytime.

## Configuration

```
# Via Claude
"Set my Persnally email to me@example.com"
"Change my digest frequency to weekly"
"Show my Persnally interests"
"Remove Rust from my Persnally profile"
"Clear all my Persnally data"

# Environment variables (optional)
PERSNALLY_API_URL=https://api.persnally.com  # default
PERSNALLY_API_KEY=your-key                   # only needed for cloud digest delivery
```

### Cloud digest delivery (optional)

Persnally works fully locally out of the box — the MCP tracks your interests, `persnally_interests` shows your profile, and `persnally_digest` (with `preview: true`) shows exactly what your next digest would contain. The cloud step is only needed to actually have the digest curated by the AI pipeline and delivered to your inbox via Resend.

To enable it:

1. Sign in at [persnally.com](https://persnally.com) and generate an API key from your dashboard.
2. Set it as either an env var (`PERSNALLY_API_KEY=...`) or via Claude:

   > "Set my Persnally API key to `<your-key>`"

Without a key, every tool still works locally — your interest graph builds, digests can still be previewed, and the privacy controls (`persnally_forget`, etc.) are unaffected. Only the outbound email step is skipped.

## Development

```bash
git clone https://github.com/sidpan2011/persnally.git
cd persnally/mcp_server/persnally
npm install
npm run build
npm test
```

## License

MIT — [github.com/sidpan2011/persnally](https://github.com/sidpan2011/persnally)
