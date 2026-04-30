# Data Contracts

Purpose: record canonical stimulus-designer files, columns, and artifact ownership.

## Trajectory CSVs

- Exported trajectory files use `*_trajectory.csv`.
- Dot position columns are named `<dot>_x` and `<dot>_y`.
- Dot radius/visibility columns are named `<dot>_radius`.
- Radius `0.0` means the dot is hidden for that frame.

## GUI Visual Primitive Columns

GUI-generated visual primitives can add non-dot columns while preserving dot columns:

- Whole-field gratings use `grating_active`, `grating_x`, `grating_y`, `grating_direction_deg`, `grating_bar_thickness_cm`, `grating_speed_cm_sec`, and `grating_phase_cm`.
- Loom stimuli use `loom_active`, `loom_x`, `loom_y`, `loom_radius`, `loom_growth_speed_cm_sec`, and `loom_max_radius_cm`.

## Exported Metadata

- `parameters/experiment_parameters.csv` is export-owned metadata summarizing stimuli and global parameters.
- `parameters/total_time_sec.csv` stores the estimated total experiment duration.
- `parameters/stimulus_designer_project.json` stores the editable project used for export.

## Projection Timing

- `scripts/stimuli/try_projection.py` consumes exported trajectory CSVs.
- Projection writes `stimulus_timing_log.csv` with stimulus file, start/end unix time, and actual playback duration seconds.
