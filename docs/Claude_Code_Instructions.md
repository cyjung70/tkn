# Instructions for Claude Code — TKN 1.0 and Existing Harness

You are assisting with the existing **Tonabit Knowledge Nexus (TKN)** repository and its in-progress Harness. Read `TKN_Requirements.md` and `TKN_Harness_Architecture.md` first.

## First assignment: inspect, do not rewrite
1. Inspect the current repository structure, README, existing design documents, implemented import/classification flows, Obsidian integration, tests, scripts, CI/CD, and Harness components.
2. Produce a **current-state inventory** distinguishing implemented, partial, missing, and unverified features. Cite concrete paths and tests as evidence. Do not assume any planned feature already works.
3. Compare the codebase to the two briefing documents; create a gap analysis and prioritized, incremental roadmap from the current version toward TKN 1.0.
4. Propose the smallest useful next iteration and acceptance tests. Favor reuse, safe migration and backwards compatibility.
5. Describe the three human approval gates (after QA, before deployment, after deployment) and the automated-commit rule. Identify ambiguities before changing deployment or Git automation.
6. Explain how validated Harness outcomes will be written back into TKN and linked in the `StableYoung-Knowledge` Obsidian vault while preserving raw sources.
7. Present the plan for human review **before making broad changes**. Do not deploy, publish, commit, push, or modify credentials without authorization.

## Expected initial deliverables
- `CURRENT_STATE.md` — evidence-based repository inventory.
- `GAP_ANALYSIS.md` — planned vs implemented, with priorities.
- `IMPLEMENTATION_PLAN.md` — phased tasks, dependencies, acceptance tests, risks and explicit approval gates.
- `OPEN_QUESTIONS.md` — unresolved decisions requiring owner input.

## Scope restrictions
Only TKN 1.0 and its Harness are in scope. Do not include QuroERP. Blockchain, points and monetization are not part of TKN 1.0. TKN 2.0 / Tonabit Community OS is future context only.

## Communication
The owner discusses ideas primarily in Korean. Use concise Korean summaries for decisions and English for machine-actionable implementation specs. Always preserve provenance and clearly distinguish confirmed decisions from proposals.
