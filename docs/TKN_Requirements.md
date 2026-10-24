# Tonabit Knowledge Nexus (TKN) 1.0 — Product Requirements

Status: Planning brief based on founder discussion, 2026-10-23. This is a target specification, not a claim that features exist.

## Guiding principle
**Separate Sources, Connect Knowledge.** Preserve original ChatGPT, Codex, Claude, and Claude Code records separately with provenance, timestamps, and links. Organize derived knowledge by topic in the existing `StableYoung-Knowledge` Obsidian vault. Never overwrite originals.

## Two pillars of TKN 1.0
1. **Knowledge-to-development pipeline**: import AI conversations, classify and distill actionable requirements, generate reviewed English development specifications for Claude Code / Harness execution, and ingest verified development learnings back into TKN.
2. **Free knowledge-sharing platform** at the proposed `tkn.tonabit.com`: combine blog publishing/search with community membership, discussion, comments and sharing. Support curated insights, educational and philosophical knowledge, including Swedenborg-related material, expressed in accessible language for broad audiences.

## Functional requirements
- Import records from ChatGPT, Codex, Claude and Claude Code; retain tool/source distinction, original content, timestamp, and traceable citations.
- Separate raw conversations from derived summaries, decisions, requirements, and publishable content; allow human review and correction.
- Integrate with Obsidian using linked, topic-oriented Markdown notes and stable source references.
- Generate structured English developer briefs from Korean ideation, preserving scope, decisions, uncertainty and acceptance criteria.
- Publish curated content with authoring, categories/tags, search, comments, sharing, registration, free membership and moderation controls.
- Keep unpublished/private content distinct from public content. Require explicit review before public publishing.
- Capture validated bug fixes, tests and implementation decisions from Harness and link them back to their source and topic.

## Out of scope for 1.0
- Blockchain and point/reward management (future 2.0 / Tonabit Community OS).
- Paid membership or monetization of the public TKN platform in 1.0.
- QuroERP implementation and planning in this brief.

## Delivery strategy
Build a small manual v0.1 import/classification foundation, use it to develop an initial Harness, and iterate: TKN → Harness → improved TKN → improved Harness → TKN 1.0. Do not attempt to implement every 1.0 feature at once.

## Open design decisions
Authentication provider, hosting stack, data model, search engine, exact community interaction rules, deployment target and release dates must be validated against the current repository and owner decisions. Do not assume them.
