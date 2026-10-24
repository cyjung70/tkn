# TKN — Incremental Implementation Plan

Last updated: 2026-10-24, after PR #2 (`a1ff334`).
Status: **Proposal.** Each phase starts only after the owner approves it. Work already done was approved step by step during the 2026-10-24 session.
Strategy (from R): TKN → Harness → improved TKN → improved Harness → TKN 1.0. Small phases, reuse v0.1, no breaking changes to existing vault notes.

## Phase overview

| Phase | Goal | Depends on | Gaps | Status |
|---|---|---|---|---|
| 0 | Clean working tree, real data into the vault | — | G1, G2, G3 | Mostly done (ChatGPT, Codex left) |
| 1 | v0.2 foundation: tests and CI, provenance, hashes, secret scan | 0 | G4, G5, G15, G16, G20 | Open — **recommended next** |
| 2 | v0.3 classification + derived notes (manual-first) | 1 | G6, G7 | Partly done ahead of Phase 1 (scripts) |
| 3 | Harness MVP: task briefs, state machine, gates, dry-run commit | 1 (2 optional) | G9–G12 | Open |
| 4 | Knowledge write-back | 3 | G14, G8 | Open |
| 5 | Deployment definition + smoke checks; mobile review | 3, owner decisions | G13, G17 | Open |
| 6 | Public platform (separate design track) | owner decisions | G18 | Open |

## Phase 0 — import real data

Done:
- README merged; briefing and planning docs in `docs/` (PR #2).
- `scripts/copy_notes_to_vault.py` not used for the vault (Q2); kept local.
- `tkn import claude`: dry run `created 86`, real run `created 86`, re-run `created 0, skipped (exists) 86`.
- `tkn import claude-code`: `created 5`, re-run `created 0, skipped (exists) 5`.
- No sync-conflict copies or leftover temp files.

Remaining:
1. `tkn import codex --dry-run`, review, real run, re-run.
2. `tkn import chatgpt <export.zip> --dry-run` when an export is available, then the same steps.

Acceptance tests: each re-run reports `created 0`; `01_Original` of other tools unchanged; no personal data in `git status`.

## Phase 1 — v0.2 foundation (recommended next)

Smallest useful iteration, in this order:
1. **Tests for the topic scripts** using synthetic fixtures under `tests/fixtures/` (no real notes): term derivation, Korean substring matching, `(N+)` minimums, review parsing, link appending, alias override, hand-edited alias kept, idempotent re-runs.
2. **CI**: GitHub Actions running pytest on Windows and Linux for PRs (fits the `main` PR rule).
3. **Move the topic scripts into the package** as `tkn topics init|classify|link` (Q13), keeping the current behaviour and file formats.
4. Add `content_hash` (SHA-256 of normalized messages) and `source_file` (relative, no home paths) to frontmatter for **new** notes; `tkn import --report-changed` reports differences without overwriting.
5. Automated privacy check: a secret/PII scan at import (logged by `(source, id)`, never printing the match) and a pre-PR scan for vault paths, conversation ids and titles in committed files.

Acceptance tests: all existing tests still pass; new tests cover every script behaviour listed above; CI is green on a PR; old notes without `content_hash` still dedup; a modified fixture is reported as changed and its note is untouched.

## Phase 2 — v0.3 classification and derived notes

Done (scripts, manual verification only):
- 14 approved topics + `Unclassified` in `docs/TOPICS_PROPOSAL.md`, English and Korean keywords.
- `02_Knowledge/Topics/<topic>.md` index notes; links appended under `## Notes` from the review file.
- `02_Knowledge/Title-Overrides.md` for misleading conversation titles.
- Raw notes untouched (Q6 decided).

Remaining:
- Remove or flag links whose suggestion was dropped (Q12) instead of one-off cleanup.
- Precision review on a labelled sample; tune keywords.
- Derived notes for summaries, decisions and requirements (G7, G8).

Acceptance tests: classification and linking are idempotent; raw note bytes unchanged (hash check); owner edits in topic notes preserved.

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

Automated-commit rule (proposed): commit only after `approved-3`, on a feature branch, with the task id in the message; never push, merge, or change repository rules automatically. Pushing and PR creation stay owner-triggered until explicitly authorized.

Observed in practice (2026-10-24): every change went through dry run → owner approval → apply → re-run check. Commits, pushes and PRs were made only on explicit owner request, on a feature branch, with a pre-push privacy scan. Claude Code auto mode blocked a ruleset edit and the PR #1 merge; the PR #2 merge went through on an explicit owner request. A Harness must treat merges and rule changes as owner actions.

Ambiguity to resolve first: H orders commit **after** deployment, but a Git-based deployment normally needs the commit **before** it. See Q5.

## Risks

- Writing personal data to the wrong place (repo, logs): keep `.gitignore` rules, never log message text, scan before every PR.
- Private-repository details leaking into this public repo: describe other repositories only at the level of technologies (as done in `TOPICS_PROPOSAL.md`).
- Format drift in exports: defensive parsers already; add fixtures when real formats change.
- Untested scripts operating on the real vault: mitigated by dry runs and hash checks so far; Phase 1 adds tests.
- Scope creep into the platform before pillar 1 works.
