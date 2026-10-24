# TKN — Gap Analysis (current state vs TKN 1.0 briefing)

Last updated: 2026-10-24, after PR #2 (`a1ff334`). First version: 2026-10-24 at `ff16d70`.

Sources compared: `TKN_Requirements.md` (R), `TKN_Harness_Architecture.md` (H), `CLAUDE.md` (C), against `CURRENT_STATE.md`.
Priority: **P0** blocks safe progress · **P1** next foundation · **P2** Harness MVP · **P3** later 1.0 · **Out** not in 1.0.
Status: **Done** · **Partial** · **Open**.

| # | Requirement | Source | Current | Remaining gap | Priority | Status |
|---|---|---|---|---|---|---|
| G1 | Preserve originals separately, never overwrite | R principle, C | Claude (86) and Claude Code (5) imported into `01_Original` via `tkn import`; raw notes unchanged by every later step (hash-checked) | Import ChatGPT and Codex | P1 | Partial |
| G2 | Single import path into the vault | C | `tkn import` is the only path to the vault; `copy_notes_to_vault.py` kept local and unused; `output/claude` notes never copied | — | — | Done |
| G3 | Repository docs consistent | — | README merged; briefing and planning docs committed under `docs/` | Keep docs updated with each PR | — | Done |
| G4 | Import all four tools with provenance and timestamps | R functional | 4 parsers; 2 verified on real data | Real ChatGPT export and Codex sessions; no source-file reference or content hash in frontmatter | P1 | Partial |
| G5 | Idempotent ingestion with content hashes | H controls | `(source, id)` only | Add `content_hash`; report changed sources (no overwrite) | P1 | Open |
| G6 | Classify by technical topic, topic-oriented linked notes | R, H step 2, C | 15 topic notes, keyword classification (English + Korean), 172 links, title overrides | Tests; removing links when a suggestion is dropped; precision review; move scripts into the `tkn` CLI | P1 | Partial |
| G7 | Separate raw from derived (summaries, decisions, requirements) with human review | R | Derived data lives only in `02_Knowledge` (topic notes, title overrides); owner corrections via the review file and overrides | Summaries, decisions and requirements notes | P2 | Partial |
| G8 | Extract decisions / open questions / requirements | H step 2 | Missing | Extraction step (manual-first; external LLMs only with approval, Q10) | P2 | Open |
| G9 | English developer briefs with acceptance criteria | R, H step 3 | Missing | Task-brief template + generator | P2 | Open |
| G10 | Task queue + state machine with persisted state and audit trail | H steps 4, controls | Missing | State file per task, append-only audit log, resumable | P2 | Open |
| G11 | QA run + human gates 1/2/3 | H steps 5–9 | Missing | Gate records; QA evidence capture | P2 | Open |
| G12 | Automated Git commit after the three gates (first automation priority) | H | Missing | Dry-run commit, staged-diff review, test repo first | P2 | Open |
| G13 | Deployment + smoke checks | H step 8 | Missing; target undefined | Define what "deploy" means for TKN (Q4) | P2 / P3 | Open |
| G14 | Write validated outcomes back to TKN/Obsidian | R, H step 11 | Missing | Outcome note linking task, sources, commit/PR, tests | P2 | Open |
| G15 | Privacy filtering before publication; secrets out of notes/logs | R, H controls | Review file gitignored; committed files scanned by hand before PR #2 | Automated secret/privacy scan (import time and pre-commit) | P1 | Partial |
| G16 | CI | — | Missing | GitHub Actions running pytest on PRs | P1 | Open |
| G17 | Mobile / asynchronous capture and review | H | Missing | Undecided (Q8) | P3 | Open |
| G18 | Public platform `tkn.tonabit.com` | R pillar 2 | Missing; no stack | Owner decisions (Q9) | P3 | Open |
| G19 | Updating changed notes / versioned derived notes | C, H | Missing; a note imported from a still-active session stays frozen | Version field + change report; re-import policy (Q14) | P3 | Open |
| G20 | Tests for the topic scripts | — | None; verified manually on the real vault | Unit tests with synthetic fixtures | P1 | Open |
| — | Blockchain, points, paid membership, QuroERP | R out of scope | — | — | Out | — |

## Key observations

1. **Phase 0 is mostly done.** Real Claude and Claude Code data is in the vault in the canonical format, and the docs are consistent. ChatGPT and Codex remain.
2. **Classification moved ahead of the v0.2 foundation.** It works on real data but is untested and lives in `scripts/`. Before building on it, it needs tests and a home in the `tkn` package (G6, G20).
3. **Harness still does not exist.** Everything in H remains a target workflow (G8–G14).
4. **Privacy controls are manual.** Pre-push scanning was done by hand for PR #2. An automated check (G15) would make this repeatable.
5. **Platform (pillar 2) stays a separate track** and should not block pillar 1.
