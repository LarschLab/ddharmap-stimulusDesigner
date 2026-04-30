# Stimulus Stage Map

Purpose: preserve stimulus-design, export, and projection semantics.

## End-To-End Stages

1. Editable project: the GUI stores stimuli, primitives, global timing, calibration, and grid settings.
2. Trajectory generation: `src/stimulus_designer.py` turns each stimulus into a dataframe.
3. Export: `export_project` writes `*_trajectory.csv` files plus `parameters/` metadata.
4. Projection playback: `try_projection.py` loads exported CSVs, opens PsychoPy fullscreen playback, draws frame by frame, and writes `stimulus_timing_log.csv`.
5. Documentation: README screenshots are generated from the GUI with `scripts/docs/capture_gui_screenshots.py`.

## Concept Ownership

- Project model, grid geometry, primitive semantics, mirror behavior, duration summaries, and export dataframe generation: `src/stimulus_designer.py`.
- GUI layout, project editing, point selection, preview guides, drag/drop, screenshot-facing UI: `scripts/stimuli/stimulus_designer_app.py`.
- Display hardware, screen/monitor settings, frame playback, escape handling, and timing log: `scripts/stimuli/try_projection.py`.
- Legacy JSON-based trajectory generators remain under `scripts/stimuli/` and should be preserved unless an explicit migration is requested.

## Navigation Notes

Do not patch exported CSVs by hand to compensate for malformed generation. Fix trajectory generation in the owner code.
