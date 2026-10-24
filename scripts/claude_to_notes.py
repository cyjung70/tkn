"""Convert conversations in a Claude export to Markdown notes.

By default only the most recently created conversation is converted; --all converts every one.
The input file is opened read-only and never modified. Existing notes are never overwritten:
conversations whose uuid already appears in a note's frontmatter are skipped.

Usage:
    python scripts/claude_to_notes.py [path/to/conversations.json] [--out DIR] [--all]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

from tkn.importers import claude
from tkn.models import Conversation
from tkn.vault.naming import sanitize_title

DEFAULT_PATH = Path("raw/claude/conversations.json")
DEFAULT_OUT = Path("output/claude")

_UUID_LINE = re.compile(r'^uuid:\s*"(.*)"\s*$')


def render(conv: Conversation, assistant: str = "Claude") -> str:
    # Values are JSON-encoded; a JSON string is a valid YAML scalar.
    fields = {
        "title": conv.title,
        "source": conv.source,
        "created": conv.created.astimezone().isoformat(timespec="seconds"),
        "uuid": conv.id,
    }
    lines = ["---", *(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in fields.items()), "---", ""]
    lines += [f"# {conv.title}", ""]

    current_role: str | None = None
    for message in conv.messages:
        if message.role == "tool":
            # Tool calls are shown inline under the current speaker, without a heading.
            lines += [f"> 🔧 `{message.text.replace('`', chr(39))}`", ""]
            continue
        if message.role != current_role:
            heading = assistant if message.role == "assistant" else "User"
            if message.timestamp:
                heading += f" · {message.timestamp.astimezone():%Y-%m-%d %H:%M}"
            lines += [f"## {heading}", ""]
            current_role = message.role
        lines += [message.text, ""]

    return "\n".join(lines).rstrip("\n") + "\n"


def existing_uuids(out: Path) -> set[str]:
    """Collect uuids from the frontmatter of notes already in the output folder."""
    found: set[str] = set()
    for note in out.glob("*.md"):
        with note.open(encoding="utf-8", errors="replace") as f:
            if f.readline().strip() != "---":
                continue
            for line in f:
                if line.strip() == "---":
                    break
                if match := _UUID_LINE.match(line.strip()):
                    found.add(json.loads(f'"{match.group(1)}"'))
    return found


def target_path(out: Path, conv: Conversation) -> Path:
    local = conv.created.astimezone()
    stem = f"{local:%Y-%m-%d}_{sanitize_title(conv.title)}"
    path = out / f"{stem}.md"
    if path.exists():
        path = out / f"{stem} ({conv.id[:8]}).md"
    return path


def convert(
    argv: list[str] | None,
    description: str,
    iter_conversations: Callable[[Path], Iterator[Conversation]],
    default_path: Path,
    default_out: Path,
    assistant: str,
) -> int:
    """Command-line entry shared by the per-tool note scripts."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("path", nargs="?", type=Path, default=default_path, help=f"default: {default_path}")
    parser.add_argument("--out", type=Path, default=default_out, help=f"output folder (default: {default_out})")
    parser.add_argument("--all", action="store_true", help="convert every conversation, not just the latest")
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"Not found: {args.path}", file=sys.stderr)
        return 1

    parsed = list(iter_conversations(args.path))
    conversations = [c for c in parsed if c.has_content]
    empty = len(parsed) - len(conversations)
    if not conversations:
        print("No conversations with content found", file=sys.stderr)
        return 1
    if not args.all:
        conversations = [max(conversations, key=lambda c: c.created)]

    args.out.mkdir(parents=True, exist_ok=True)
    done = existing_uuids(args.out)
    written = skipped = 0
    for conv in sorted(conversations, key=lambda c: c.created):
        if conv.id in done:
            skipped += 1
            continue
        target = target_path(args.out, conv)
        if target.exists():
            print(f"Name collision, skipped: {target}", file=sys.stderr)
            skipped += 1
            continue
        target.write_text(render(conv, assistant), encoding="utf-8")
        done.add(conv.id)
        written += 1
        if not args.all:
            print(f"Wrote {target} ({len(conv.messages)} messages, created {conv.created.astimezone():%Y-%m-%d %H:%M})")

    print(f"Written: {written}, already present: {skipped}, without content: {empty if args.all else 0}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return convert(argv, __doc__.splitlines()[0], claude.iter_conversations, DEFAULT_PATH, DEFAULT_OUT, "Claude")


if __name__ == "__main__":
    sys.exit(main())
