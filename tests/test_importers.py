from __future__ import annotations

import zipfile
from datetime import datetime, timezone
from pathlib import Path

from tkn.importers import chatgpt, claude, claude_code, codex


def _texts(conv):
    return [(m.role, m.text) for m in conv.messages]


def test_chatgpt_follows_current_branch(fixtures: Path):
    convs = list(chatgpt.iter_conversations(fixtures / "chatgpt_conversations.json"))

    assert len(convs) == 1  # the broken conversation is skipped
    conv = convs[0]
    assert conv.id == "chatgpt-conv-0001"
    assert conv.title == "Sorting a list: in Python?"
    assert conv.created == datetime.fromtimestamp(1792713000.0, tz=timezone.utc)
    assert _texts(conv) == [
        ("user", "How do I sort a list?"),
        ("tool", "python"),
        ("assistant", "Use sorted().\n\n[image]"),
    ]


def test_chatgpt_reads_from_zip(fixtures: Path, tmp_path: Path):
    archive = tmp_path / "export.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.write(fixtures / "chatgpt_conversations.json", "conversations.json")

    assert [c.id for c in chatgpt.iter_conversations(archive)] == ["chatgpt-conv-0001"]


def test_claude_blocks_and_fallback_title(fixtures: Path):
    (conv,) = claude.iter_conversations(fixtures / "claude_conversations.json")

    assert conv.id == "claude-conv-0001"
    assert conv.title == "Explain recursion briefly"
    assert _texts(conv) == [
        ("user", "Explain recursion briefly\n\n[attachment: notes.txt]"),
        ("tool", "web_search: recursion"),
        ("assistant", "A function that calls itself."),
    ]


def test_claude_code_session(fixtures: Path):
    convs = list(claude_code.iter_conversations(fixtures / "claude_code"))

    # Subagent transcripts and bookkeeping-only files are not conversations.
    assert [c.id for c in convs] == ["sess-0001"]
    conv = convs[0]
    assert conv.title == "List demo files"
    assert conv.project == "D:/work/demo"
    assert _texts(conv) == [
        ("user", "List the files here"),
        ("tool", "Bash: ls -la"),
        ("assistant", "There are two files."),
    ]
    assert conv.created < conv.updated


def test_codex_session(fixtures: Path):
    (conv,) = codex.iter_conversations(fixtures / "codex")

    assert conv.id == "codex-0001"
    assert conv.project == "D:/work/demo"
    assert conv.title == "Run the tests please"
    assert _texts(conv) == [
        ("user", "Run the tests please"),
        ("tool", "shell: pytest -q"),
        ("assistant", "All tests passed."),
        ("user", "And check lint"),
    ]
