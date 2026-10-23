"""Tool-agnostic data models shared by importers and the vault writer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

Role = Literal["user", "assistant", "tool"]

SOURCES = ("chatgpt", "claude", "claude-code", "codex")


@dataclass
class Message:
    role: Role
    # For role "tool" this is a one-line summary of the tool call, not its output.
    text: str
    timestamp: datetime | None = None


@dataclass
class Conversation:
    source: str
    id: str
    title: str
    created: datetime
    updated: datetime | None = None
    messages: list[Message] = field(default_factory=list)
    # Working directory for CLI tools (Claude Code, Codex).
    project: str | None = None
    source_path: Path | None = None

    @property
    def has_content(self) -> bool:
        return any(m.role in ("user", "assistant") for m in self.messages)
