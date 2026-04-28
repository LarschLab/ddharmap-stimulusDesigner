# Stimulus Workflow Router

Purpose: route stimulus JSON, trajectory generation, and PsychoPy projection tasks.

Use this file when a task mentions `scripts/stimuli`, trajectory CSVs, stimulus packages, projection playback, or timing logs.

## Read order

1. `.agents/references/stimulus-stage-map.md`.
2. `.agents/references/data-contracts.md` for trajectory CSV and timing-log contracts.
3. `.agents/references/symbol-index.md` for generator function ownership.
4. Target JSON/script.
5. Projection script only for runtime display/playback behavior.

## Task routing table

| Query content | Read first | Owner layer |
| --- | --- | --- |
| circular bout trajectories, angle/radius/speed math, base trajectory CSVs | `stimulus-stage-map.md`, `symbol-index.md` | `scripts/stimuli/trayectory_stimuli.py` |
| flicker trajectories, flickering dot radius/size, flicker duration | `stimulus-stage-map.md`, `data-contracts.md` | `scripts/stimuli/Trayectory_flicker.py` |
| rocking trajectories, same-arc or left/right rocking, rocking metadata | `stimulus-stage-map.md`, `symbol-index.md` | `scripts/stimuli/Trayectory_rocking_stimuli.py` |
| JSON package/config values | `stimulus-stage-map.md` | matching JSON under `scripts/stimuli/` |
| PsychoPy playback, screen/monitor settings, `stimulus_timing_log.csv` | `data-contracts.md` | `scripts/stimuli/try_projection.py` |
| Stimulus designer GUI, PyQt layout, app scaling, tooltips, keyboard shortcuts | `stimulus-stage-map.md`, `recent-changes-stimulus.md` | `scripts/stimuli/stimulus_designer_app.py` |

## Ownership guidance

Generated trajectory CSV semantics are owned by the generator scripts and their JSON configs. Projection should consume existing `*_trajectory.csv` files and write timing logs without redefining trajectory geometry.

Use `.agents/references/recent-changes-stimulus.md` for meaningful handoffs after stimulus workflow changes. Log changes that alter GUI/runtime behavior, projection behavior, generated artifacts, config semantics, validation gaps, or likely next breakpoints; skip only routine edits whose implications are fully obvious from the diff.
