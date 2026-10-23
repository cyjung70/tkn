"""Codex CLI session importer (~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl)."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from tkn.importers._common import iter_jsonl, parse_iso, summarize_tool_call, title_from_messages
from tkn.models import Conversation, Message

log = logging.getLogger(__name__)

SOURCE = "codex"

# Context that Codex injects as "user" messages; not typed by the user.
_INJECTED_PREFIXES = (
    "<environment_context>",
    "<user_instructions>",
    "<permissions instructions>",
    "# AGENTS.md instructions",
)
# Voice (realtime) sessions wrap the user's request in a delegation envelope.
_DELEGATION_INPUT = re.compile(r"<realtime_delegation>.*?<input>(.*?)</input>", re.DOTALL)

_TOOL_CALL_TYPES = {"function_call", "custom_tool_call", "local_shell_call"}


def iter_conversations(root: Path) -> Iterator[Conversation]:
    if not root.is_dir():
        raise FileNotFoundError(f"Codex sessions directory not found: {root}")
    for path in sorted(root.rglob("rollout-*.jsonl")):
        try:
            conv = parse_session(path)
        except Exception as exc:
            log.warning("Skipping Codex session %s: %s", path.name, exc)
            continue
        if conv is not None:
            yield conv


def parse_session(path: Path) -> Conversation | None:
    session_id: str | None = None
    project: str | None = None
    created: datetime | None = None
    timestamps: list[datetime] = []
    messages: list[Message] = []

    for entry in iter_jsonl(path):
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            continue
        timestamp = parse_iso(entry.get("timestamp"))
        if timestamp:
            timestamps.append(timestamp)

        etype = entry.get("type")
        if etype == "session_meta":
            session_id = session_id or payload.get("id") or payload.get("session_id")
            project = project or payload.get("cwd")
            created = created or parse_iso(payload.get("timestamp"))
        elif etype == "response_item":
            message = _parse_response_item(payload, timestamp)
            if message is not None:
                messages.append(message)

    created = created or (min(timestamps) if timestamps else None)
    if created is None:
        return None

    return Conversation(
        source=SOURCE,
        id=session_id or path.stem,
        title=title_from_messages(messages),
        created=created,
        updated=max(timestamps) if timestamps else None,
        messages=messages,
        project=project,
        source_path=path,
    )


def _parse_response_item(payload: dict[str, Any], timestamp: datetime | None) -> Message | None:
    ptype = payload.get("type")
    if ptype in _TOOL_CALL_TYPES:
        args = payload.get("arguments") or payload.get("input") or payload.get("action")
        return Message("tool", summarize_tool_call(payload.get("name") or ptype, args), timestamp)
    if ptype != "message":
        return None

    role = payload.get("role")
    if role not in ("user", "assistant"):
        return None
    content = payload.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n\n".join(b.get("text") or "" for b in content if isinstance(b, dict) and "text" in b)
    else:
        return None
    text = text.strip()

    if role == "user":
        if text.startswith(_INJECTED_PREFIXES):
            return None
        match = _DELEGATION_INPUT.search(text)
        if match:
            text = match.group(1).strip()
    if not text:
        return None
    return Message(role, text, timestamp)
