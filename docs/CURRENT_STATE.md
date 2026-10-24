# TKN — Current State Inventory

Inspected: 2026-10-24, branch `main` at `ff16d70` plus uncommitted working-tree files.
Scope: TKN 1.0 and its Harness only (QuroERP excluded).

Status legend:
- **Implemented**: code exists and an automated test covers it
- **Partial**: code exists but is incomplete, diverges from conventions, or is untested
- **Missing**: no code found
- **Unverified**: claimed somewhere, or plausible, but not demonstrated in this inspection

## 1. Repository layout

| Path | Role | Tracked |
|---|---|---|
| `tkn/` | Python package (CLI, importers, vault writer) | yes |
| `tests/` | pytest suite with synthetic fixtures | yes |
| `scripts/claude_stats.py`, `scripts/claude_to_notes.py` | Claude export helper scripts | yes |
| `scripts/copy_notes_to_vault.py` | Copy `output/claude/*.md` into the vault | **no (untracked)** |
| `CLAUDE.md` | Project conventions for Claude Code | yes |
| `README.md` | **Locally replaced** by the briefing-package README (see §6) | modified |
| `README_OLD10.md` | Copy of the original project README | no |
| `TKN_Requirements.md`, `TKN_Harness_Architecture.md`, `Claude_Code_Instructions.md` | Briefing documents (planning only) | no |
| `tkn.example.toml` / `tkn.toml` | Config template / local config (gitignored) | template only |
| `raw/`, `output/` | Local exports and generated notes (gitignored, personal data) | no |

No `.github/`, CI config, Dockerfile, deployment config, or Harness directory exists.

## 2. Feature inventory

### Import pipeline (v0.1)

| Feature | Status | Evidence |
|---|---|---|
| ChatGPT import (ZIP or JSON, `current_node` main path, tool calls) | Implemented | `tkn/importers/chatgpt.py`; `test_chatgpt_follows_current_branch`, `test_chatgpt_reads_from_zip` |
| Claude (claude.ai) import | Implemented | `tkn/importers/claude.py`; `test_claude_blocks_and_fallback_title` |
| Claude Code import (skip sidechain/meta/subagents/thinking/tool output) | Implemented | `tkn/importers/claude_code.py`; `test_claude_code_session`, `test_private_content_is_not_written` |
| Codex import (`response_item` only, unwrap delegation) | Implemented | `tkn/importers/codex.py`; `test_codex_session`, `test_private_content_is_not_written` |
| Common model (`Conversation`, `Message`) | Implemented | `tkn/models.py` |
| Malformed records logged and skipped | Implemented | `tkn/importers/*` (`log.warning`), CLI counts them (`tkn/cli.py` `_WarningCounter`) |

### Vault output

| Feature | Status | Evidence |
|---|---|---|
| Note path `<vault>/<root>/<Tool>/<YYYY-MM>/<date>_<title>.md`, time-zone aware | Implemented | `tkn/vault/naming.py`; `test_note_path_uses_local_month` |
| Title sanitizing, Windows reserved names | Implemented | `test_sanitize_title` |
| JSON-quoted frontmatter (`source`, `id`, `title`, `created`, `updated`, `project`) | Implemented | `tkn/vault/render.py`; `test_render_and_read_back_key` |
| Dedup by `(source, id)` scanned from vault frontmatter | Implemented | `tkn/vault/writer.py` `VaultWriter.__post_init__`; `test_writer_skips_existing_and_resolves_collisions`, `test_import_is_idempotent` (×4 sources) |
| Never overwrite user edits; atomic write via temp file | Implemented | `test_writer_never_overwrites_user_edits` |
| Dry run | Implemented | `test_dry_run_writes_nothing` |
| `--since` filter, `-v` listing | Implemented, untested | `tkn/cli.py`; no test asserts filtering |
| Config loading (`tkn.toml`) | Implemented, lightly tested | `tkn/config.py`; `test_missing_config_returns_error` |

Test run in this inspection: `.venv\Scripts\python -m pytest` → **18 passed**.

### Helper scripts (added 2026-10-24)

| Script | Status | Notes |
|---|---|---|
| `scripts/claude_stats.py` | Partial (no tests) | Count + oldest/newest `created_at`; verified on the real export (86 conversations) |
| `scripts/claude_to_notes.py` | Partial (no tests, diverges) | Writes `output/claude/*.md` with `uuid` instead of `id`, flat folder, no `YYYY-MM` subfolder. These notes are **not recognized** by `VaultWriter` dedup |
| `scripts/copy_notes_to_vault.py` | Partial (untracked, no tests) | Only `--dry-run` executed (86 files would be copied); no real copy has happened |

### Planned features with no code

| Feature (source document) | Status |
|---|---|
| Topic classification, `Topics/<topic>.md` index notes (CLAUDE.md §Behavior 4) | Missing |
| Updating notes whose source changed; versioned derived notes | Missing |
| Content hashes for idempotent ingestion (Harness §Engineering controls) | Missing; dedup uses `(source, id)` only |
| Extraction of decisions / questions / requirements (Harness pipeline step 2) | Missing |
| English task-brief generation with acceptance criteria (step 3) | Missing |
| Task queue and state machine `drafted → … → knowledge-synced` | Missing |
| Persisted run state and audit trail | Missing |
| QA runner, three human approval gates, deployment, smoke checks | Missing |
| Automated Git commit after approvals | Missing (target workflow only) |
| Write-back of Harness outcomes to the vault | Missing |
| Privacy filtering before publication | Missing (import-time skipping of tool output exists, but no secret scanning) |
| Public platform `tkn.tonabit.com` (blog, search, membership, comments, moderation) | Missing; no web code, stack undecided |
| CI/CD | Missing |

## 3. Obsidian integration

- Vault found at `<vault>` (cloud-synced folder, contains `.obsidian/`), with `01_Original/{ChatGPT,Claude,ClaudeCode,Codex}` and `02_Knowledge/`. **All five folders are currently empty.**
- No folder named `StableYoung-Knowledge` was found under the vault's parent folder (depth 3). Whether `<vault>` *is* that vault is unconfirmed (see OPEN_QUESTIONS Q1).
- Local `tkn.toml` points to that vault (`root_folder = "01_Original"`, `claude_code = "ClaudeCode"`), so `tkn import` would write the canonical layout there. This has not been run.

## 4. Git and repository controls

- Remote `github.com/cyjung70/tkn`; only branch `main`. PR #1 squash-merged on 2026-10-24.
- Ruleset `tkn_rule` (ID 25699848) on the default branch: no deletion, no force push, no creation, linear history, PR required (0 approvals). No bypass actors.
- Claude Code auto-mode classifier blocked two actions in this session (ruleset edit, PR merge) and required the owner to run them. Any Harness automation must expect this boundary.

## 5. Verification gaps (unverified)

- Real ChatGPT export: never imported in this session (PR #1 test plan item open).
- `tkn import claude` on the real export: not run; only the helper scripts were.
- Claude Code / Codex smoke test on real logs: reported in PR #1, not re-verified here.
- Writing to a cloud-synced folder (sync conflicts, long paths): untested.

## 6. Working-tree anomalies to resolve before further work

1. `README.md` was overwritten with the briefing README; the original is in `README_OLD10.md`. `pyproject.toml` uses `README.md` as the package readme.
2. Briefing documents and `scripts/copy_notes_to_vault.py` are untracked.
