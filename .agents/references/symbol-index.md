# Symbol Index

Purpose: identify public, notebook-callable, or script-callable owners.

Use this file before editing notebooks or long scripts.

## `src/data_loading.py`

- `transform_stimuli_duration` - normalizes stimulus timing dictionaries for downstream alignment.
- `load_2p_experiment` - high-level 2P loader that builds paths, loads dFoF/artifacts, derives stimulus timing, and returns the canonical experiment dict.

## `src/dff_extraction.py`

- `load_fluorescence_data` - loads Suite2p fluorescence as frames x ROIs.
- `filter_dim_rois` - filters low-intensity ROIs.
- `compute_percentile_baseline` - computes smoothed percentile F0 baseline.
- `compute_dff` - computes `(F - F0) / F0`.
- `filter_inactive_rois_by_std_or_z` - keeps active ROIs by std or z-event evidence.
- `process_suite2p_fluorescence` - Suite2p plane-to-dFoF extraction owner.

## `src/stimuli_timeline.py`

- `get_motion_timing_simple` - current default trajectory timing extractor.
- `get_radius_timing` and `get_stimulus_timing` - legacy/specialized timing extractors.
- `make_stimulus_traces` - older movement/appearance trace builder.
- `make_stimulus_traces_2` - canonical stimulus table and numeric trace builder.
- `extract_stimulus_chunks` - extracts stimulus-aligned neural chunks for plotting.

## `src/stimulus_designer.py`

- `Calibration`, `GlobalStimulusParams`, `GridSettings`, `Primitive`, `StimulusSpec`, `StimulusProject` - editable stimulus-designer project model.
- `make_grid_point`, `mirror_stimulus_in_place` - point-grid placement and in-place stimulus mirroring helpers.
- `generate_stimulus_dataframe` - trajectory CSV dataframe generator for GUI previews and exports.
- `export_project` - writes canonical `*_trajectory.csv` files and `parameters/` metadata.
- `import_legacy_config`, `load_project`, `save_project` - JSON import and editable project persistence.
- `launch_psychopy_projection` - starts `scripts/stimuli/try_projection.py` for a generated stimulus folder.

## `src/analysis_tools.py`

- `find_file_with_suffix` - helper for unique suffix-based file lookup.
- `build_trial_aligned_traces` - trial-window extraction around stimulus onsets.
- `plot_accepted_rejected_rasters` - reliability inspection plotting.
- `filter_neurons_by_trial_reliability` - neuron reliability filter and saved index owner.
- `classify_responses_from_raster` - evoked/tardive response classification owner.
- `compute_left_right_index` - left/right response index owner.
- `build_neuron_order_groupwise_onset` - grouped onset sorting owner.
- `plot_venn_3stim` - response-overlap plotting helper.
- `zscore_dfof_from_prestim_baseline` - pre-stimulus baseline z-score owner.

## `src/plotting.py`

- `add_stimuli_markers`, `raster_with_stimuli` - base raster/stimulus marker rendering.
- `compute_sort_orders`, `compute_single_sort_order` - raster sorting owners.
- `save_sorted_rasters_for_all_modes` - saved sorted-raster artifact owner.
- `plot_sorted_chunks_single_mode` - single sorted chunk raster owner.
- `plot_stimulus_means`, `summarize_durations` - stimulus mean/summary plotting helpers.
- `compute_move_lines_for_flat_matrix`, `plot_allfish_flat_raster` - flat all-fish raster owners.

## `src/significant_traces.py`

- `gaussfit_neg`, `estimate_and_center_noise_model`, `normalize_dff` - noise fitting and normalization owners.
- `extract_transition_points`, `estimate_kde_peak`, `generate_synthetic_noise`, `create_grid`, `histogram2d`, `compute_global_sigma` - transition-density pipeline pieces.
- `compute_significant_odds`, `rasterize_with_odds`, `compute_noise_model_romano_fast_modular` - significant trace/raster pipeline owners.
- `plot_dff_and_raster` - aligned centered-dFoF/raster diagnostic plot owner.

## `scripts/stimuli`

- `trayectory_stimuli.py` owns base circular trajectory generation and trajectory diagnostic plots.
- `Trayectory_flicker.py` owns flicker trajectory and flickering-dot generation.
- `Trayectory_rocking_stimuli.py` owns same-arc and left/right rocking trajectory generation.
- `try_projection.py` owns PsychoPy playback, monitor setup, and `stimulus_timing_log.csv`.
- `stimulus_designer_app.py` owns the PyQt stimulus designer GUI and delegates generation to `src/stimulus_designer.py`.
