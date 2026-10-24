# TKN — Incremental Implementation Plan (proposal, awaiting owner review)

Status: **Proposal.** Nothing below is approved. Each phase starts only after the owner approves it.
Strategy (from R): TKN → Harness → improved TKN → improved Harness → TKN 1.0. Small phases, reuse v0.1, no breaking changes to existing vault notes.

## Phase overview

| Phase | Goal | Depends on | Gaps |
|---|---|---|---|
| 0 | Clean working tree, real data into the vault | — | G1, G2, G3 |
| 1 | v0.2 foundation: provenance, hashes, CI, secret scan | 0 | G4, G5, G15, G16 |
| 2 | v0.3 classification + derived notes (manual-first) | 1 | G6, G7 |
| 3 | Harness MVP: task briefs, state machine, gates, dry-run commit | 1 (2 optional) | G9–G12 |
| 4 | Knowledge write-back | 3 | G14, G8 |
| 5 | Deployment definition + smoke checks; mobile review | 3, owner decisions | G13, G17 |
| 6 | Public platform (separate design track) | owner decisions | G18 |

## Phase 0 — smallest useful next iteration (recommended)

Tasks:
1. Restore `README.md` from `README_OLD10.md`; move the three briefing docs and these four deliverables to `docs/` (e.g. `docs/briefing/`, `docs/planning/`).
2. Decide the fate of `scripts/copy_notes_to_vault.py`. Recommendation: **do not use it for the vault**; delete or keep it unused, because `tkn import` already writes the canonical format with `id` dedup.
3. Run `tkn import claude raw/claude/conversations.json --dry-run`, review, then run it for real into `<vault>\01_Original\Claude`.
4. Repeat dry run → real run for `claude-code` and `codex` (and `chatgpt` when an export is available).

Acceptance tests:
- `pytest` passes (18 tests, unchanged).
- Dry run reports `created 86` for Claude; the real run creates 86 notes under `Claude/<YYYY-MM>/`.
- A second real run reports `created 0, skipped (exists) 86`.
- `git status` shows no personal data; README renders the project description again.

Risk: cloud sync while writing. Mitigation: atomic temp-file writes already exist; run while sync is idle and check for "conflict" copies afterwards.

## Phase 1 — v0.2 foundation

Tasks:
- Add `content_hash` (SHA-256 of normalized messages) and `source_file` (path relative to the export, no home paths) to frontmatter for **new** notes. Existing notes are read as-is.
- `tkn import --report-changed`: list conversations whose hash differs from the vault note. Report only; no overwrite.
- Secret scanner (regex for keys/tokens) run at import; findings logged by `(source, id)` without printing the secret.
- GitHub Actions: pytest on Windows + Linux for PRs (fits the `main` PR rule).
- Tests for `--since` and the new fields.

Acceptance tests: old fixtures still import; notes without `content_hash` still dedup; a modified fixture is reported as changed and the note is untouched; CI is green on a PR.

## Phase 2 — v0.3 classification and derived notes

- Topic list in config; `tkn classify` writes topic tags to a **sidecar or derived note**, not into raw notes (keeps raw sources untouched; see Q6).
- `02_Knowledge/Topics/<topic>.md` index notes linking raw notes by wikilink.
- Manual-first: rules/keywords + owner correction; LLM assistance optional later behind a flag.

Acceptance tests: classify is idempotent; raw note bytes unchanged (hash check); owner edits in topic notes preserved.

## Phase 3 — Harness MVP

Location: `harness/` package in this repo (CLI `tkn task …`), or a separate repo (Q3).

- Task brief: Markdown + frontmatter in `02_Knowledge/Tasks/<task-id>.md` (English, acceptance criteria, source links).
- State: `tasks/<task-id>/state.json` + append-only `audit.jsonl`; states exactly as in H.
- Transitions are explicit CLI commands; gates recorded as `approved-1/2/3` with approver, timestamp, evidence path.
- QA: run configured commands (pytest), store output as evidence.
- Commit step: `tkn task commit <id> --dry-run` shows the staged diff and the commit message; a real commit is allowed only when all three approvals are recorded. Initially exercised **only on a scratch test repository**. No push.

Acceptance tests: illegal transitions rejected; interrupted run resumes without duplicate actions; commit refused without approvals; dry run writes nothing to Git.

## Phase 4 — knowledge write-back

- On `committed → knowledge-synced`, write `02_Knowledge/Harness/<task-id>.md`: summary, decisions, test evidence, commit SHA / PR URL, links to source conversations via `(source, id)` and wikilinks.
- Never modify `01_Original`.

Acceptance: outcome note links resolve in Obsidian; re-sync is idempotent.

## Phase 5–6

Defined after owner answers Q4 (deployment target), Q8 (mobile), and Q9 (platform stack).

## Human approval gates and the commit rule

| Gate | When | Owner sees | Recorded as |
|---|---|---|---|
| 1 | After QA passes | Diff summary, test output, open risks | `approved-1` |
| 2 | Immediately before deployment (including local) | Deployment plan, target, rollback | `approved-2` |
| 3 | After deployment + smoke checks | Smoke-check results, deployed state | `approved-3` |

Automated-commit rule (proposed): commit only after `approved-3`, on a feature branch, with the task id in the message; never push, merge, or change repository rules automatically. Pushing and PR creation stay owner-triggered until explicitly authorized. This matches the observed Claude Code auto-mode limits (ruleset edits and merges required the owner).

Ambiguity to resolve first: H orders commit **after** deployment, but a Git-based deployment normally needs the commit **before** it. See Q5.

## Risks

- Writing personal data to the wrong place (repo, logs): keep `.gitignore` rules, never log message text.
- Format drift in exports: defensive parsers already; add fixtures when real formats change.
- Scope creep into the platform before pillar 1 works.
