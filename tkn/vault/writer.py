"""Write notes into the vault without duplicating or overwriting existing ones."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tkn.config import Config
from tkn.models import Conversation
from tkn.vault.naming import note_path
from tkn.vault.render import render_note

log = logging.getLogger(__name__)

WriteResult = Literal["created", "exists", "empty"]

# Frontmatter is near the top; avoid reading whole notes when indexing.
_FRONTMATTER_READ_CHARS = 8192


def read_note_key(path: Path) -> tuple[str, str] | None:
    """Return (source, id) from a note's frontmatter, or None if absent."""
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            head = f.read(_FRONTMATTER_READ_CHARS)
    except OSError:
        return None
    lines = head.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, raw = line.partition(":")
        if sep and key.strip() in ("source", "id"):
            values[key.strip()] = _parse_scalar(raw.strip())
    if "source" in values and "id" in values:
        return values["source"], values["id"]
    return None


def _parse_scalar(raw: str) -> str:
    if raw.startswith('"'):
        try:
            return str(json.loads(raw))
        except ValueError:
            pass
    return raw.strip("'\"")


@dataclass
class VaultWriter:
    config: Config
    dry_run: bool = False

    def __post_init__(self) -> None:
        self.index: dict[tuple[str, str], Path] = {}
        self._assigned: set[Path] = set()
        root = self.config.import_root
        if root.is_dir():
            for md in root.rglob("*.md"):
                key = read_note_key(md)
                if key:
                    self.index.setdefault(key, md)

    def write(self, conv: Conversation) -> tuple[WriteResult, Path | None]:
        key = (conv.source, conv.id)
        if key in self.index:
            return "exists", self.index[key]
        if not conv.has_content:
            return "empty", None

        path = self._free_path(conv)
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_text(render_note(conv, self.config.timezone), encoding="utf-8", newline="\n")
            os.replace(tmp, path)
        self.index[key] = path
        self._assigned.add(path)
        return "created", path

    def _free_path(self, conv: Conversation) -> Path:
        """Pick a file name that is not taken (on disk or earlier in this run)."""
        for suffix in ("", f" ({conv.id[:8]})", f" ({conv.id})"):
            path = note_path(self.config, conv, suffix)
            # Dry runs write nothing, so also check paths assigned earlier in this run.
            if not path.exists() and path not in self._assigned:
                return path
        raise FileExistsError(f"No free file name for {conv.source} {conv.id}")
