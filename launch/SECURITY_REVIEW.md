# Pre-launch security review — persnally (the published npm package)

**Date:** 2026-06-15 · **Scope:** the entire published surface (`persnallyd/`, everything a `npm i -g persnally` user runs), not a diff. · **Reviewer:** line-by-line read of every source file + dependency audit.

## Verdict

**No critical or high-severity findings.** The architecture's trust claims hold up under a full read. Three medium/low fixes applied (PR #28, v2.0.2); one trust-perception decision left to the founder.

This doc doubles as the honest answer to the inevitable "did anyone actually look at the security of this?" launch question.

## Threat model

The daemon runs on the user's machine and holds, over time, a structured model of who they are. The realistic adversaries:

1. **A malicious webpage** the user visits while the daemon is running (CSRF / DNS rebinding against `127.0.0.1:4983`).
2. **Malicious content inside the user's own AI history** trying to become executable when rendered (stored XSS via extracted topic/profile text in the dashboard).
3. **A co-tenant on a shared machine** trying to read the API key or inject events.
4. **The product itself** quietly exfiltrating data (the trust claim: local-first, nothing leaves except disclosed LLM calls).

## What was verified clean

| Surface | Finding |
|---|---|
| **Cross-origin / CSRF / DNS rebinding** | Hardened in PR #24, verified complete across *every* endpoint (Host allowlist + Origin check + JSON-only writes). The cost-bearing `POST /synthesize` is protected by the Origin check; `DELETE` is double-protected (preflight + Origin). DNS rebinding is stopped by the Host check. Verified live on the running daemon: foreign Origin → 403, `text/plain` → 415. |
| **Stored XSS (dashboard)** | `dashboard.html` has an `esc()` helper escaping `& < > " '`, applied to every user-derived value (titles, bodies, headline, topic names, evidence summaries, and all `data-*` attributes). The only unescaped interpolations are validated integers and ISO datetimes that cannot carry markup. No path to script execution in the localhost origin. |
| **SQL injection** | All queries in `store.ts` use prepared statements with bound parameters. The one string-interpolated column (`stats()` `group()`) is only ever called with hardcoded `"type"`/`"source"`. |
| **Command injection** | Every `child_process` call (`git`, `unzip`, `launchctl`, `open`) uses `execFileSync`/`spawn` with **array args, no shell** — attacker-controlled filenames or git config cannot break out. No `shell: true`, no `eval`. |
| **Data egress / privacy claim** | The only network calls are: the Anthropic API (BYOK, during import/synthesis — disclosed), Ollama (localhost), the daemon health check (localhost), and the MCP↔daemon loopback. No analytics, no phone-home. `telemetry.jsonl` is written to disk but **never transmitted** (see decision below). The local-first claim holds in code. |
| **Daemon network exposure** | Binds `127.0.0.1` only — not reachable off-host. |
| **Dependencies** | `npm audit` (runtime + dev): **0 vulnerabilities.** Four runtime deps only (`@anthropic-ai/sdk`, `@modelcontextprotocol/sdk`, `better-sqlite3`, `zod`). |
| **Published tarball** | 50 files, `build/src` + LICENSE + README only. No `.env`, no secrets, no `telemetry.jsonl`. `.env` was never committed to git history (verified). |
| **Hard delete** | `forgetTopic`/`forgetBatch`/`forgetAll` delete events *and* derived descendants, then rebuild views — the "truly deletable" claim is real, no tombstones. |

## Findings & fixes (PR #28, v2.0.2)

1. **API-key file TOCTOU — medium.** `saveConfig` did `writeFileSync` then `chmod 0600`, leaving a brief world-readable window on first create (matters on multi-user machines; the file holds the Anthropic key). **Fixed:** create with `{ mode: 0o600 }` *and* keep the chmod. New test asserts a freshly created key file is `0600`.
2. **Malformed-plist on exotic usernames — low (robustness).** `installAutostart` interpolated `process.execPath`/`cliPath`/`LOG_FILE` into plist XML unescaped; a home dir containing `& < > " '` produced invalid XML and silently broke autostart. Not attacker-controlled (own paths), but a real "doesn't work for some users" launch bug. **Fixed:** XML-escape all interpolated values.
3. **One bad client config aborts onboarding — low (robustness).** A malformed existing `claude_desktop_config.json` (people hand-edit these) made `persnally setup` crash mid-run. **Fixed:** `connectAll` tolerates per-client failure; `connectClient` refuses to overwrite a config it can't parse (which would wipe the user's other MCP servers) and surfaces a clear error.

## Open decision (founder's call — not changed)

**`~/.persnally/telemetry.jsonl`.** Genuinely local-only — verified no egress, logs counts/timestamps/tool-names only, never conversation content. But the *name* reads as phone-home, and a source-reading HN audience will grep for exactly this. Three options before launch:
- **Document it** prominently (README + dashboard footer: "local usage counts, never transmitted").
- **Rename** it (e.g. `usage-local.jsonl`) — but `experiments/capture_rate.py` depends on the exact filename, so update that too.
- **Gate it** behind an opt-in env var.

Recommendation: document + rename for the public build, keep the experiment script pointed at the new name. Left untouched here because it touches the Phase 0 experiment and is a brand call, not a bug.

## Known, accepted limitations (document, don't fix pre-launch)

- **Self-reported MCP client identity** — scoping is enforceable only against honest clients until per-client tokens (planned with the Phase 4 agent relay). Acceptable while the trust boundary is "your own machine."
- **No encryption at rest** — acceptable for local single-user; required before any Phase 4 sync.
- **macOS-only autostart** — `launchd`; a Linux systemd unit is a pre-launch nice-to-have if the launch is expected to draw Linux users.
