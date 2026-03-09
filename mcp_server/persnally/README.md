# Persnally MCP Server

An AI-native personalized intelligence engine that learns from your conversations and curates daily digests tailored to your interests.

## How It Works

1. **Install** as an MCP server in Claude Desktop or any MCP-compatible client
2. **Chat naturally** — the AI calls `persnally_track` to note topics you're interested in
3. **Interest graph builds** locally with exponential decay, sentiment tracking, and depth scoring
4. **Trigger a digest** and receive a curated email via Resend with content matched to your interests

**Privacy by architecture**: Only structured signals are stored (topic, weight, category). Raw conversations never leave your machine.

## Quick Start

### Install

```bash
npm install -g persnally-mcp
```

### Configure Claude Desktop

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

### Configure Your Email

In any Claude conversation:
> "Set my Persnally email to alice@example.com"

Claude will call `persnally_config` automatically.

## Tools

| Tool | Description |
|------|-------------|
| `persnally_track` | Track topics from conversations (called automatically by the AI) |
| `persnally_interests` | View your current interest profile |
| `persnally_digest` | Generate and send a personalized digest email |
| `persnally_config` | Configure email, frequency, API key |
| `persnally_forget` | Remove topics or clear all data |

## Interest Engine

The interest engine uses several signals to build your profile:

- **Exponential decay** (half-life: 7 days) — recent interests matter more
- **Depth scoring** — a deep conversation about Rust outweighs 10 brief mentions
- **Sentiment tracking** — "I hate CSS" deprioritizes CSS, doesn't boost it
- **Balanced allocation** — if you're 60% tech + 30% business + 10% finance, your digest reflects that ratio
- **Intent classification** — learning, building, researching, deciding, discussing, debugging

## Data Storage

All data is stored locally at `~/.persnally/`:

- `interest-graph.json` — your interest profile
- `config.json` — email, frequency, preferences

No data is sent anywhere unless you explicitly trigger a digest with an API key configured.

## Development

```bash
git clone https://github.com/sidpan2011/persnally
cd mcp_server/persnally
npm install
npm run build
npm start
```

## License

MIT
