from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from tkn.config import Config
from tkn.models import Conversation, Message
from tkn.vault.naming import note_path, sanitize_title
from tkn.vault.render import render_note
from tkn.vault.writer import VaultWriter, read_note_key


def _conv(conv_id: str = "abc12345-xyz", title: str = "Hello", created: datetime | None = None) -> Conversation:
    created = created or datetime(2026, 10, 23, 0, 0, tzinfo=timezone.utc)
    return Conversation(
        source="chatgpt",
        id=conv_id,
        title=title,
        created=created,
        messages=[Message("user", "Hi", created), Message("assistant", "Hello!", created)],
    )


def test_sanitize_title():
    assert sanitize_title('a/b:c*d?"e<f>g|h#i^j[k]l') == "a b c d e f g h i j k l"
    assert sanitize_title("  trailing dots... ") == "trailing dots"
    assert sanitize_title("한국어 제목") == "한국어 제목"
    assert sanitize_title("///") == "Untitled"
    assert sanitize_title("CON") == "_CON"
    assert len(sanitize_title("x" * 200)) == 80
    assert sanitize_title("odd \U0005ffff\ufdd0 title \ufffe") == "odd title"


def test_note_path_uses_local_month(config: Config):
    # 2026-09-30 20:00 UTC is already October 1st in Seoul.
    conv = _conv(created=datetime(2026, 9, 30, 20, 0, tzinfo=timezone.utc))
    path = note_path(config, conv)
    assert path == config.import_root / "ChatGPT" / "2026-10" / "2026-10-01_Hello.md"


def test_render_and_read_back_key():
    conv = _conv(title='Quote " and: colon')
    conv.messages.insert(1, Message("tool", "Bash: echo `x`"))
    note = render_note(conv, ZoneInfo("Asia/Seoul"))

    assert note.startswith("---\nsource: \"chatgpt\"\nid: \"abc12345-xyz\"\n")
    assert 'title: "Quote \\" and: colon"' in note
    assert 'created: "2026-10-23T09:00:00+09:00"' in note
    assert "## User · 2026-10-23 09:00" in note
    assert "> 🔧 `Bash: echo 'x'`" in note


def test_writer_skips_existing_and_resolves_collisions(config: Config):
    writer = VaultWriter(config)
    assert writer.write(_conv("id-one"))[0] == "created"
    assert writer.write(_conv("id-one"))[0] == "exists"

    result, path = writer.write(_conv("id-two"))
    assert result == "created"
    assert path is not None and path.name == "2026-10-23_Hello (id-two).md"

    # A fresh writer rebuilds the index from frontmatter, not file names.
    assert VaultWriter(config).write(_conv("id-two"))[0] == "exists"
    assert read_note_key(path) == ("chatgpt", "id-two")


def test_writer_never_overwrites_user_edits(config: Config):
    writer = VaultWriter(config)
    _, path = writer.write(_conv())
    assert path is not None
    path.write_text(path.read_text(encoding="utf-8") + "\nMy notes\n", encoding="utf-8")

    assert VaultWriter(config).write(_conv())[0] == "exists"
    assert path.read_text(encoding="utf-8").endswith("My notes\n")


def test_empty_conversation_is_skipped(config: Config):
    conv = _conv()
    conv.messages = [Message("tool", "Bash: ls")]
    assert VaultWriter(config).write(conv) == ("empty", None)


def test_dry_run_writes_nothing(config: Config, vault: Path):
    assert VaultWriter(config, dry_run=True).write(_conv())[0] == "created"
    assert not any(vault.rglob("*.md"))
