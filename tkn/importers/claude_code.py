"""Claude Code session importer (~/.claude/projects/<encoded-path>/<session-id>.jsonl)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from tkn.importers._common import iter_jsonl, parse_iso, summarize_tool_call, title_from_messages
from tkn.models import Conversation, Message

log = logging.getLogger(__name__)

SOURCE = "claude-code"

# User "messages" that are really slash-command bookkeeping, not prompts.
_COMMAND_PREFIXES = ("<command-", "<local-command-")


def iter_conversations(root: Path) -> Iterator[Conversation]:
    if not root.is_dir():
        raise FileNotFoundError(f"Claude Code projects directory not found: {root}")
    for path in sorted(root.rglob("*.jsonl")):
        # Subagent transcripts live in nested folders and belong to their parent session.
        if "subagents" in path.relative_to(root).parts:
            continue
        try:
            conv = parse_session(path)
        except Exception as exc:
            log.warning("Skipping Claude Code session %s: %s", path.name, exc)
            continue
        if conv is not None:
            yield conv


def parse_session(path: Path) -> Conversation | None:
    session_id: str | None = None
    project: str | None = None
    ai_title: str | None = None
    summary_title: str | None = None
    timestamps: list[datetime] = []
    messages: list[Message] = []

    for entry in iter_jsonl(path):
        etype = entry.get("type")
        if etype == "ai-title" and entry.get("aiTitle"):
            ai_title = str(entry["aiTitle"])
            continue
        if etype == "summary" and entry.get("summary"):
            summary_title = str(entry["summary"])
            continue
        if etype not in ("user", "assistant"):
            continue

        session_id = session_id or entry.get("sessionId")
        project = project or entry.get("cwd")
        timestamp = parse_iso(entry.get("timestamp"))
        if timestamp:
            timestamps.append(timestamp)
        if entry.get("isSidechain") or entry.get("isMeta") or entry.get("isCompactSummary"):
            continue
        message = entry.get("message")
        if isinstance(message, dict):
            messages.extend(_parse_content(etype, message.get("content"), timestamp))

    if not timestamps:
        # No conversation entries at all (e.g. a file with only bookkeeping lines).
        return None

    return Conversation(
        source=SOURCE,
        id=session_id or path.stem,
        title=(ai_title or summary_title or "").strip() or title_from_messages(messages),
        created=min(timestamps),
        updated=max(timestamps),
        messages=messages,
        project=project,
        source_path=path,
    )


def _parse_content(role: str, content: Any, timestamp: datetime | None) -> list[Message]:
    if isinstance(content, str):
        text = content.strip()
        if not text or text.startswith(_COMMAND_PREFIXES):
            return []
        return [Message(role, text, timestamp)]  # type: ignore[arg-type]

    result: list[Message] = []
    if not isinstance(content, list):
        return result
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "text":
            text = (block.get("text") or "").strip()
            if text and not text.startswith(_COMMAND_PREFIXES):
                result.append(Message(role, text, timestamp))  # type: ignore[arg-type]
        elif btype == "tool_use":
            result.append(Message("tool", summarize_tool_call(block.get("name") or "", block.get("input")), timestamp))
        elif btype == "image":
            result.append(Message(role, "[image]", timestamp))  # type: ignore[arg-type]
        # thinking, tool_result and unknown blocks are skipped.
    return result
