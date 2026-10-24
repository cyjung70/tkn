# TKN ↔ Harness Engineering — Proposed Architecture

## System boundary
TKN is the **upstream knowledge and specification system**. Harness is the **execution and feedback system**, with Claude Code performing coding actions. ChatGPT and other tools may contribute source material, but an AI conversation is not automatically an approved task.

## Iterative pipeline
1. Import and preserve source conversations (ChatGPT, Codex, Claude, Claude Code).
2. Classify by technical topic; extract decisions, unresolved questions, requirements and provenance.
3. Create concise, traceable English task briefs with explicit acceptance criteria.
4. Queue approved tasks for Claude Code/Harness execution.
5. Inspect repository, implement incremental changes, run tests and QA locally.
6. **Human checkpoint 1**: review after QA passes.
7. **Human checkpoint 2**: review immediately before deployment (including local deployment, if that is the current target).
8. Deploy to the authorized target; run post-deployment smoke checks.
9. **Human checkpoint 3**: review the deployed result.
10. Perform automated Git commit only after the three checkpoints, as requested; confirm branch/commit policy before implementation. Never silently push or deploy to production.
11. Feed verified errors, resolutions, test evidence and decisions back into TKN/Obsidian, linking original sources and code revisions.

## Asynchronous/mobile use
The owner can capture Korean requests by phone and later inspect summarized plans, QA evidence, deployment previews and approval requests. No unattended deployment, publication or commit that bypasses the defined approval gates.

## Engineering controls
- Idempotent ingestion; source identifiers and content hashes; versioned derived notes.
- Least-privilege credentials, secrets outside notes/logs, privacy filtering before publication.
- Task states: drafted → reviewed → queued → implementing → QA-passed → approved-1 → ready-to-deploy → approved-2 → deployed → approved-3 → committed → knowledge-synced.
- Persist state and audit trails so a paused run resumes safely without duplicate actions.
- Test failures return to implementation; failed deployment triggers safe recovery and requires renewed review as appropriate.

## First automation priority
Automated **Git commit** after the prescribed approval gates; initially use dry-run, staged-diff review and a controlled test repository. Treat this as a target workflow, not an existing feature.
