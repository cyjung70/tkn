from __future__ import annotations

from pathlib import Path

import pytest

from tkn.cli import main


def _notes(vault: Path) -> dict[Path, str]:
    return {p: p.read_text(encoding="utf-8") for p in vault.rglob("*.md")}


@pytest.mark.parametrize(
    ("source", "path_arg", "expected"),
    [
        ("chatgpt", "chatgpt_conversations.json", "Imported/ChatGPT/2026-10/2026-10-23_Sorting a list in Python.md"),
        ("claude", "claude_conversations.json", "Imported/Claude/2026-10/2026-10-02_Explain recursion briefly.md"),
        ("claude-code", None, "Imported/Claude Code/2026-10/2026-10-05_List demo files.md"),
        ("codex", None, "Imported/Codex/2026-10/2026-10-05_Run the tests please.md"),
    ],
)
def test_import_is_idempotent(source, path_arg, expected, fixtures: Path, vault: Path, config_file: Path, capsys):
    argv = ["import", source, "--config", str(config_file)]
    if path_arg:
        argv.insert(2, str(fixtures / path_arg))

    assert main(argv) == 0
    first = _notes(vault)
    assert [p.relative_to(vault).as_posix() for p in first] == [expected]

    assert main(argv) == 0
    assert _notes(vault) == first
    assert "created 0, skipped (exists) 1" in capsys.readouterr().out


def test_private_content_is_not_written(fixtures: Path, vault: Path, config_file: Path):
    main(["import", "claude-code", "--config", str(config_file)])
    main(["import", "codex", "--config", str(config_file)])
    text = "\n".join(_notes(vault).values())
    for marker in ("SECRET OUTPUT", "META CONTENT", "SIDECHAIN", "SUBAGENT", "TOOL OUTPUT", "DEVELOPER", "DUPLICATE"):
        assert marker not in text


def test_missing_config_returns_error(tmp_path: Path):
    assert main(["import", "codex", "--config", str(tmp_path / "nope.toml")]) == 2
