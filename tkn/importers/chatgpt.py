"""ChatGPT export importer (conversations.json, optionally inside the export ZIP).

Messages are stored as a tree in `mapping`; the visible conversation is the path
from `current_node` back to the root.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from tkn.importers._common import from_epoch, load_export_json, summarize_tool_call, title_from_messages
from tkn.models import Conversation, Message

log = logging.getLogger(__name__)

SOURCE = "chatgpt"

# Content types that carry no user-visible conversation text.
_SKIPPED_CONTENT_TYPES = {"user_editable_context", "thoughts", "reasoning_recap", "model_editable_context"}


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
            log.warning("Skipping ChatGPT conversation %s: %s", raw.get("id", "?"), exc)
            continue
        if conv is not None:
            conv.source_path = path
            yield conv


def _parse_conversation(raw: dict[str, Any]) -> Conversation | None:
    conv_id = raw.get("conversation_id") or raw.get("id")
    if not conv_id:
        raise ValueError("missing conversation id")

    messages = [m for node in _main_path(raw.get("mapping") or {}, raw.get("current_node"))
                if (m := _parse_node(node)) is not None]

    created = from_epoch(raw.get("create_time")) or next((m.timestamp for m in messages if m.timestamp), None)
    if created is None:
        raise ValueError("missing creation time")

    return Conversation(
        source=SOURCE,
        id=str(conv_id),
        title=(raw.get("title") or "").strip() or title_from_messages(messages),
        created=created,
        updated=from_epoch(raw.get("update_time")),
        messages=messages,
    )


def _main_path(mapping: dict[str, Any], current_node: Any) -> list[dict[str, Any]]:
    if current_node not in mapping:
        current_node = _latest_leaf(mapping)
    path: list[dict[str, Any]] = []
    seen: set[str] = set()
    node_id = current_node
    while node_id in mapping and node_id not in seen:
        seen.add(node_id)
        node = mapping[node_id]
        path.append(node)
        node_id = node.get("parent")
    path.reverse()
    return path


def _latest_leaf(mapping: dict[str, Any]) -> str | None:
    leaves = [(nid, n) for nid, n in mapping.items() if not n.get("children")]
    if not leaves:
        return None
    return max(leaves, key=lambda item: ((item[1].get("message") or {}).get("create_time") or 0))[0]


def _parse_node(node: dict[str, Any]) -> Message | None:
    msg = node.get("message")
    if not isinstance(msg, dict):
        return None
    metadata = msg.get("metadata") or {}
    if metadata.get("is_visually_hidden_from_conversation"):
        return None

    role = (msg.get("author") or {}).get("role")
    timestamp = from_epoch(msg.get("create_time"))

    # Assistant messages addressed to a tool (browser, python, ...) are tool calls.
    recipient = msg.get("recipient") or "all"
    if role == "assistant" and recipient != "all":
        return Message("tool", summarize_tool_call(recipient, None), timestamp)
    if role not in ("user", "assistant"):
        # System and tool output messages are skipped.
        return None

    text = _content_text(msg.get("content") or {})
    if not text.strip():
        return None
    return Message(role, text.strip(), timestamp)


def _content_text(content: dict[str, Any]) -> str:
    ctype = content.get("content_type")
    if ctype in _SKIPPED_CONTENT_TYPES:
        return ""
    if ctype == "code":
        lang = content.get("language") or ""
        if lang == "unknown":
            lang = ""
        return f"```{lang}\n{content.get('text') or ''}\n```"
    parts = content.get("parts")
    if isinstance(parts, list):
        return "\n\n".join(t for t in (_part_text(p) for p in parts) if t)
    text = content.get("text")
    return text if isinstance(text, str) else ""


def _part_text(part: Any) -> str:
    if isinstance(part, str):
        return part
    if isinstance(part, dict):
        if part.get("content_type") == "image_asset_pointer":
            return "[image]"
        if isinstance(part.get("text"), str):
            return part["text"]
        return "[attachment]"
    return ""
