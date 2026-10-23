"""Claude (claude.ai) export importer (conversations.json, optionally inside the export ZIP)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from tkn.importers._common import load_export_json, parse_iso, summarize_tool_call, title_from_messages
from tkn.models import Conversation, Message

log = logging.getLogger(__name__)

SOURCE = "claude"

_ROLES = {"human": "user", "assistant": "assistant"}


def iter_conversations(path: Path) -> Iterator[Conversation]:
    data = load_export_json(path)
    if not isinstance(data, list):
        raise ValueError("Unexpected conversations.json layout: expected a list")
    for raw in data:
        if not isinstance(raw, dict):
            continue
        try:
            conv = _parse_conversation(raw)
        except Exception as exc:
            log.warning("Skipping Claude conversation %s: %s", raw.get("uuid", "?"), exc)
            continue
        conv.source_path = path
        yield conv


def _parse_conversation(raw: dict[str, Any]) -> Conversation:
    conv_id = raw.get("uuid")
    if not conv_id:
        raise ValueError("missing uuid")

    messages: list[Message] = []
    for chat_message in raw.get("chat_messages") or []:
        if isinstance(chat_message, dict):
            messages.extend(_parse_message(chat_message))

    created = parse_iso(raw.get("created_at")) or next((m.timestamp for m in messages if m.timestamp), None)
    if created is None:
        raise ValueError("missing creation time")

    return Conversation(
        source=SOURCE,
        id=str(conv_id),
        title=(raw.get("name") or "").strip() or title_from_messages(messages),
        created=created,
        updated=parse_iso(raw.get("updated_at")),
        messages=messages,
    )


def _parse_message(chat_message: dict[str, Any]) -> list[Message]:
    role = _ROLES.get(chat_message.get("sender") or "")
    if role is None:
        return []
    timestamp = parse_iso(chat_message.get("created_at"))

    result: list[Message] = []
    texts: list[str] = []

    def flush_text() -> None:
        text = "\n\n".join(t for t in texts if t.strip()).strip()
        if text:
            result.append(Message(role, text, timestamp))
        texts.clear()

    content = chat_message.get("content")
    if isinstance(content, list) and content:
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                texts.append(block.get("text") or "")
            elif btype == "tool_use":
                flush_text()
                result.append(Message("tool", summarize_tool_call(block.get("name") or "", block.get("input")), timestamp))
            # thinking, tool_result and unknown blocks are skipped.
    else:
        texts.append(chat_message.get("text") or "")

    for item in (chat_message.get("attachments") or []) + (chat_message.get("files") or []):
        if isinstance(item, dict):
            name = item.get("file_name") or item.get("file_uuid") or "file"
            texts.append(f"[attachment: {name}]")

    flush_text()
    return result
