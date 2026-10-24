# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Language Rule

**Write CLAUDE.md, all code, comments, and commit messages in English only.**

This covers identifiers, docstrings, log/error messages, test names, and documentation in the repo. Conversation content imported from users (which may be in Korean or other languages) is data and is stored as-is.

## Project Overview

**TKN** is a Python program that imports conversation histories from several AI tools, saves them as Markdown notes in an Obsidian vault organized by tool, and classifies them by topic.

Supported tools:

| Tool | Expected input source | Format |
|------|-----------------------|--------|
| ChatGPT | `conversations.json`, or `conversations-000.json`, `-001.json`, ... in newer exports, from the Settings → Data export ZIP | JSON. Messages are stored as a `mapping` tree (each node has `parent`/`children`); walk back from `current_node` to recover the main conversation path |
| Claude (claude.ai) | `conversations.json` from the Settings → Export data ZIP | JSON. Per-conversation `chat_messages` array (`sender`: `human`/`assistant`) |
| Codex (CLI) | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | JSONL, one event per line |
| Claude Code | `~/.claude/projects/<encoded-path>/<session-id>.jsonl` | JSONL, one message/event per line, linked via `parentUuid` |

> These formats can change between versions. When writing or updating a parser, check against real sample files, ignore unknown fields, and handle missing fields defensively instead of crashing.

## Status

v0.1 (conversation import) is implemented. Topic classification and updating changed notes are not yet implemented.

## Commands

```powershell
python -m venv .venv; .venv\Scripts\pip install -e ".[dev]"   # setup (Python 3.11+)
.venv\Scripts\python -m pytest                                  # tests
tkn import chatgpt <export.zip|export folder|conversations.json> [--dry-run] [--since YYYY-MM-DD] [-v]
tkn import claude  <export.zip|conversations.json>
tkn import claude-code [dir]    # default from config, else ~/.claude/projects
tkn import codex [dir]          # default from config, else ~/.codex/sessions
```

Config is read from `./tkn.toml` (gitignored; copy `tkn.example.toml`) or `--config`.

## Behavior

1. **Import** (`tkn/importers/`): each parser converts one tool's files into `Conversation`/`Message` (`tkn/models.py`). Malformed records are logged and skipped
2. **Write** (`tkn/vault/`): one Markdown note per conversation
3. **Dedup**: before writing, the vault's frontmatter is scanned for `(source, id)`. Existing conversations are always skipped, never overwritten (v0.1 does not update notes whose source changed)
4. **Classify** (planned): topics via tags, frontmatter, and `Topics/<topic>.md` index notes

## Structure

```
tkn/
  models.py          # Conversation, Message
  config.py          # tkn.toml loading
  importers/         # chatgpt.py, claude.py, claude_code.py, codex.py, _common.py
  vault/             # naming.py (paths), render.py (Markdown), writer.py (index + write/skip)
  cli.py             # `tkn` entry point
tests/
  fixtures/          # Hand-written synthetic samples only, never real conversations
```

To add a new tool, add one parser under `importers/` that returns only the common model, so the vault and classify stages stay tool-agnostic.

## Importer Notes

- ChatGPT: follow the `current_node` -> root path; assistant messages with `recipient != "all"` are tool calls
- Claude Code: skip `isSidechain`, `isMeta`, `subagents/` files, `thinking`, `tool_result`, and `<command-...>` lines. Title from the `ai-title` entry
- Codex: use `response_item` only (`realtime_item` transcript segments duplicate it). Skip injected `<environment_context>`-style user messages; unwrap `<realtime_delegation><input>`
- Tool calls are rendered as a one-line summary (``> 🔧 `Bash: git status` ``); tool output is never written

## Obsidian Vault Conventions

- Path: `<vault>/<root_folder>/<Tool>/<YYYY-MM>/<YYYY-MM-DD>_<title>.md`. Dates use the configured time zone
- Titles: characters `\ / : * ? " < > | # ^ [ ]` and control chars replaced, max 80 chars. Name collisions get ` (<id prefix>)`
- Frontmatter values are JSON-quoted strings (valid YAML):
  ```yaml
  ---
  source: "chatgpt"        # chatgpt | claude | claude-code | codex
  id: "<original ID>"      # deduplication key together with source
  title: "..."
  created: "2026-10-23T08:50:00+09:00"
  updated: "..."           # when known
  project: "D:\dev\tkn"  # Claude Code / Codex working directory
  ---
  ```
- `(source, id)` identifies a conversation. File names may change, so never use them for identification.
- Never overwrite content the user edited in the vault.

## Development Guidelines

- Target Python 3.11+, with type hints
- Always pass `encoding="utf-8"` for file I/O (avoids Windows default-encoding issues)
- Use `pathlib.Path`; never hardcode home-directory paths — take them from config or CLI arguments
- Stream large JSON/JSONL inputs where practical
- Preserve original timestamps and be explicit about time zones (convert only for display)
- Source conversations may contain personal data or secrets: never put real conversations in test fixtures, logs, or commits

## Environment

- OS: Windows (PowerShell). Watch for path-separator and encoding differences
- IDE: IntelliJ/PyCharm (`.idea/`) — do not commit personal settings such as `.idea/workspace.xml`
- License: LGPL-3.0
