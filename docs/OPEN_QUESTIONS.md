# TKN — Open Questions for the Owner

Each question blocks or shapes a phase in `IMPLEMENTATION_PLAN.md`. Proposed defaults are proposals, not decisions.

| # | Question | Blocks | Proposed default |
|---|---|---|---|
| Q1 | Is `<vault>` the `StableYoung-Knowledge` vault? No folder with that name was found. | Phase 0 | Treat `<vault>` as the vault until told otherwise |
| Q2 | Use `tkn import` (canonical `id`, `YYYY-MM` folders) for the vault and drop `scripts/copy_notes_to_vault.py` / the `output/claude` notes? | Phase 0 | Yes; keep helper scripts for inspection only |
| Q3 | Harness location: `harness/` inside this repo, or a separate repository? | Phase 3 | Inside this repo until the interfaces settle |
| Q4 | What does "deployment" mean for TKN 1.0 pillar 1: local `pip install`, writing to the vault, a release tag, or a server? | Phase 3 gate 2, Phase 5 | Local install + vault write as the "local deployment" target |
| Q5 | The architecture puts the automated commit **after** deployment and gate 3. Should the commit come before deployment (needed for Git-based deploys), with gate 3 then approving push/PR? | Phase 3 | Commit locally after gate 1; push/PR after gate 3 |
| Q6 | May classification add tags/fields to raw notes in `01_Original`, or must all derived data live in `02_Knowledge`? | Phase 2 | Raw notes untouched; derived data in `02_Knowledge` |
| Q7 | Branch policy for automated commits: feature branch per task + PR into `main` (fits the current ruleset)? | Phase 3 | Yes |
| Q8 | How should mobile review/approval work: Obsidian mobile editing a gate field, GitHub PR on phone, or something else? | Phase 5 | Approve by editing a frontmatter field in the task note, synced via the vault's cloud sync |
| Q9 | Platform `tkn.tonabit.com`: authentication provider, hosting, data model, search engine, moderation rules, release date. | Phase 6 | Undecided; separate design doc |
| Q10 | May LLM APIs be used for extraction/classification on private conversations? If yes, which provider and what data may leave the machine? | Phases 2, 4 | Manual/rule-based first; no external API without approval |
| Q11 | Should the briefing documents themselves be committed (under `docs/`)? They contain no personal data. | Phase 0 | Yes, after README restore |
