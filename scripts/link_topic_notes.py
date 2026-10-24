"""Add links to classified notes in the "## Notes" section of each topic note.

Input is the "Suggested topics" column of docs/CLASSIFICATION_REVIEW.md, so manual corrections
made in that file are respected. Topic notes live in <vault_path>/<topics folder>.

Only new link lines are appended inside the "## Notes" section, and links that are already present
are skipped. Notes in <root_folder> are only read, never modified.

Display titles can be overridden per (source, id) in a table in 02_Knowledge/Title-Overrides.md.
An existing link's text is updated to the override only while it still has the default text
(the file name), so link texts edited by hand are kept.

Usage:
    python scripts/link_topic_notes.py [--review FILE] [--folder 02_Knowledge/Topics]
        [--overrides FILE] [--config tkn.toml] [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from tkn.config import ConfigError, load_config
from tkn.vault.writer import read_note_key

DEFAULT_REVIEW = Path("docs/CLASSIFICATION_REVIEW.md")
DEFAULT_FOLDER = "02_Knowledge/Topics"
DEFAULT_OVERRIDES = "02_Knowledge/Title-Overrides.md"
DEFAULT_CONFIG = Path("tkn.toml")

NOTES_HEADING = "## Notes"

# | source | id | title | original title |
_OVERRIDE_ROW = re.compile(r"^\|\s*([a-z-]+)\s*\|\s*([^|\s]+)\s*\|\s*([^|]+?)\s*\|.*\|\s*$")
_FORBIDDEN_IN_ALIAS = ("|", "[[", "]]")


def read_overrides(path: Path) -> dict[tuple[str, str], str]:
    """Return (source, id) -> display title. A missing file means no overrides."""
    if not path.is_file():
        return {}
    overrides = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            match = _OVERRIDE_ROW.match(line.strip())
            if not match or match.group(1) == "source" or set(match.group(1)) <= {"-"}:
                continue
            title = match.group(3)
            if any(bad in title for bad in _FORBIDDEN_IN_ALIAS):
                print(f"skip override with '|', '[[' or ']]' in the title: {title}", file=sys.stderr)
                continue
            overrides[(match.group(1), match.group(2))] = title
    return overrides


def read_review(review: Path) -> list[tuple[str, list[str]]]:
    """Return (note path relative to root_folder, suggested topics) for each review row."""
    rows = []
    with review.open(encoding="utf-8") as f:
        for line in f:
            if not line.startswith("| ") or line.startswith(("| Note ", "| Topic ")):
                continue
            # Split on unescaped pipes; the note path may contain an escaped "\|".
            cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
            if len(cells) != 5 or not cells[0].endswith(".md"):
                continue
            rows.append((cells[0], [t.strip() for t in cells[2].split(",") if t.strip()]))
    return rows


def link_line(root_folder: str, rel: str, alias: str | None = None) -> tuple[str, str]:
    """Return (link target, bullet line) for a note path relative to root_folder."""
    target = f"{root_folder}/{rel[:-3]}"
    return target, f"- [[{target}|{alias or Path(rel).stem}]]"


def update_alias(text: str, target: str, default: str, alias: str) -> tuple[str, str]:
    """Change an existing link's text from the default to alias.

    Returns (new text, status) where status is "updated", "current" (already alias),
    or "edited" (text was changed by hand, so it is left alone).
    """
    pattern = re.compile(re.escape(f"[[{target}|") + r"([^\]]*)\]\]")
    match = pattern.search(text)
    if match is None or match.group(1) == alias:
        return text, "current"
    if match.group(1) != default:
        return text, "edited"
    return text[: match.start(1)] + alias + text[match.end(1) :], "updated"


def add_links(text: str, lines: list[str]) -> str | None:
    """Append lines at the end of the Notes section. None if the section is missing."""
    body = text.splitlines()
    try:
        start = next(i for i, line in enumerate(body) if line.strip() == NOTES_HEADING)
    except StopIteration:
        return None
    end = next((i for i in range(start + 1, len(body)) if body[i].startswith("## ")), len(body))
    # Insert after the last non-blank line of the section (or right after the heading).
    insert_at = end
    while insert_at > start + 1 and not body[insert_at - 1].strip():
        insert_at -= 1
    if insert_at == start + 1:
        lines = ["", *lines]
    # Keep one blank line before a following heading; existing blank lines are reused.
    trailer = [""] if insert_at < len(body) and body[insert_at].strip() else []
    new_body = body[:insert_at] + lines + trailer + body[insert_at:]
    return "\n".join(new_body).rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW, help=f"default: {DEFAULT_REVIEW}")
    parser.add_argument("--folder", default=DEFAULT_FOLDER, help=f"topic notes folder (default: {DEFAULT_FOLDER})")
    parser.add_argument("--overrides", type=Path, help=f"title overrides (default: <vault>/{DEFAULT_OVERRIDES})")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help=f"default: {DEFAULT_CONFIG}")
    parser.add_argument("--dry-run", action="store_true", help="show what would be linked without writing")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    if not args.review.is_file():
        print(f"Review file not found: {args.review}", file=sys.stderr)
        return 1

    topics_dir = config.vault_path / args.folder
    overrides_path = args.overrides or config.vault_path / DEFAULT_OVERRIDES
    overrides = read_overrides(overrides_path)
    by_topic: dict[str, list[str]] = defaultdict(list)
    aliases: dict[str, str] = {}
    missing_notes = 0
    for rel, topics in read_review(args.review):
        note = config.import_root / rel
        if not note.is_file():
            print(f"skip (note not found): {rel}", file=sys.stderr)
            missing_notes += 1
            continue
        key = read_note_key(note)
        if key and key in overrides:
            aliases[rel] = overrides[key]
        for topic in topics:
            by_topic[topic].append(rel)

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}title overrides: {len(overrides)} from {overrides_path}, {len(aliases)} used")
    total_added = total_present = total_renamed = 0
    for topic in sorted(by_topic):
        topic_note = topics_dir / f"{topic}.md"
        if not topic_note.is_file():
            print(f"{prefix}skip (no topic note): {topic} ({len(by_topic[topic])} links)")
            continue
        original = text = topic_note.read_text(encoding="utf-8")
        new_lines, present, renamed = [], 0, []
        for rel in sorted(by_topic[topic]):
            alias = aliases.get(rel)
            target, line = link_line(config.root_folder, rel, alias)
            if f"[[{target}|" in text or f"[[{target}]]" in text:
                present += 1
                if alias:
                    text, status = update_alias(text, target, Path(rel).stem, alias)
                    if status == "updated":
                        renamed.append(f"{Path(rel).stem} -> {alias}")
                    elif status == "edited":
                        print(f"{prefix}{topic}: keep hand-edited link text for {Path(rel).stem}")
            else:
                new_lines.append(line)
        total_present += present
        if new_lines:
            text = add_links(text, new_lines)
            if text is None:
                print(f"{prefix}skip (no '{NOTES_HEADING}' section): {topic}")
                continue
        if text == original:
            print(f"{prefix}{topic}: nothing to change ({present} already linked)")
            continue
        print(f"{prefix}{topic}: add {len(new_lines)} links, rename {len(renamed)} ({present} already linked)")
        if args.dry_run:
            for line in new_lines[:3]:
                print(f"    + {line}")
            if len(new_lines) > 3:
                print(f"    ... {len(new_lines) - 3} more")
            for change in renamed:
                print(f"    ~ {change}")
        else:
            tmp = topic_note.with_name(topic_note.name + ".tmp")
            tmp.write_text(text, encoding="utf-8", newline="\n")
            os.replace(tmp, topic_note)
        total_added += len(new_lines)
        total_renamed += len(renamed)

    verb = "Would add" if args.dry_run else "Added"
    print(
        f"{prefix}{verb} {total_added} links, renamed {total_renamed} link texts, "
        f"already linked {total_present}, notes not found {missing_notes}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
