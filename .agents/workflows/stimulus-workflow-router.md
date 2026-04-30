# Stimulus Workflow Router

Purpose: route stimulus designer, trajectory export, legacy stimulus generation, and PsychoPy playback tasks.

## Read Order

1. `.agents/references/stimulus-stage-map.md`.
2. `.agents/references/data-contracts.md` when files, columns, or logs are involved.
3. `.agents/references/symbol-index.md` when public callable symbols may change.
4. Target owner module.
5. Long legacy scripts only when owner-module context is insufficient.

## Task Routing Table

| Query content | Read first | Owner layer |
| --- | --- | --- |
| stimulus designer GUI, PyQt layout, preview guides, tooltips, keyboard shortcuts, drag/drop, screenshot docs | `recent-changes-stimulus.md` | `scripts/stimuli/stimulus_designer_app.py` |
| editable project model, grid points, primitive params, geometry, duration summaries, mirror behavior | `symbol-index.md` | `src/stimulus_designer.py` |
| export CSVs, `parameters/experiment_parameters.csv`, `parameters/total_time_sec.csv`, saved project JSON | `data-contracts.md` | `src/stimulus_designer.py` |
| PsychoPy playback, screen/monitor settings, fullscreen presentation, `stimulus_timing_log.csv` | `data-contracts.md` | `scripts/stimuli/try_projection.py` |
| circular bout, flicker, rocking legacy trajectory scripts and JSON configs | `stimulus-stage-map.md` | matching script/config under `scripts/stimuli/` |

## Ownership Guidance

Generated trajectory CSV semantics are owned by generator code and project/config values. Projection consumes existing `*_trajectory.csv` files and writes playback timing logs without redefining geometry.

Use `.agents/references/recent-changes-stimulus.md` for meaningful handoffs after stimulus workflow changes. Log changes that alter GUI/runtime behavior, projection behavior, generated artifacts, config semantics, validation gaps, or likely next breakpoints.
