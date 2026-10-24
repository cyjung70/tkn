# TKN — Gap Analysis (current state vs TKN 1.0 briefing)

Sources compared: `TKN_Requirements.md` (R), `TKN_Harness_Architecture.md` (H), `CLAUDE.md` (C), against `CURRENT_STATE.md`.
Priority: **P0** blocks safe progress · **P1** next foundation · **P2** Harness MVP · **P3** later 1.0 · **Out** not in 1.0.

| # | Requirement | Source | Current | Gap | Priority |
|---|---|---|---|---|---|
| G1 | Preserve originals separately, never overwrite | R principle, C | Implemented (`VaultWriter`) | Real data not yet in the vault; helper-script notes (`uuid`) bypass dedup | P0 |
| G2 | Single import path into the vault | C | `tkn import` exists; parallel path via `scripts/claude_to_notes.py` + `copy_notes_to_vault.py` | Two formats for the same data → duplicate risk | P0 |
| G3 | Repository docs consistent | — | README replaced by briefing README | Restore README; place briefing docs under `docs/` | P0 |
| G4 | Import all four tools with provenance and timestamps | R functional | Implemented for 4 tools | Real ChatGPT export unverified; no source-file reference or content hash in frontmatter | P1 |
| G5 | Idempotent ingestion with content hashes | H controls | `(source, id)` only | Add `content_hash`; detect changed sources (report, not overwrite) | P1 |
| G6 | Classify by technical topic, topic-oriented linked notes | R, H step 2, C | Missing | Topic model, tagging, `Topics/` index notes in `02_Knowledge` | P1 |
| G7 | Separate raw from derived (summaries, decisions, requirements) with human review | R | Folder split exists (`01_Original` / `02_Knowledge`); nothing derived | Derived-note schema with links to `(source, id)`, review status | P1 |
| G8 | Extract decisions / open questions / requirements | H step 2 | Missing | Extraction step (manual-first, LLM-assisted later) | P2 |
| G9 | English developer briefs with acceptance criteria | R, H step 3 | Missing (this document set was written by hand) | Task-brief template + generator | P2 |
| G10 | Task queue + state machine with persisted state and audit trail | H steps 4, controls | Missing | State file per task, append-only audit log, resumable | P2 |
| G11 | QA run + human gates 1/2/3 | H steps 5–9 | Missing | Gate records; QA evidence capture | P2 |
| G12 | Automated Git commit after the three gates (first automation priority) | H | Missing | Dry-run commit, staged-diff review, test repo first | P2 |
| G13 | Deployment + smoke checks | H step 8 | Missing; target undefined | Define what "deploy" means for TKN (see Q4) | P2 (definition) / P3 (automation) |
| G14 | Write validated outcomes back to TKN/Obsidian | R, H step 11 | Missing | Outcome note linking task, sources, commit/PR, tests | P2 |
| G15 | Privacy filtering before publication; secrets out of notes/logs | R, H controls | Partial (tool output never written; `.gitignore`) | Secret scanner before any derived/public note | P1 (scanner) / P3 (publish) |
| G16 | CI | — | Missing | GitHub Actions running pytest on PRs | P1 |
| G17 | Mobile / asynchronous capture and review | H | Missing | Probably Obsidian mobile on the synced vault; undecided | P3 |
| G18 | Public platform `tkn.tonabit.com` (publishing, search, membership, comments, moderation) | R pillar 2 | Missing; no stack | Needs owner decisions (auth, hosting, data model, search) | P3 |
| G19 | Updating changed notes / versioned derived notes | C, H | Missing | Version field + change report; never edit raw notes in place | P3 |
| — | Blockchain, points, paid membership, QuroERP | R out of scope | — | — | Out |

## Key observations

1. **The v0.1 core is solid and tested** (18 tests); the gaps are almost all downstream of import.
2. **Harness does not exist yet.** Everything in H is a target workflow. The first Harness work should be file-based state and gate records, not deployment automation.
3. **The fastest real-world value is getting real data into the vault correctly** (G1, G2): `tkn import claude raw/claude/conversations.json` already produces the canonical format. The copy script would place a second, incompatible format into the same folder.
4. **Platform (pillar 2) is a separate product** with open stack decisions; it should not block pillar 1.
