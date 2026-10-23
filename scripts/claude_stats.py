"""Print the conversation count and date range of a Claude (claude.ai) export.

The input file is opened read-only and never modified.

Usage:
    python scripts/claude_stats.py [path/to/conversations.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path("raw/claude/conversations.json")


def parse_iso(value: object) -> datetime | None:
    """Parse an ISO 8601 string. Naive values are assumed to be UTC."""
    if not isinstance(value, str) or not value:
        return None
    # Python < 3.11 fromisoformat() rejects a trailing "Z".
    if value.endswith(("Z", "z")):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_PATH, help=f"default: {DEFAULT_PATH}")
    args = parser.parse_args(argv)

    if not args.path.is_file():
        print(f"File not found: {args.path}", file=sys.stderr)
        return 1

    with args.path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("Unexpected layout: expected a top-level list", file=sys.stderr)
        return 1

    conversations = [c for c in data if isinstance(c, dict)]
    dates = [dt for c in conversations if (dt := parse_iso(c.get("created_at")))]
    missing = len(conversations) - len(dates)

    print(f"Conversations: {len(conversations)}")
    if dates:
        oldest, newest = min(dates), max(dates)
        print(f"Oldest:        {oldest.isoformat()}  (local: {oldest.astimezone():%Y-%m-%d %H:%M})")
        print(f"Newest:        {newest.isoformat()}  (local: {newest.astimezone():%Y-%m-%d %H:%M})")
    else:
        print("No valid created_at timestamps found")
    if missing:
        print(f"Missing/invalid created_at: {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
