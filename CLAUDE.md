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
| ChatGPT | `conversations.json` from the Settings → Data export ZIP | JSON. Messages are stored as a `mapping` tree (each node has `parent`/`children`); walk back from `current_node` to recover the main conversation path |
| Claude (claude.ai) | `conversations.json` from the Settings → Export data ZIP | JSON. Per-conversation `chat_messages` array (`sender`: `human`/`assistant`) |
| Codex (CLI) | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | JSONL, one event per line |
| Claude Code | `~/.claude/projects/<encoded-path>/<session-id>.jsonl` | JSONL, one message/event per line, linked via `parentUuid` |

> These formats can change between versions. When writing or updating a parser, check against real sample files, ignore unknown fields, and handle missing fields defensively instead of crashing.

## Status

Early stage. There is no source code, dependency setup, or test suite yet. The structure and conventions below are **proposals**; update this file once they are actually implemented.

## Intended Behavior

1. **Import**: read each tool's export files / session logs and convert them into a common internal model (`Conversation`, `Message`)
2. **Export**: write Markdown notes into per-tool folders in the vault
3. **Classify**: assign topics based on conversation content and link them via tags, frontmatter, and topic index notes
4. **Incremental sync**: identify already-imported conversations by ID, never create duplicates, and only update notes whose source changed

## Proposed Structure

```
tkn/
  models.py          # Common data models (dataclasses): Conversation, Message, ...
  importers/         # Per-tool parsers: chatgpt.py, claude.py, codex.py, claude_code.py
  vault/             # Obsidian note rendering and file writing
  classify/          # Topic classification logic
  cli.py             # Command-line entry point
tests/
  fixtures/          # Minimal per-tool samples (anonymized only, never real conversations)
```

To add a new tool, add one parser under `importers/` that returns only the common model, so the export and classify stages stay tool-agnostic.

## Obsidian Vault Conventions (proposed)

- Path: `<vault>/<tool>/<YYYY-MM-DD> <title>.md` (e.g. `ChatGPT/`, `Claude/`, `Codex/`, `Claude Code/`)
- Strip or replace characters forbidden in Windows/Obsidian file names (`\ / : * ? " < > | # ^ [ ]`) and cap the length
- Example YAML frontmatter:
  ```yaml
  ---
  source: chatgpt
  conversation_id: <original ID>
  title: ...
  created: 2026-10-23T08:50:00+09:00
  updated: ...
  topics: [python, obsidian]
  tags: [tkn/chatgpt, topic/python]
  ---
  ```
- `conversation_id` is the deduplication key. File names may change, so never use them to identify a conversation.
- Never overwrite content the user edited in the vault (e.g. separate generated and user-owned sections, or confirm before overwriting).
- Topic classification links notes to `Topics/<topic>.md` index notes via `[[wikilinks]]`.

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
