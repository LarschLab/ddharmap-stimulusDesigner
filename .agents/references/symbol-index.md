# Symbol Index

Purpose: identify public script-callable stimulus-designer owners.

## `src/stimulus_designer.py`

- `Calibration`, `GlobalStimulusParams`, `GridSettings`, `Primitive`, `StimulusSpec`, `StimulusProject` - editable stimulus-designer project model.
- `default_project`, `project_to_dict`, `project_from_dict`, `save_project`, `load_project` - project persistence helpers.
- `import_legacy_config` - importer for historical stimulus JSON configs.
- `make_grid_point`, `grid_point_to_position`, `mirror_stimulus_in_place` - point-grid placement and stimulus mirroring helpers.
- `generate_stimulus_dataframe` - trajectory CSV dataframe generator for GUI previews and exports.
- `primitive_duration_sec`, `primitive_duration_summary` - primitive-level duration helpers for GUI timeline summaries.
- `export_project` - writes canonical `*_trajectory.csv` files and `parameters/` metadata.
- `launch_psychopy_projection` - starts `scripts/stimuli/try_projection.py` for a generated stimulus folder.

## `scripts/stimuli`

- `stimulus_designer_app.py` owns the PyQt stimulus designer GUI and delegates generation to `src/stimulus_designer.py`.
- `try_projection.py` owns PsychoPy playback, monitor setup, and `stimulus_timing_log.csv`.
- `trayectory_stimuli.py` owns legacy circular trajectory generation and diagnostic plots.
- `Trayectory_flicker.py` owns legacy flicker trajectory generation.
- `Trayectory_rocking_stimuli.py` owns legacy same-arc and left/right rocking trajectory generation.
