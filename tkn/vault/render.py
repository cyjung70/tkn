"""Render a Conversation as an Obsidian Markdown note."""

from __future__ import annotations

import json
from datetime import datetime, tzinfo

from tkn.models import Conversation

_ROLE_HEADINGS = {"user": "User", "assistant": "Assistant"}


def render_note(conv: Conversation, tz: tzinfo) -> str:
    lines = ["---", *_frontmatter_lines(conv, tz), "---", "", f"# {conv.title}", ""]

    current_role: str | None = None
    for message in conv.messages:
        if message.role == "tool":
            # Tool calls are shown inline under the current speaker, without a heading.
            summary = message.text.replace("`", "'")
            lines += [f"> 🔧 `{summary}`", ""]
            continue
        if message.role != current_role:
            heading = _ROLE_HEADINGS[message.role]
            if message.timestamp:
                heading += f" · {message.timestamp.astimezone(tz):%Y-%m-%d %H:%M}"
            lines += [f"## {heading}", ""]
            current_role = message.role
        lines += [message.text, ""]

    return "\n".join(lines).rstrip("\n") + "\n"


def _frontmatter_lines(conv: Conversation, tz: tzinfo) -> list[str]:
    # Values are JSON-encoded; a JSON string is a valid YAML scalar.
    fields: dict[str, object] = {
        "source": conv.source,
        "id": conv.id,
        "title": conv.title,
        "created": _iso(conv.created, tz),
    }
    if conv.updated:
        fields["updated"] = _iso(conv.updated, tz)
    if conv.project:
        fields["project"] = conv.project
    return [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()]


def _iso(value: datetime, tz: tzinfo) -> str:
    return value.astimezone(tz).isoformat(timespec="seconds")
