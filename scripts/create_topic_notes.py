"""Create one topic index note per approved topic in the Obsidian vault.

Topics are read from the table in docs/TOPICS_PROPOSAL.md, plus "Unclassified". Notes go to
<vault_path>/<folder> (vault_path from tkn.toml). Existing notes are skipped, never overwritten.

Usage:
    python scripts/create_topic_notes.py [--proposal FILE] [--folder 02_Knowledge/Topics] [--config tkn.toml] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from tkn.config import ConfigError, load_config

DEFAULT_PROPOSAL = Path("docs/TOPICS_PROPOSAL.md")
DEFAULT_FOLDER = "02_Knowledge/Topics"
DEFAULT_CONFIG = Path("tkn.toml")

# | # | `Topic-Name` | description | keywords | repos |
_ROW = re.compile(r"^\|\s*\d+\s*\|\s*`([A-Za-z0-9-]+)`\s*\|(.*)\|(.*)\|(.*)\|\s*$")


@dataclass(frozen=True)
class Topic:
    name: str
    description: str
    keywords: str


UNCLASSIFIED = Topic(
    name="Unclassified",
    description="Notes that do not fit any topic yet, kept here until they are classified.",
    keywords="",
)


def read_topics(proposal: Path) -> list[Topic]:
    topics = []
    with proposal.open(encoding="utf-8") as f:
        for line in f:
            if match := _ROW.match(line.strip()):
                name, description, keywords, _repos = (part.strip() for part in match.groups())
                topics.append(Topic(name, description, keywords))
    return topics


def render(topic: Topic) -> str:
    lines = [
        "---",
        f"type: {json.dumps('topic')}",
        f"topic: {json.dumps(topic.name, ensure_ascii=False)}",
        "---",
        "",
        f"# {topic.name}",
        "",
        topic.description,
        "",
    ]
    if topic.keywords:
        lines += [f"**Keywords:** {topic.keywords}", ""]
    lines += ["## Notes", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL, help=f"default: {DEFAULT_PROPOSAL}")
    parser.add_argument("--folder", default=DEFAULT_FOLDER, help=f"folder inside the vault (default: {DEFAULT_FOLDER})")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help=f"default: {DEFAULT_CONFIG}")
    parser.add_argument("--dry-run", action="store_true", help="show what would be created without writing")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    if not args.proposal.is_file():
        print(f"Proposal not found: {args.proposal}", file=sys.stderr)
        return 1

    topics = read_topics(args.proposal)
    if not topics:
        print(f"No topics found in {args.proposal}", file=sys.stderr)
        return 1
    topics.append(UNCLASSIFIED)

    dest = config.vault_path / args.folder
    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}{len(topics)} topics -> {dest}" + ("" if dest.is_dir() else " (folder will be created)"))
    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    created = skipped = 0
    for topic in topics:
        target = dest / f"{topic.name}.md"
        if target.exists():
            print(f"{prefix}skip (exists): {target.name}")
            skipped += 1
            continue
        if not args.dry_run:
            try:
                # Exclusive create, so a note appearing after the check is still never overwritten.
                with target.open("x", encoding="utf-8", newline="\n") as f:
                    f.write(render(topic))
            except FileExistsError:
                print(f"skip (exists): {target.name}")
                skipped += 1
                continue
        print(f"{prefix}create: {target.name}")
        created += 1

    verb = "Would create" if args.dry_run else "Created"
    print(f"{prefix}{verb}: {created}, skipped (already exists): {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
