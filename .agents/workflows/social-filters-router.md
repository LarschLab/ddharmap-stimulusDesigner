# Stimulus Designer Router

Purpose: dispatch tasks in this stimulus-designer-only repository.

Use this file after reading `AGENTS.md` and `coding.md`.

## Read This First

1. Classify the target: GUI, trajectory generation/export, PsychoPy playback, docs/workflow, or repo tooling.
2. Open the matching smallest reference.
3. Open owner modules before long scripts.
4. Preserve trajectory and timing contracts unless the task explicitly asks for a migration.

## Workflow Dispatch

| Target or query content | Open first | Owner layer |
| --- | --- | --- |
| GUI layout, point grid, preview drawing, primitive editor, drag/drop, project open/save | `.agents/workflows/stimulus-workflow-router.md`, then `.agents/references/recent-changes-stimulus.md` | `scripts/stimuli/stimulus_designer_app.py` |
| Project model, primitive geometry, dataframe generation, mirror/export semantics | `.agents/references/stimulus-stage-map.md`, then `.agents/references/symbol-index.md` | `src/stimulus_designer.py` |
| Trajectory CSV columns, metadata files, exported project artifacts | `.agents/references/data-contracts.md` | `src/stimulus_designer.py` |
| PsychoPy fullscreen playback, display settings, timing log | `.agents/references/data-contracts.md` | `scripts/stimuli/try_projection.py` |
| Legacy stimulus generator scripts or JSON packages | `.agents/references/stimulus-stage-map.md` | `scripts/stimuli/*.py`, `scripts/stimuli/*.json` |
| README, install docs, screenshot docs, agent workflow docs | `.agents/user-guide.md` | docs and `.agents/` |

## Cross-Workflow Invariants

- Prefer owner-module edits over patching generated CSVs.
- Keep generated trajectory files as `*_trajectory.csv`.
- Keep projection playback as a consumer of exported CSVs.
- Log meaningful GUI/runtime/export behavior changes in `.agents/references/recent-changes-stimulus.md`.
