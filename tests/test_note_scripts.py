"""Tests for scripts/claude_to_notes.py and scripts/chatgpt_to_notes.py."""

from __future__ import annotations

from pathlib import Path

import chatgpt_to_notes
import claude_to_notes


def test_chatgpt_to_notes_writes_each_conversation_once(fixtures: Path, tmp_path: Path):
    out = tmp_path / "out"
    source = fixtures / "chatgpt_conversations.json"
    assert chatgpt_to_notes.main([str(source), "--out", str(out), "--all"]) == 0
    (note,) = out.glob("*.md")
    text = note.read_text(encoding="utf-8")
    assert 'source: "chatgpt"' in text
    assert 'uuid: "chatgpt-conv-0001"' in text
    assert "## ChatGPT · " in text and "## User · " in text

    note.write_text(text + "edited by hand\n", encoding="utf-8")
    assert chatgpt_to_notes.main([str(source), "--out", str(out), "--all"]) == 0
    assert note.read_text(encoding="utf-8").endswith("edited by hand\n")
    assert len(list(out.glob("*.md"))) == 1


def test_claude_to_notes_keeps_claude_headings(fixtures: Path, tmp_path: Path):
    out = tmp_path / "out"
    assert claude_to_notes.main([str(fixtures / "claude_conversations.json"), "--out", str(out)]) == 0
    (note,) = out.glob("*.md")
    text = note.read_text(encoding="utf-8")
    assert 'source: "claude"' in text and "## Claude · " in text
