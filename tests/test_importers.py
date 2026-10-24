from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

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


def _write_shards(fixtures: Path, folder: Path) -> list[str]:
    """Split the fixture into two shards like newer exports; return the expected ids in order."""
    (conv,) = [c for c in json.loads((fixtures / "chatgpt_conversations.json").read_text(encoding="utf-8"))
               if c.get("id") == "chatgpt-conv-0001"]
    second = {**conv, "id": "chatgpt-conv-0002", "conversation_id": "chatgpt-conv-0002"}
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "conversations-001.json").write_text(json.dumps([second]), encoding="utf-8")
    (folder / "conversations-000.json").write_text(json.dumps([conv]), encoding="utf-8")
    (folder / "export_manifest.json").write_text("{}", encoding="utf-8")
    return ["chatgpt-conv-0001", "chatgpt-conv-0002"]


def test_chatgpt_reads_sharded_export_folder(fixtures: Path, tmp_path: Path):
    expected = _write_shards(fixtures, tmp_path / "export")

    assert [c.id for c in chatgpt.iter_conversations(tmp_path / "export")] == expected


def test_chatgpt_reads_sharded_zip(fixtures: Path, tmp_path: Path):
    expected = _write_shards(fixtures, tmp_path / "export")
    archive = tmp_path / "export.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for file in (tmp_path / "export").iterdir():
            zf.write(file, f"export/{file.name}")

    assert [c.id for c in chatgpt.iter_conversations(archive)] == expected


def test_chatgpt_folder_without_conversations(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        list(chatgpt.iter_conversations(tmp_path))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Use sorted(). citeturn0search1turn0search2\nNext", "Use sorted().\nNext"),
        ("Cited span. Done.", "Cited span. Done."),
        ('See entity["software","Python",0].', "See Python."),
        ('Try product_entity["turn0product1","Some Mouse"]', "Try Some Mouse"),
        ("Docs: urlSorting HOWTOhttps://example.com/sort", "Docs: [Sorting HOWTO](https://example.com/sort)"),
        ("Bad urltitlejavascript:x.", "Bad."),
        ("entitynot json gone", " gone"),
    ],
)
def test_chatgpt_clean_markers(text: str, expected: str):
    assert chatgpt._clean_markers(text) == expected


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
