"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from collections.abc import Callable, Iterator
from datetime import date
from pathlib import Path

from tkn.config import Config, ConfigError, load_config
from tkn.importers import chatgpt, claude, claude_code, codex
from tkn.models import SOURCES, Conversation
from tkn.vault.writer import VaultWriter

log = logging.getLogger("tkn")


class _WarningCounter(logging.Handler):
    """Counts warnings logged by importers (skipped malformed records)."""

    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.count = 0

    def emit(self, record: logging.LogRecord) -> None:
        self.count += 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tkn", description="Import AI conversations into an Obsidian vault.")
    sub = parser.add_subparsers(dest="command", required=True)

    imp = sub.add_parser("import", help="Import conversations from one tool")
    imp.add_argument("source", choices=SOURCES)
    imp.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Export ZIP, export folder (chatgpt) or conversations.json (chatgpt, claude); "
        "overrides the configured session directory (claude-code, codex)",
    )
    imp.add_argument("--config", type=Path, default=Path("tkn.toml"), help="Config file (default: ./tkn.toml)")
    imp.add_argument("--dry-run", action="store_true", help="Show what would be written without writing")
    imp.add_argument("--since", type=date.fromisoformat, help="Only import conversations created on/after YYYY-MM-DD")
    imp.add_argument("-v", "--verbose", action="store_true", help="List every created note")
    return parser


def _conversations(source: str, path: Path | None, config: Config) -> Iterator[Conversation]:
    importers: dict[str, tuple[Callable[[Path], Iterator[Conversation]], Path | None]] = {
        "chatgpt": (chatgpt.iter_conversations, None),
        "claude": (claude.iter_conversations, None),
        "claude-code": (claude_code.iter_conversations, config.claude_code_dir),
        "codex": (codex.iter_conversations, config.codex_dir),
    }
    func, default = importers[source]
    target = path or default
    if target is None:
        raise ConfigError(f"'{source}' needs a path to the export ZIP or conversations.json")
    if not target.exists():
        raise ConfigError(f"Path not found: {target}")
    return func(target)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    counter = _WarningCounter()
    logging.getLogger("tkn.importers").addHandler(counter)

    try:
        config = load_config(args.config)
        conversations = _conversations(args.source, args.path, config)
        writer = VaultWriter(config, dry_run=args.dry_run)
        stats: Counter[str] = Counter()
        for conv in conversations:
            if args.since and conv.created.astimezone(config.timezone).date() < args.since:
                stats["filtered"] += 1
                continue
            try:
                result, note = writer.write(conv)
            except OSError as exc:
                log.error("Failed to write %s %s: %s", conv.source, conv.id, exc)
                stats["errors"] += 1
                continue
            stats[result] += 1
            if result == "created" and args.verbose and note:
                print(f"  + {note.relative_to(config.vault_path)}")
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        log.error("%s", exc)
        return 2
    finally:
        logging.getLogger("tkn.importers").removeHandler(counter)

    prefix = "[dry run] " if args.dry_run else ""
    print(
        f"{prefix}{args.source}: created {stats['created']}, skipped (exists) {stats['exists']}, "
        f"skipped (empty) {stats['empty']}, filtered {stats['filtered']}, "
        f"malformed {counter.count}, errors {stats['errors']}"
    )
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
