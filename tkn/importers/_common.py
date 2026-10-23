"""Helpers shared by importers."""

from __future__ import annotations

import io
import json
import logging
import zipfile
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tkn.models import Message

log = logging.getLogger(__name__)

TITLE_MAX_CHARS = 60
TOOL_ARG_MAX_CHARS = 80

# Tool input keys that best describe a call, in order of preference.
_TOOL_ARG_KEYS = ("command", "cmd", "file_path", "path", "pattern", "url", "query", "description", "prompt")


def parse_iso(value: Any) -> datetime | None:
    """Parse an ISO 8601 string. Naive values are assumed to be UTC."""
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def from_epoch(value: Any) -> datetime | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def title_from_messages(messages: list[Message]) -> str:
    for m in messages:
        if m.role == "user" and m.text.strip():
            first_line = m.text.strip().splitlines()[0].strip()
            if len(first_line) > TITLE_MAX_CHARS:
                first_line = first_line[:TITLE_MAX_CHARS].rstrip() + "…"
            return first_line
    return "Untitled"


def summarize_tool_call(name: str, args: Any) -> str:
    """Build a one-line description of a tool call, e.g. 'Bash: git status'."""
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            pass
    detail = ""
    if isinstance(args, dict):
        for key in _TOOL_ARG_KEYS:
            value = args.get(key)
            if value:
                detail = " ".join(value) if isinstance(value, list) else str(value)
                break
    elif isinstance(args, str):
        detail = args
    detail = " ".join(detail.split())
    if len(detail) > TOOL_ARG_MAX_CHARS:
        detail = detail[:TOOL_ARG_MAX_CHARS].rstrip() + "…"
    name = name or "tool"
    return f"{name}: {detail}" if detail else name


def load_export_json(path: Path, member_name: str = "conversations.json") -> Any:
    """Load a JSON file from an export ZIP or directly from disk."""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            candidates = [n for n in zf.namelist() if n.rsplit("/", 1)[-1] == member_name]
            if not candidates:
                raise FileNotFoundError(f"{member_name} not found in {path.name}")
            # Prefer the shallowest match.
            candidates.sort(key=lambda n: n.count("/"))
            with zf.open(candidates[0]) as raw:
                return json.load(io.TextIOWrapper(raw, encoding="utf-8"))
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yield JSON objects from a JSONL file, skipping malformed lines."""
    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                log.debug("%s:%d: malformed JSON line skipped", path.name, line_no)
                continue
            if isinstance(obj, dict):
                yield obj
