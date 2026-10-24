# TKN — Open Questions for the Owner

Last updated: 2026-10-24, after PR #2.

Each question blocks or shapes a phase in `IMPLEMENTATION_PLAN.md`. Proposed defaults are proposals, not decisions.

## Open

| # | Question | Blocks | Proposed default |
|---|---|---|---|
| Q1 | Is `<vault>` the `StableYoung-Knowledge` vault? No folder with that name was found. | Phase 4 write-back | Treat `<vault>` as the vault until told otherwise (current practice) |
| Q3 | Harness location: `harness/` inside this repo, or a separate repository? | Phase 3 | Inside this repo until the interfaces settle |
| Q4 | What does "deployment" mean for TKN 1.0 pillar 1: local `pip install`, writing to the vault, a release tag, or a server? | Phase 3 gate 2, Phase 5 | Local install + vault write as the "local deployment" target |
| Q5 | The architecture puts the automated commit **after** deployment and gate 3. Should the commit come before deployment (needed for Git-based deploys), with gate 3 then approving push/PR? | Phase 3 | Commit locally after gate 1; push/PR after gate 3 |
| Q7 | Branch policy for automated commits: feature branch per task + PR into `main` (fits the current ruleset)? | Phase 3 | Yes (current practice for PR #1 and #2) |
| Q8 | How should mobile review/approval work: Obsidian mobile editing a gate field, GitHub PR on phone, or something else? | Phase 5 | Approve by editing a frontmatter field in the task note, synced via the vault's cloud sync |
| Q9 | Platform `tkn.tonabit.com`: authentication provider, hosting, data model, search engine, moderation rules, release date. | Phase 6 | Undecided; separate design doc |
| Q10 | May LLM APIs be used for extraction on private conversations? If yes, which provider and what data may leave the machine? | Phases 2, 4 | Manual/rule-based first; no external API without approval (classification so far used none) |
| Q12 | When a note's suggested topics change, should `link_topic_notes.py` remove the old links automatically, only report them, or leave them? | Phase 2 | Report by default; remove with an explicit flag, and only links still in the generated format |
| Q13 | Move the topic scripts into the package as `tkn topics init|classify|link`? | Phase 1 | Yes, same behaviour and file formats |
| Q14 | A note imported while its session was still active stays frozen. Re-import such notes by deleting and importing again, or wait for change detection (G5/G19)? | Phase 1 | Wait for change detection; do not delete raw notes by hand |
| Q15 | Should `Title-Overrides.md` also cover ChatGPT and Codex notes once imported, and should overrides be suggested automatically for greeting-style titles? | Phase 2 | Yes for coverage; suggestions as a review list, applied only after approval |

## Decided

| # | Question | Decision (2026-10-24) |
|---|---|---|
| Q2 | Use `tkn import` for the vault and drop `copy_notes_to_vault.py` / the `output/claude` notes? | Yes. `tkn import` only; the copy script stays local and unused |
| Q6 | May classification change raw notes in `01_Original`? | No. Raw notes are never modified; topics, links and title overrides live in `02_Knowledge` |
| Q11 | Commit the briefing documents under `docs/`? | Yes (PR #2) |
| — | Topic list and naming | All 14 proposed topics plus `Unclassified`, English hyphenated names, no numbers |
| — | Keyword language | English and Korean keywords; English `production` means the production environment, ERP manufacturing uses `manufacturing` / `manufacture` |
| — | Misleading conversation titles | Fixed by display-title overrides in `02_Knowledge/Title-Overrides.md`, with the date prefix; originals untouched |
| — | Private repositories | Described in this public repo only at the level of technologies; local vault paths written as `<vault>` |
