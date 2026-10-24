"""Tests for the topic scripts in scripts/ (synthetic notes only)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import classify_notes
import create_topic_notes
import link_topic_notes
from conftest import ROOT_FOLDER

PROPOSAL = Path(__file__).parent / "fixtures" / "topics_proposal.md"


def _note(path: Path, source: str, conv_id: str, title: str, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    head = "\n".join(
        [
            "---",
            f"source: {json.dumps(source)}",
            f"id: {json.dumps(conv_id)}",
            f"title: {json.dumps(title, ensure_ascii=False)}",
            "---",
            "",
        ]
    )
    path.write_text(head + body, encoding="utf-8", newline="\n")
    return path


def _hashes(root: Path) -> dict[Path, str]:
    return {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*.md"))}


@pytest.fixture
def raw(vault: Path) -> Path:
    """A small 01_Original-style folder with three synthetic notes."""
    root = vault / ROOT_FOLDER / "Claude" / "2026-10"
    _note(root / "2026-10-01_Database talk.md", "claude", "id-db", "Database talk", "We use PostgreSQL and NVL.\n재고를 확인했다.\n")
    _note(root / "2026-10-02_Hello.md", "claude", "id-hello", "Hello", "보안 보안 보안 그리고 개인정보.\n")
    _note(root / "2026-10-03_Small talk.md", "claude", "id-small", "Small talk", "Nothing technical here. Dates like 2026-MM-01.\n")
    return vault / ROOT_FOLDER


# --- create_topic_notes -------------------------------------------------------


def test_read_topics_parses_only_the_numbered_table():
    topics = create_topic_notes.read_topics(PROPOSAL)
    assert [t.name for t in topics] == ["Demo-Databases", "Demo-Tools", "Demo-Security"]
    assert topics[2].description == "Security for tests"
    assert topics[2].keywords == "SQL injection, secrets"


def test_render_topic_note_has_frontmatter_and_empty_notes_section():
    text = create_topic_notes.render(create_topic_notes.Topic("Demo-Tools", "Tooling", "`.gitignore`"))
    assert text.startswith('---\ntype: "topic"\ntopic: "Demo-Tools"\n---\n')
    assert "**Keywords:** `.gitignore`" in text
    assert text.rstrip().endswith("## Notes")


def test_unclassified_note_has_no_keywords_line():
    assert "**Keywords:**" not in create_topic_notes.render(create_topic_notes.UNCLASSIFIED)


def test_create_topic_notes_dry_run_then_create_then_skip(config_file: Path, vault: Path):
    args = ["--proposal", str(PROPOSAL), "--config", str(config_file)]
    topics_dir = vault / create_topic_notes.DEFAULT_FOLDER

    assert create_topic_notes.main([*args, "--dry-run"]) == 0
    assert not topics_dir.exists()

    assert create_topic_notes.main(args) == 0
    names = sorted(p.stem for p in topics_dir.glob("*.md"))
    assert names == ["Demo-Databases", "Demo-Security", "Demo-Tools", "Unclassified"]

    edited = topics_dir / "Demo-Tools.md"
    edited.write_text("my own edits\n", encoding="utf-8")
    assert create_topic_notes.main(args) == 0
    assert edited.read_text(encoding="utf-8") == "my own edits\n"


# --- classify_notes: term derivation and matching ------------------------------


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        ("MM (purchasing, inventory)", ["MM", "purchasing", "inventory"]),
        ("`NVL`→`COALESCE`", ["NVL", "COALESCE"]),
        ("IntelliJ / PyCharm", ["IntelliJ", "PyCharm"]),
        ("`''` vs `NULL`", ["NULL"]),
        ('"확인 필요" marking', ["확인 필요", "확인 필요 marking"]),
        ("ChatGPT `conversations.json`", ["conversations.json", "ChatGPT conversations.json"]),
    ],
)
def test_item_terms(item: str, expected: list[str]):
    assert classify_notes.item_terms(item) == expected


def test_split_items_keeps_commas_inside_parentheses_and_drops_source_marker():
    items = classify_notes.split_items("MM (purchasing, inventory), BOM, approval gates *(local docs)*")
    assert items == ["MM (purchasing, inventory)", "BOM", "approval gates"]


def test_acronyms_are_case_sensitive_and_ignore_date_parts():
    mm = classify_notes.term_pattern("MM")
    assert mm.search("the MM module")
    assert not mm.search("mm of rain")
    assert not mm.search("YYYY-MM-DD")


def test_words_match_case_insensitively_on_word_boundaries():
    pattern = classify_notes.term_pattern("inventory")
    assert pattern.search("Inventory report")
    assert not pattern.search("inventorying")


def test_korean_terms_match_with_particles():
    pattern = classify_notes.term_pattern("재고")
    assert pattern.search("재고를 확인했다")


def test_read_korean_terms_with_minimum_counts():
    terms = classify_notes.read_korean_terms(PROPOSAL)
    assert terms["Demo-Security"] == [("보안", 3), ("개인정보", 1)]
    assert terms["Demo-Tools"] == [("깃허브", 1)]


def _patterns() -> classify_notes.Patterns:
    korean = classify_notes.read_korean_terms(PROPOSAL)
    patterns: classify_notes.Patterns = {}
    for topic in create_topic_notes.read_topics(PROPOSAL):
        terms = {t: 1 for item in classify_notes.split_items(topic.keywords) for t in classify_notes.item_terms(item)}
        for term, minimum in korean.get(topic.name, []):
            terms.setdefault(term, minimum)
        patterns[topic.name] = [(t, classify_notes.term_pattern(t), m) for t, m in terms.items()]
    return patterns


def test_classify_uses_min_hits_title_hits_and_unclassified(tmp_path: Path):
    patterns = _patterns()
    db = _note(tmp_path / "a.md", "claude", "a", "Notes", "PostgreSQL and NVL.\n")
    weak = _note(tmp_path / "b.md", "claude", "b", "Notes", "PostgreSQL once.\n")
    titled = _note(tmp_path / "c.md", "claude", "c", "PostgreSQL tips", "no keywords in the body\n")

    assert classify_notes.classify(db, patterns, min_hits=2).suggested == ["Demo-Databases"]
    result = classify_notes.classify(weak, patterns, min_hits=2)
    assert result.suggested == ["Unclassified"]
    assert "Demo-Databases" in result.matches  # listed as a weak match
    assert classify_notes.classify(titled, patterns, min_hits=2).suggested == ["Demo-Databases"]


def test_per_term_minimum_count(tmp_path: Path):
    patterns = _patterns()
    two = _note(tmp_path / "a.md", "claude", "a", "Notes", "보안 보안 개인정보\n")
    three = _note(tmp_path / "b.md", "claude", "b", "Notes", "보안 보안 보안\n")

    result = classify_notes.classify(two, patterns, min_hits=2)
    assert "보안" not in result.matches.get("Demo-Security", {})
    assert result.suggested == ["Unclassified"]  # only 개인정보 ×1 counts
    assert classify_notes.classify(three, patterns, min_hits=2).suggested == ["Demo-Security"]


def test_classify_main_writes_review_and_leaves_notes_untouched(config_file: Path, raw: Path, tmp_path: Path):
    before = _hashes(raw)
    out = tmp_path / "review.md"
    assert classify_notes.main(["--proposal", str(PROPOSAL), "--out", str(out), "--config", str(config_file)]) == 0
    assert _hashes(raw) == before

    rows = dict(link_topic_notes.read_review(out))
    assert rows["Claude/2026-10/2026-10-01_Database talk.md"] == ["Demo-Databases"]
    assert rows["Claude/2026-10/2026-10-02_Hello.md"] == ["Demo-Security"]
    assert rows["Claude/2026-10/2026-10-03_Small talk.md"] == ["Unclassified"]


# --- link_topic_notes -----------------------------------------------------------


def test_read_review_handles_escaped_pipes(tmp_path: Path):
    review = tmp_path / "review.md"
    review.write_text(
        "| Note | Source | Suggested topics | Matched keywords | Weak matches |\n"
        "|---|---|---|---|---|\n"
        "| Claude/2026-10/a \\| b.md | claude | T1, T2 | **T1**: `x` ×2 | — |\n",
        encoding="utf-8",
    )
    assert link_topic_notes.read_review(review) == [("Claude/2026-10/a | b.md", ["T1", "T2"])]


def test_add_links_appends_inside_the_notes_section():
    text = "# T\n\n## Notes\n\n- [[a|a]]\n\n## Later\n\nkeep me\n"
    updated = link_topic_notes.add_links(text, ["- [[b|b]]"])
    assert updated == "# T\n\n## Notes\n\n- [[a|a]]\n- [[b|b]]\n\n## Later\n\nkeep me\n"


def test_add_links_before_a_heading_without_blank_line():
    updated = link_topic_notes.add_links("## Notes\n- [[a|a]]\n## Later\n", ["- [[b|b]]"])
    assert updated == "## Notes\n- [[a|a]]\n- [[b|b]]\n\n## Later\n"


def test_add_links_to_an_empty_notes_section():
    assert link_topic_notes.add_links("# T\n\n## Notes\n", ["- [[b|b]]"]) == "# T\n\n## Notes\n\n- [[b|b]]\n"


def test_add_links_without_notes_section_returns_none():
    assert link_topic_notes.add_links("# T\n", ["- [[b|b]]"]) is None


@pytest.mark.parametrize(
    ("current", "status", "expected"),
    [
        ("default", "updated", "[[t|New title]]"),
        ("New title", "current", "[[t|New title]]"),
        ("my edit", "edited", "[[t|my edit]]"),
    ],
)
def test_update_alias(current: str, status: str, expected: str):
    text, result = link_topic_notes.update_alias(f"- [[t|{current}]]\n", "t", "default", "New title")
    assert result == status
    assert text == f"- {expected}\n"


def test_read_overrides_skips_header_and_unsafe_titles(tmp_path: Path, capsys):
    path = tmp_path / "Title-Overrides.md"
    path.write_text(
        "| source | id | title | original title |\n"
        "|---|---|---|---|\n"
        "| claude | id-1 | 2026-10-01_Better title | Hello |\n"
        "| claude | id-2 | bad [[link]] title | Hi |\n",
        encoding="utf-8",
    )
    assert link_topic_notes.read_overrides(path) == {("claude", "id-1"): "2026-10-01_Better title"}
    assert "skip override" in capsys.readouterr().err
    assert link_topic_notes.read_overrides(tmp_path / "missing.md") == {}


def _setup_links(config_file: Path, vault: Path, raw: Path, tmp_path: Path) -> tuple[Path, Path, list[str]]:
    create_topic_notes.main(["--proposal", str(PROPOSAL), "--config", str(config_file)])
    review = tmp_path / "review.md"
    classify_notes.main(["--proposal", str(PROPOSAL), "--out", str(review), "--config", str(config_file)])
    args = ["--review", str(review), "--config", str(config_file), "--overrides", str(tmp_path / "overrides.md")]
    return vault / create_topic_notes.DEFAULT_FOLDER, review, args


def test_link_main_adds_links_once_and_never_touches_raw_notes(config_file: Path, vault: Path, raw: Path, tmp_path: Path):
    topics_dir, _, args = _setup_links(config_file, vault, raw, tmp_path)
    before_raw = _hashes(raw)

    before_topics = _hashes(topics_dir)
    assert link_topic_notes.main([*args, "--dry-run"]) == 0
    assert _hashes(topics_dir) == before_topics

    assert link_topic_notes.main(args) == 0
    db = (topics_dir / "Demo-Databases.md").read_text(encoding="utf-8")
    assert f"- [[{ROOT_FOLDER}/Claude/2026-10/2026-10-01_Database talk|2026-10-01_Database talk]]" in db
    unclassified = (topics_dir / "Unclassified.md").read_text(encoding="utf-8")
    assert "2026-10-03_Small talk]]" in unclassified

    after_first = _hashes(topics_dir)
    assert link_topic_notes.main(args) == 0
    assert _hashes(topics_dir) == after_first
    assert _hashes(raw) == before_raw


def test_link_main_applies_overrides_but_keeps_hand_edits(config_file: Path, vault: Path, raw: Path, tmp_path: Path):
    topics_dir, _, args = _setup_links(config_file, vault, raw, tmp_path)
    assert link_topic_notes.main(args) == 0

    security = topics_dir / "Demo-Security.md"
    db = topics_dir / "Demo-Databases.md"
    db.write_text(db.read_text(encoding="utf-8").replace("|2026-10-01_Database talk]]", "|my label]]"), encoding="utf-8")

    (tmp_path / "overrides.md").write_text(
        "| source | id | title | original title |\n"
        "|---|---|---|---|\n"
        "| claude | id-hello | 2026-10-02_Security basics | Hello |\n"
        "| claude | id-db | 2026-10-01_Database overview | Database talk |\n",
        encoding="utf-8",
    )
    assert link_topic_notes.main(args) == 0

    assert "|2026-10-02_Security basics]]" in security.read_text(encoding="utf-8")
    assert "|my label]]" in db.read_text(encoding="utf-8")
    assert "Database overview" not in db.read_text(encoding="utf-8")
