# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Persnally, please report it responsibly.

**Email:** sidh.pan98@gmail.com

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge your report within 48 hours and aim to release a fix within 7 days for critical issues.

**Do not** open a public GitHub issue for security vulnerabilities.

## What We Consider Security Issues

- Data leakage (raw conversations being stored or transmitted)
- Authentication bypasses on the API
- API key exposure
- Interest graph data being sent without user consent
- Email injection or spoofing via the digest system

## Architecture Security Notes

Persnally is designed with privacy as a core architectural constraint:

- **Local-first**: The MCP server runs on your machine. Your interest graph is a JSON file at `~/.persnally/`
- **No raw messages**: Only structured signals (topic, weight, category, sentiment) are stored. Conversations never leave your machine
- **Opt-in cloud sync**: Data is only sent to the API when you explicitly trigger a digest or configure cloud sync
- **API authentication**: All API endpoints require either a Supabase JWT or a hashed API key
- **No tracking**: The web frontend has no analytics, tracking pixels, or third-party scripts

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |
