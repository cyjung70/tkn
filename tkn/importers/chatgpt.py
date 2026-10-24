"""ChatGPT export importer (conversations.json, optionally inside the export ZIP).

Newer exports split conversations into conversations-000.json, conversations-001.json, ...
The path may be the export ZIP, the extracted export directory, or a single JSON file.

Messages are stored as a tree in `mapping`; the visible conversation is the path
from `current_node` back to the root.
"""

from __future__ import annotations

import io
import json
import logging
import re
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from tkn.importers._common import from_epoch, load_export_json, summarize_tool_call, title_from_messages
from tkn.models import Conversation, Message

log = logging.getLogger(__name__)

SOURCE = "chatgpt"

# Content types that carry no user-visible conversation text.
_SKIPPED_CONTENT_TYPES = {"user_editable_context", "thoughts", "reasoning_recap", "model_editable_context"}

# Inline rich-text markers in assistant answers: U+E200 <kind> (U+E202 <arg>)* U+E201.
# Citations point to search results that are not in the export, so they are dropped.
_MARKER = re.compile(r"[ \t]*\ue200([^\ue200\ue201]*)\ue201")
# Highlight brackets around cited spans and other leftover markers in the same block.
_STRAY_MARKERS = re.compile(r"[\ue200-\ue2ff]")

# Shard names in newer exports.
_SHARD = re.compile(r"conversations-\d+\.json")


def iter_conversations(path: Path) -> Iterator[Conversation]:
    for data in _load_exports(path):
        if not isinstance(data, list):
            raise ValueError("Unexpected conversations.json layout: expected a list")
        yield from _iter_parsed(data, path)


def _load_exports(path: Path) -> Iterator[Any]:
    """Yield the parsed conversation lists, one shard at a time to limit memory use."""
    if path.is_dir():
        shards = sorted(p for p in path.iterdir() if _SHARD.fullmatch(p.name))
        single = path / "conversations.json"
        if not shards and not single.is_file():
            raise FileNotFoundError(f"No conversations.json or conversations-NNN.json in {path}")
        for file in shards or [single]:
            yield load_export_json(file)
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            shards = sorted(n for n in zf.namelist() if _SHARD.fullmatch(n.rsplit("/", 1)[-1]))
            if not shards:
                yield load_export_json(path)
                return
            # Use the shallowest folder that has shards.
            folder = min((n.rpartition("/")[0] for n in shards), key=lambda d: d.count("/"))
            for name in shards:
                if name.rpartition("/")[0] == folder:
                    with zf.open(name) as raw:
                        yield json.load(io.TextIOWrapper(raw, encoding="utf-8"))
    else:
        yield load_export_json(path)


def _iter_parsed(data: list[Any], path: Path) -> Iterator[Conversation]:
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
    if role == "assistant":
        text = _clean_markers(text)
    if not text.strip():
        return None
    return Message(role, text.strip(), timestamp)


def _clean_markers(text: str) -> str:
    return _STRAY_MARKERS.sub("", _MARKER.sub(_marker_text, text))


def _marker_text(match: re.Match[str]) -> str:
    """Keep the readable part of entity, product and link markers; drop the rest."""
    kind, *args = match.group(1).split("\ue202")
    lead = match.group(0)[: match.start(1) - 1 - match.start(0)]
    if kind == "url" and len(args) >= 2 and args[1].startswith(("http://", "https://")):
        return f"{lead}[{args[0].strip()}]({args[1].strip()})"
    if kind in ("entity", "product_entity") and args:
        try:
            value = json.loads(args[0])
        except ValueError:
            value = None
        if isinstance(value, list) and len(value) >= 2 and isinstance(value[1], str):
            return lead + value[1]
    return ""


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
