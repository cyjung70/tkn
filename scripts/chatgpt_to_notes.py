"""Convert conversations in a ChatGPT export to Markdown notes.

The input is the extracted export folder (conversations.json or conversations-NNN.json shards),
the export ZIP, or a single conversations JSON file. Everything else works like
claude_to_notes.py: by default only the most recently created conversation is converted;
--all converts every one. Inputs are never modified and existing notes are never overwritten.

Usage:
    python scripts/chatgpt_to_notes.py [path/to/export] [--out DIR] [--all]
"""

from __future__ import annotations

import sys
from pathlib import Path

from claude_to_notes import convert

from tkn.importers import chatgpt

DEFAULT_PATH = Path("raw/chatgpt")
DEFAULT_OUT = Path("output/chatgpt")


def main(argv: list[str] | None = None) -> int:
    return convert(argv, __doc__.splitlines()[0], chatgpt.iter_conversations, DEFAULT_PATH, DEFAULT_OUT, "ChatGPT")


if __name__ == "__main__":
    sys.exit(main())
