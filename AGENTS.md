# Agent Entrypoint

This repository is focused on the stimulus designer GUI, trajectory CSV export, and PsychoPy playback.

## Required Startup Order

1. Open `coding.md` for baseline coding behavior.
2. Open `.agents/workflows/social-filters-router.md`.
3. Follow its stimulus-design routing table.
4. Read the smallest relevant reference doc.
5. Open owner modules before long scripts.

## Non-Negotiable Repo Rules

- Keep reusable stimulus-generation logic in `src/stimulus_designer.py`.
- Keep the PyQt GUI in `scripts/stimuli/stimulus_designer_app.py`.
- Treat `scripts/stimuli/try_projection.py` as projection/runtime behavior, not trajectory-generation authority.
- Preserve canonical trajectory CSV columns and metadata outputs unless the task is an explicit migration.
- Fix semantic bugs at the writer/owner stage, not by patching exported artifacts by hand.
- Validate after edits with the smallest relevant import, smoke, GUI, or artifact-contract check.
- Update `.agents/references/symbol-index.md` when public script-callable stimulus-designer symbols change.

## Reference Files

- `coding.md` - generic coding behavior generated from `setupAgents.md`.
- `.agents/workflows/social-filters-router.md` - top-level stimulus-design dispatcher.
- `.agents/workflows/stimulus-workflow-router.md` - detailed stimulus workflow routing.
- `.agents/references/stimulus-stage-map.md` - stimulus generation and projection stages.
- `.agents/references/data-contracts.md` - trajectory CSV and playback log contracts.
- `.agents/references/current-state.md` - practical caveats for the stimulus-only repo.
- `.agents/references/symbol-index.md` - public stimulus-design callable surface and owners.
- `.agents/references/recent-changes-stimulus.md` - handoff log for meaningful stimulus workflow changes.

## Scope Note

Old neural-analysis workflows have been removed from this repo. Do not route new tasks through imaging notebooks, processing pipelines, or neural analysis modules.
