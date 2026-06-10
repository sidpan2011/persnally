#!/usr/bin/env python3
"""
Phase 0 capture-rate analysis.

Reads ~/.persnally/telemetry.jsonl (written by the instrumented MCP server)
and answers: what fraction of organic AI conversations produce persnally_track
signals? This decides whether passive accrual works or import must carry v2.

Usage:
    python experiments/capture_rate.py [--since YYYY-MM-DD] [--export path/to/claude_export_dir]

Denominators:
- Claude Code: counted automatically from local transcripts (~/.claude/projects/*/*.jsonl)
- claude.ai/Desktop: pass a fresh data export via --export to count conversations in window
"""

import argparse
import glob
import json
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

TELEMETRY = Path.home() / ".persnally" / "telemetry.jsonl"
CLAUDE_CODE_TRANSCRIPTS = Path.home() / ".claude" / "projects"
EXCLUDED_CLIENTS = {"smoke-test"}


def load_events(since: datetime) -> list[dict]:
    if not TELEMETRY.exists():
        raise SystemExit(f"No telemetry at {TELEMETRY} — has the instrumented server run?")
    events = []
    for line in TELEMETRY.read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("client") in EXCLUDED_CLIENTS:
            continue
        ts = datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
        if ts >= since:
            e["_ts"] = ts
            events.append(e)
    return events


def count_claude_code_sessions(since: datetime) -> int:
    """Each transcript .jsonl under ~/.claude/projects is one session."""
    n = 0
    for f in glob.glob(str(CLAUDE_CODE_TRANSCRIPTS / "*" / "*.jsonl")):
        mtime = datetime.fromtimestamp(os.path.getmtime(f), tz=UTC)
        if mtime >= since:
            n += 1
    return n


def count_export_conversations(export_dir: Path, since: datetime) -> int:
    conv = export_dir / "conversations.json"
    if not conv.exists():
        raise SystemExit(f"No conversations.json in {export_dir}")
    n = 0
    for c in json.loads(conv.read_text()):
        ts = (c.get("updated_at") or c.get("created_at") or "").replace("Z", "+00:00")
        if ts and datetime.fromisoformat(ts) >= since:
            n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="window start (YYYY-MM-DD); default = first event")
    ap.add_argument("--export", help="Claude export dir for the claude.ai/Desktop denominator")
    args = ap.parse_args()

    since = datetime.fromisoformat(args.since).replace(tzinfo=UTC) if args.since else datetime.min.replace(tzinfo=UTC)
    events = load_events(since)
    if not events:
        raise SystemExit("No organic telemetry events in window yet — keep using your AI tools.")

    start = min(e["_ts"] for e in events)
    end = max(e["_ts"] for e in events)
    days = max((end - start).days, 1)

    track_calls = [e for e in events if e.get("tool") == "persnally_track"]
    sessions = [e for e in events if e["event"] == "session_start"]
    by_client_tracks = Counter(e["client"] for e in track_calls)
    by_client_sessions = Counter(e["client"] for e in sessions)
    topics = sum(e.get("topics", 0) for e in track_calls)

    # Track calls more than an hour apart count as separate "tracked conversations"
    tracked_convos: dict[str, int] = defaultdict(int)
    last_seen: dict[str, datetime] = {}
    for e in sorted(track_calls, key=lambda x: x["_ts"]):
        c = e["client"]
        if c not in last_seen or (e["_ts"] - last_seen[c]).total_seconds() > 3600:
            tracked_convos[c] += 1
        last_seen[c] = e["_ts"]

    print(f"Window: {start.date()} → {end.date()} ({days}d)")
    print(f"Track calls: {len(track_calls)} ({topics} topics) | MCP sessions: {len(sessions)}")
    for client in sorted(set(by_client_tracks) | set(by_client_sessions)):
        print(
            f"  {client}: {by_client_tracks[client]} tracks "
            f"≈ {tracked_convos[client]} tracked convos, {by_client_sessions[client]} sessions"
        )

    cc_sessions = count_claude_code_sessions(start if not args.since else since)
    cc_tracked = sum(n for c, n in tracked_convos.items() if "code" in c.lower() or "claude" in c.lower())
    if cc_sessions:
        print(
            f"\nClaude Code: {cc_tracked}/{cc_sessions} sessions produced signals "
            f"→ capture rate {cc_tracked / cc_sessions:.0%}"
        )

    if args.export:
        n = count_export_conversations(Path(args.export), start if not args.since else since)
        desktop_tracked = sum(n2 for c, n2 in tracked_convos.items() if "code" not in c.lower())
        if n:
            print(
                f"claude.ai/Desktop: {desktop_tracked}/{n} conversations produced signals "
                f"→ capture rate {desktop_tracked / n:.0%}"
            )
    else:
        print(
            "\n(For the claude.ai/Desktop denominator, request a fresh export at the end "
            "of the window and rerun with --export.)"
        )


if __name__ == "__main__":
    main()
