"""Build note paths: <vault>/<root>/<Tool>/<YYYY-MM>/<YYYY-MM-DD>_<title>.md"""

from __future__ import annotations

import re
from pathlib import Path

from tkn.config import Config
from tkn.models import Conversation

TITLE_MAX_CHARS = 80

# Characters forbidden in Windows file names or meaningful to Obsidian links, plus control chars.
_FORBIDDEN = re.compile(r'[\\/:*?"<>|#^\[\]\x00-\x1f\x7f]')
_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def sanitize_title(title: str, max_chars: int = TITLE_MAX_CHARS) -> str:
    cleaned = _FORBIDDEN.sub(" ", title)
    cleaned = " ".join(cleaned.split())
    cleaned = cleaned[:max_chars]
    # Windows silently drops trailing dots and spaces.
    cleaned = cleaned.rstrip(". ")
    if not cleaned:
        return "Untitled"
    if cleaned.split(".")[0].upper() in _WINDOWS_RESERVED:
        cleaned = f"_{cleaned}"
    return cleaned


def note_path(config: Config, conv: Conversation, suffix: str = "") -> Path:
    local = conv.created.astimezone(config.timezone)
    folder = config.import_root / config.folders[conv.source] / local.strftime("%Y-%m")
    return folder / f"{local:%Y-%m-%d}_{sanitize_title(conv.title)}{suffix}.md"
