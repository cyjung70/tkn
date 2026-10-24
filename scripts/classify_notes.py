"""Suggest topics for vault notes by keyword matching, and write a review file.

Keywords come from the topic table and the Korean keyword table in docs/TOPICS_PROPOSAL.md. Notes are read from
<vault_path>/<root_folder> (tkn.toml) and are never modified. Nothing is written to the vault;
the only output is the review file. No external services are used.

A topic is suggested when its keywords occur at least --min-hits times in a note's body, or at
least once in its title. Notes with no suggested topic go to "Unclassified".

Usage:
    python scripts/classify_notes.py [--proposal FILE] [--out FILE] [--min-hits N] [--config tkn.toml]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from create_topic_notes import UNCLASSIFIED, read_topics
from tkn.config import ConfigError, load_config

DEFAULT_PROPOSAL = Path("docs/TOPICS_PROPOSAL.md")
DEFAULT_OUT = Path("docs/CLASSIFICATION_REVIEW.md")
DEFAULT_CONFIG = Path("tkn.toml")
DEFAULT_MIN_HITS = 2

_SOURCE_MARKER = "*(local docs)*"

# | `Topic-Name` | 키워드, 키워드 |  (the Korean keyword table)
_KOREAN_ROW = re.compile(r"^\|\s*`([A-Za-z0-9-]+)`\s*\|(.*)\|\s*$")
_HANGUL = re.compile(r"[가-힣]")
# "보안 (3+)": the term only counts with at least 3 occurrences.
_TERM_MIN = re.compile(r"^(.*?)\s*\((\d+)\+\)$")


@dataclass
class NoteResult:
    path: Path
    source: str
    title: str
    # topic -> term -> (body hits, in title)
    matches: dict[str, dict[str, tuple[int, bool]]] = field(default_factory=dict)
    suggested: list[str] = field(default_factory=list)


def split_items(cell: str) -> list[str]:
    """Split a keyword cell on commas that are not inside parentheses."""
    items, depth, current = [], 0, ""
    for ch in cell.replace(_SOURCE_MARKER, ""):
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if ch == "," and depth == 0:
            items.append(current)
            current = ""
        else:
            current += ch
    items.append(current)
    return [item.strip() for item in items if item.strip()]


def item_terms(item: str) -> list[str]:
    """Turn one keyword item into match terms.

    "MM (purchasing, inventory)" -> MM, purchasing, inventory
    "`NVL`→`COALESCE`", "IntelliJ / PyCharm", "`''` vs `NULL`" -> both sides
    Backticked or quoted parts become terms of their own, as does the whole phrase.
    """
    parts = [item]
    if (paren := re.match(r"^(.*?)\s*\((.*)\)\s*$", item)) and "`" not in item:
        parts = [paren.group(1), *(p.strip() for p in paren.group(2).split(","))]
    terms: list[str] = []
    for part in parts:
        for side in re.split(r"\s*→\s*|\s+/\s+|\s+vs\s+", part):
            for code, quoted in re.findall(r"`([^`]+)`|\"([^\"]+)\"", side):
                terms.append(code or quoted)
            terms.append(side.replace("`", "").replace('"', "").strip())
    # Drop duplicates and terms without letters or digits (such as '').
    return [t for t in dict.fromkeys(terms) if re.search(r"\w", t)]


def read_korean_terms(proposal: Path) -> dict[str, list[tuple[str, int]]]:
    """Return topic -> [(term, minimum occurrences)] from the Korean keyword table."""
    terms: dict[str, list[tuple[str, int]]] = {}
    with proposal.open(encoding="utf-8") as f:
        for line in f:
            if match := _KOREAN_ROW.match(line.strip()):
                entries = []
                for raw in (t.strip() for t in match.group(2).split(",")):
                    if not raw:
                        continue
                    if minimum := _TERM_MIN.match(raw):
                        entries.append((minimum.group(1), int(minimum.group(2))))
                    else:
                        entries.append((raw, 1))
                terms[match.group(1)] = entries
    return terms


def term_pattern(term: str) -> re.Pattern[str]:
    # Korean particles attach to words (재고를), so Korean terms match as substrings.
    # Otherwise word boundaries also exclude "-", so "MM" does not match "YYYY-MM-DD".
    korean = bool(_HANGUL.search(term))
    prefix = r"(?<![\w-])" if re.match(r"\w", term) and not korean else ""
    suffix = r"(?![\w-])" if re.search(r"\w$", term) and not korean else ""
    # Short upper-case terms (MM, SD, NVL, DUAL) are acronyms: match case-sensitively.
    flags = 0 if term.isupper() and len(term) <= 6 else re.IGNORECASE
    return re.compile(prefix + re.escape(term) + suffix, flags)


def read_note(path: Path) -> tuple[dict[str, str], str]:
    """Return (frontmatter fields, body) of a note."""
    text = path.read_text(encoding="utf-8", errors="replace")
    fields: dict[str, str] = {}
    if not text.startswith("---\n"):
        return fields, text
    head, sep, body = text[4:].partition("\n---\n")
    if not sep:
        return fields, text
    for line in head.splitlines():
        key, colon, raw = line.partition(":")
        if colon:
            raw = raw.strip()
            try:
                fields[key.strip()] = str(json.loads(raw)) if raw.startswith('"') else raw
            except ValueError:
                fields[key.strip()] = raw
    return fields, body


Patterns = dict[str, list[tuple[str, re.Pattern[str], int]]]


def classify(path: Path, patterns: Patterns, min_hits: int) -> NoteResult:
    fields, body = read_note(path)
    result = NoteResult(path, fields.get("source", "?"), fields.get("title", path.stem))
    for topic, terms in patterns.items():
        found = {}
        for term, pattern, term_min in terms:
            hits, in_title = len(pattern.findall(body)), bool(pattern.search(result.title))
            if hits < term_min and not in_title:
                continue
            if hits or in_title:
                found[term] = (hits, in_title)
        if not found:
            continue
        result.matches[topic] = found
        if sum(h for h, _ in found.values()) >= min_hits or any(t for _, t in found.values()):
            result.suggested.append(topic)
    if not result.suggested:
        result.suggested.append(UNCLASSIFIED.name)
    return result


def _format_terms(found: dict[str, tuple[int, bool]]) -> str:
    ranked = sorted(found.items(), key=lambda kv: (-kv[1][0], kv[0]))
    return ", ".join(f"`{t}` ×{h}" + (" (title)" if in_title else "") for t, (h, in_title) in ranked)


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_review(results: list[NoteResult], topics: list[str], root: Path, min_hits: int, proposal: Path) -> str:
    counts = Counter(t for r in results for t in r.suggested)
    lines = [
        "# Classification Review",
        "",
        f"Generated by `scripts/classify_notes.py` on {datetime.now().astimezone():%Y-%m-%d %H:%M %z}. "
        "**Suggestions only — nothing has been written to the vault.**",
        "",
        f"- Notes: `{root}` ({len(results)} notes, read-only)",
        f"- Keywords: `{proposal}`",
        f"- Rule: a topic is suggested when its keywords occur at least {min_hits} times in the body, "
        "or at least once in the title. Otherwise the matches are listed as *weak*.",
        "- Matching is case-insensitive, except short upper-case acronyms (`MM`, `SD`, `NVL`, …). "
        "Korean keywords match as substrings, since particles attach to words.",
        "",
        "## Summary",
        "",
        "| Topic | Notes |",
        "|---|---|",
        *(f"| {t} | {counts.get(t, 0)} |" for t in topics),
        "",
        "## Notes",
        "",
        "| Note | Source | Suggested topics | Matched keywords | Weak matches |",
        "|---|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda r: str(r.path)):
        strong = "<br>".join(f"**{t}**: {_format_terms(r.matches[t])}" for t in r.suggested if t in r.matches)
        weak = "<br>".join(f"{t}: {_format_terms(f)}" for t, f in r.matches.items() if t not in r.suggested)
        rel = r.path.relative_to(root).as_posix()
        lines.append(
            f"| {_cell(rel)} | {r.source} | {', '.join(r.suggested)} | {_cell(strong) or '—'} | {_cell(weak) or '—'} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL, help=f"default: {DEFAULT_PROPOSAL}")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"review file (default: {DEFAULT_OUT})")
    parser.add_argument("--min-hits", type=int, default=DEFAULT_MIN_HITS, help=f"default: {DEFAULT_MIN_HITS}")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help=f"default: {DEFAULT_CONFIG}")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    topics = read_topics(args.proposal)
    if not topics:
        print(f"No topics found in {args.proposal}", file=sys.stderr)
        return 1

    korean = read_korean_terms(args.proposal)
    patterns: Patterns = {}
    for t in topics:
        terms = {term: 1 for item in split_items(t.keywords) for term in item_terms(item)}
        for term, term_min in korean.get(t.name, []):
            terms.setdefault(term, term_min)
        patterns[t.name] = [(term, term_pattern(term), term_min) for term, term_min in terms.items()]
    root = config.import_root
    results = [classify(p, patterns, args.min_hits) for p in sorted(root.rglob("*.md"))]

    names = [t.name for t in topics] + [UNCLASSIFIED.name]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_review(results, names, root, args.min_hits, args.proposal), encoding="utf-8", newline="\n")

    unclassified = sum(1 for r in results if r.suggested == [UNCLASSIFIED.name])
    print(f"Classified {len(results)} notes ({unclassified} unclassified) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
