#!/usr/bin/env python3
"""
Phase 0 "describe-me" experiment.

Parses a Claude data export and asks Claude to describe the person behind it.
Persnally bets on this output being *startling*, not just accurate.
If it's merely neat, the core idea does not hold.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python experiments/describe_me.py path/to/export_dir
    python experiments/describe_me.py path/to/conversations.json
    python experiments/describe_me.py --zip path/to/export.zip

A full export dir is richest: it adds conversation summaries, user-created
projects, and Claude's own accumulated memory — the highest-signal-per-byte
sources, per the Phase 0 finding.
"""

import argparse
import glob
import json
import sys
import zipfile
from pathlib import Path

MODEL = "claude-fable-5"
MAX_CHARS = 400_000

PROMPT = """You are analyzing a person's real conversations with an AI assistant. \
This is the only information you have about them. Build the sharpest possible \
picture of who they are, then write it as if you've known them for years.

Cover, only where the evidence supports it:
- What they're working on right now, and what they're building toward
- How they think and make decisions (cautious/bold, first-principles/pattern-matching, etc.)
- Their technical depth and the specific tools, languages, and domains they live in
- How they communicate (terse/expansive, blunt/diplomatic)
- What they care about, what frustrates them, what they're avoiding
- Non-obvious inferences — things they never said outright but that the pattern reveals

Be specific and concrete; cite the kind of evidence that led to each claim. \
Where you're guessing, say so. Do not flatter. The test of this output is whether \
the person reads it and thinks "how did it know that?"

--- CONVERSATIONS ---
{corpus}
--- END CONVERSATIONS ---

Now write the description."""


def _text_from_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    return ""


def extract_user_text(conversations: list) -> tuple[str, dict]:
    """Pull only the human's messages. We profile the person, not the assistant."""
    parts: list[str] = []
    stats = {"conversations": 0, "user_messages": 0}

    for convo in conversations:
        stats["conversations"] += 1
        title = convo.get("name") or convo.get("title") or ""
        if title:
            parts.append(f"\n## {title}")
        for msg in convo.get("chat_messages", convo.get("messages", [])):
            if (msg.get("sender") or msg.get("role")) not in ("human", "user"):
                continue
            text = msg.get("text") or _text_from_content(msg.get("content"))
            if text and text.strip():
                parts.append(text.strip())
                stats["user_messages"] += 1

    return "\n".join(parts), stats


def assemble_corpus(conversations: list, export_dir: Path | None) -> tuple[str, dict]:
    """User messages, plus the high-signal extras when a full export dir is given."""
    corpus, stats = extract_user_text(conversations)
    sections = [corpus]

    summaries = [
        f"- {c.get('name', '(untitled)')}: {c['summary'].strip()}"
        for c in conversations
        if (c.get("summary") or "").strip()
    ]
    if summaries:
        sections.append("\n--- CONVERSATION SUMMARIES ---\n" + "\n".join(summaries))

    if export_dir:
        projects = []
        for f in sorted(glob.glob(str(export_dir / "projects" / "*.json"))):
            p = json.load(open(f))
            if p.get("is_starter_project"):
                continue
            line = f"- {p.get('name', '')}: {p.get('description', '')}".strip()
            if (p.get("prompt_template") or "").strip():
                line += f"\n  prompt_template: {p['prompt_template'].strip()[:500]}"
            projects.append(line)
        if projects:
            sections.append("\n--- USER-CREATED PROJECTS ---\n" + "\n".join(projects))
            stats["projects"] = len(projects)

        mem_file = export_dir / "memories.json"
        if mem_file.exists():
            memories = json.loads(mem_file.read_text())
            memory_text = "\n".join(
                m.get("conversations_memory", "") for m in memories if isinstance(m, dict)
            )
            if memory_text.strip():
                sections.append(
                    "\n--- ASSISTANT'S ACCUMULATED MEMORY OF USER ---\n" + memory_text
                )

    return "\n\n".join(sections), stats


def load_conversations(path: Path | None, zip_path: Path | None) -> tuple[list, Path | None]:
    """Returns (conversations, export_dir). export_dir is set only for a full export folder."""
    if zip_path:
        with zipfile.ZipFile(zip_path) as zf:
            name = next((n for n in zf.namelist() if n.endswith("conversations.json")), None)
            if not name:
                sys.exit(f"No conversations.json inside {zip_path}")
            return json.loads(zf.read(name)), None
    if path and path.is_dir():
        conv = path / "conversations.json"
        if not conv.exists():
            sys.exit(f"No conversations.json in {path}")
        return json.loads(conv.read_text()), path
    if path:
        return json.loads(path.read_text()), None
    sys.exit("provide an export dir, conversations.json, or --zip export.zip")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="export dir or conversations.json")
    ap.add_argument("--zip", dest="zip_path", help="export .zip")
    args = ap.parse_args()

    conversations, export_dir = load_conversations(
        Path(args.path) if args.path else None,
        Path(args.zip_path) if args.zip_path else None,
    )
    corpus, stats = assemble_corpus(conversations, export_dir)
    if not corpus.strip():
        sys.exit("No user content found — is this a Claude export?")

    truncated = len(corpus) > MAX_CHARS
    corpus = corpus[-MAX_CHARS:]
    print(
        f"{stats['conversations']} convos, {stats['user_messages']} user msgs, "
        f"{stats.get('projects', 0)} projects, {len(corpus):,} chars"
        f"{' (truncated)' if truncated else ''}.\n",
        file=sys.stderr,
    )

    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("pip install anthropic")

    with Anthropic().messages.stream(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": PROMPT.format(corpus=corpus)}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
