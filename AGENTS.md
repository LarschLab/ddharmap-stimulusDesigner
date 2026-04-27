# Agent Entrypoint

This repository uses a routed instruction system under `.agents/`. Start with the generic coding baseline, then use the router to load only the workflow and reference docs relevant to the current task.

## Required startup order

1. Open `coding.md` for baseline coding behavior.
2. Open `.agents/workflows/social-filters-router.md`.
3. Follow its workflow dispatch table.
4. Read the smallest relevant reference doc.
5. Open stage maps or the symbol index only if needed.
6. Open owning modules before large notebooks or scripts.
7. Open large notebook/script regions only when owner-module context is insufficient.

## Non-negotiable repo rules

- Keep notebooks orchestration-thin; reusable analysis logic belongs in `src/`.
- Preserve canonical file names, array shapes, timing fields, and stage order unless the task is an explicit migration.
- Fix semantic bugs at the writer/owner stage, not by patching downstream consumers.
- Treat `scripts/stimuli/try_projection.py` as projection/runtime behavior, not trajectory-generation authority.
- Validate after edits with the smallest relevant import, smoke, notebook-stage, or artifact-contract check.
- Update `.agents/references/symbol-index.md` when public notebook/script-callable symbols change.

## Reference files

- `coding.md` - generic coding behavior generated from `setupAgents.md`.
- `.agents/user-guide.md` - human guide for using and maintaining the workflow.
- `.agents/workflows/social-filters-router.md` - top-level task dispatcher.
- `.agents/workflows/calcium-analysis-router.md` - calcium notebook and `src/` analysis routing.
- `.agents/workflows/stimulus-workflow-router.md` - stimulus config, trajectory, and projection routing.
- `.agents/references/symbol-index.md` - public callable surface and ownership notes.
- `.agents/references/data-contracts.md` - canonical shapes, files, and artifact contracts.
- `.agents/references/current-state.md` - known mixed migration state and caveats.
- `.agents/references/recent-changes.md` - handoff log index.

## Scope note

This file is intentionally short. Repo-specific routing details live under `.agents/`; generic coding behavior lives in `coding.md` and must be applied before workflow-specific instructions.
