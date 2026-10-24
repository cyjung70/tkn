# TKN — Current State Inventory

Last updated: 2026-10-24, branch `main` at `a1ff334` (PR #2 merged).
First inspection: 2026-10-24 at `ff16d70`.
Scope: TKN 1.0 and its Harness only (QuroERP excluded).

Status legend:
- **Implemented**: code exists and an automated test covers it
- **Partial**: code exists and has been run on real data, but is incomplete, diverges from conventions, or is untested
- **Missing**: no code found
- **Unverified**: claimed somewhere, or plausible, but not demonstrated

Vault paths are written as `<vault>`.

## 1. Repository layout

| Path | Role | Tracked |
|---|---|---|
| `tkn/` | Python package (CLI, importers, vault writer) | yes |
| `tests/` | pytest suite with synthetic fixtures | yes |
| `scripts/claude_stats.py`, `scripts/claude_to_notes.py` | Claude export helper scripts | yes |
| `scripts/create_topic_notes.py`, `scripts/classify_notes.py`, `scripts/link_topic_notes.py` | Topic notes, keyword classification, topic links | yes (PR #2) |
| `scripts/copy_notes_to_vault.py` | Copy `output/claude/*.md` into the vault; superseded by `tkn import` | **no (local only, by decision)** |
| `docs/` | Briefing, this inventory, gap analysis, plan, open questions, topic proposal, previous README | yes (PR #2) |
| `docs/CLASSIFICATION_REVIEW.md` | Generated review of topic suggestions; lists real note titles | **no (gitignored)** |
| `README.md` | Merged project README (slogan, setup, usage, structure, roadmap) | yes |
| `CLAUDE.md` | Project conventions for Claude Code | yes |
| `tkn.example.toml` / `tkn.toml` | Config template / local config pointing at `<vault>` | template only |
| `raw/`, `output/` | Local exports and generated notes (personal data) | no (gitignored) |

No `.github/`, CI config, deployment config, or Harness directory exists.

## 2. Feature inventory

### Import pipeline (v0.1)

| Feature | Status | Evidence |
|---|---|---|
| ChatGPT import (ZIP or JSON, `current_node` main path, tool calls) | Implemented; **not run on real data** | `tkn/importers/chatgpt.py`; `test_chatgpt_follows_current_branch`, `test_chatgpt_reads_from_zip` |
| Claude (claude.ai) import | Implemented; **run on real data** | `tkn/importers/claude.py`; `test_claude_blocks_and_fallback_title`; 86 conversations imported, re-run created 0 |
| Claude Code import | Implemented; **run on real data** | `tkn/importers/claude_code.py`; `test_claude_code_session`, `test_private_content_is_not_written`; 5 sessions imported (2 projects), re-run created 0 |
| Codex import | Implemented; **not run on real data** | `tkn/importers/codex.py`; `test_codex_session` |
| Common model, malformed records logged and skipped | Implemented | `tkn/models.py`; `tkn/cli.py` `_WarningCounter`; 0 malformed records in the real Claude and Claude Code runs |

### Vault output

| Feature | Status | Evidence |
|---|---|---|
| Note path `<vault>/<root>/<Tool>/<YYYY-MM>/<date>_<title>.md`, time-zone aware | Implemented | `tkn/vault/naming.py`; `test_note_path_uses_local_month` |
| Title sanitizing, collision suffix ` (<id prefix>)` | Implemented | `test_sanitize_title`; 2 real collisions resolved in the Claude import |
| JSON-quoted frontmatter (`source`, `id`, `title`, `created`, `updated`, `project`) | Implemented | `tkn/vault/render.py`; `test_render_and_read_back_key` |
| Dedup by `(source, id)`, never overwrite user edits, atomic writes | Implemented | `tkn/vault/writer.py`; `test_writer_*`, `test_import_is_idempotent` |
| Dry run | Implemented | `test_dry_run_writes_nothing` |
| `--since` filter, `-v` listing | Implemented, untested | `tkn/cli.py` |
| Updating notes whose source changed | Missing | An imported note is frozen; a session imported while still active (one Claude Code session) keeps only its content up to the import |

Test run: `.venv\Scripts\python -m pytest` → **18 passed**.

### Topic classification (added 2026-10-24)

| Feature | Status | Evidence |
|---|---|---|
| Approved topic list (14 topics + `Unclassified`) with English and Korean keywords | Implemented (document) | `docs/TOPICS_PROPOSAL.md` |
| Topic index notes in `02_Knowledge/Topics` (`type: "topic"`, description, keywords, `## Notes`) | Partial (no tests) | `scripts/create_topic_notes.py`; 15 notes created, re-run skipped all |
| Keyword classification into a review file | Partial (no tests) | `scripts/classify_notes.py`; 91 notes classified, 30 unclassified; per-term minimum counts (`보안 (3+)`), Korean substring matching |
| Links from topic notes to raw notes | Partial (no tests) | `scripts/link_topic_notes.py`; 172 links; re-run adds nothing |
| Display-title overrides for misleading titles | Partial (no tests) | `<vault>/02_Knowledge/Title-Overrides.md` (10 entries); 42 link texts renamed; hand-edited link texts are kept |
| Removing links when a suggestion is dropped | Missing | `link_topic_notes.py` only adds; 3 stale links were removed once by a one-off script |
| Classification quality | Known limits | Keyword matching only, no external API. Generic terms still produce some false positives (e.g. a greeting conversation under Security-and-Privacy); some technical notes fall outside all 14 topics (MQL4, Rust, Nginx) |

### Helper scripts

| Script | Status | Notes |
|---|---|---|
| `scripts/claude_stats.py` | Partial (no tests) | Count + oldest/newest `created_at`; verified on the real export |
| `scripts/claude_to_notes.py` | Partial (no tests, diverges) | Writes `output/claude/*.md` (86 notes, local) with `uuid` instead of `id`; not used for the vault |

### Planned features with no code

| Feature (source document) | Status |
|---|---|
| Content hashes, change reports for re-exported sources (Harness §Engineering controls) | Missing |
| Extraction of decisions / questions / requirements (Harness pipeline step 2) | Missing |
| English task-brief generation with acceptance criteria (step 3) | Missing |
| Task queue, state machine, persisted state and audit trail | Missing |
| QA runner, three human approval gates, deployment, smoke checks | Missing |
| Automated Git commit after approvals | Missing (target workflow only) |
| Write-back of Harness outcomes to the vault | Missing |
| Secret scanning / privacy filtering before publication | Missing |
| Public platform `tkn.tonabit.com` | Missing; stack undecided |
| CI/CD | Missing |

## 3. Obsidian integration

| Vault folder | Contents |
|---|---|
| `01_Original/Claude` | 86 notes in 8 month folders (2024-06 … 2026-10) |
| `01_Original/ClaudeCode` | 5 notes (4 from this repository, 1 from another project) |
| `01_Original/ChatGPT`, `01_Original/Codex` | empty (not imported yet) |
| `02_Knowledge/Topics` | 15 topic notes with 172 links |
| `02_Knowledge/Title-Overrides.md` | 10 display-title overrides |

- Raw notes in `01_Original` were never modified after import; hashes were compared before and after every topic step.
- No sync-conflict copies or leftover `.tmp` files were found after the imports and topic steps.
- Whether `<vault>` is the `StableYoung-Knowledge` vault is still unconfirmed (OPEN_QUESTIONS Q1).

## 4. Git and repository controls

- Remote `github.com/cyjung70/tkn` (public); only branch `main`. PR #1 and PR #2 squash-merged on 2026-10-24.
- Ruleset `tkn_rule` (ID 25699848), default branch only: no deletion, no force push, no creation, linear history, pull request required (0 approvals; merge, squash and rebase allowed, but linear history rules out merge commits). No bypass actors.
- Claude Code auto mode blocked a ruleset edit and the PR #1 merge; the owner ran those. The PR #2 merge, requested explicitly by the owner, went through.
- Before pushing PR #2, committed files were scanned for vault paths, private-repository details, conversation titles and ids (0 hits).

## 5. Verification gaps (unverified)

- Real ChatGPT export and Codex sessions: not imported yet.
- Classification precision: reviewed by spot checks only; no labelled sample.
- Topic scripts: no automated tests.

## 6. Open items in the working tree

- `scripts/copy_notes_to_vault.py` is untracked and kept local by decision.
- `GAP_ANALYSIS.md`, `IMPLEMENTATION_PLAN.md` and `OPEN_QUESTIONS.md` still describe the state of the first inspection (for example, Phase 0 and G6 are now partly done).
