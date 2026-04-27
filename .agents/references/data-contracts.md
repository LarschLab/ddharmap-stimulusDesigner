# Data Contracts

Purpose: record canonical shapes, files, and artifact ownership used across workflows.

## Calcium contracts

- dFoF matrices are frames x neurons. Keep this orientation unless a function explicitly documents a transposed plotting shape.
- `load_2p_experiment` returns a dict containing `dfof`, timing metadata, `stimuli_durations`, `adjusted_log`, `stimuli_trace_60`, `stimuli_table`, `stimuli_id_map`, `paths`, `dFoF_merged_map`, optional artifact arrays, and Suite2p plane metadata.
- `stimuli_table` rows contain block, trial, stimulus name/id, onset/offset time, onset/offset frame, and total frames.
- `stimuli_id_map` maps stimulus names to integer IDs starting at 1. Zero in traces means no stimulus.
- `trial_aligned_traces[stim_id]` is treated by plotting as neurons x time x repetitions.
- `raster` and `deltaF_center` are frames x neurons and must remain aligned.
- Kept/filtered ROI index arrays preserve mapping back to Suite2p ROI indices.

## Canonical calcium files

- Merged dFoF: `<fish_id>_dFoF_merged.npy` under `03_analysis/functional/suite2P/merged_dFoF/`.
- Filtered ROI indices: `<prefix>_dFoF_merged_filtered_roi_indices.npy`.
- Significant traces: `<prefix>_significant_traces.npz` with `raster` and `deltaF_center`.
- Reliability filter indices: `<prefix>_kept_neuron_indices.npy`.
- Z-score artifact: `<prefix>_zcore.npz` with `z_traces`.

## Stimulus contracts

- Trajectory files use `*_trajectory.csv`.
- Dot position columns are named `<dot>_x` and `<dot>_y`; radius/visibility columns use `<dot>_radius` where applicable.
- Projection consumes generated trajectory CSVs and writes `stimulus_timing_log.csv` with stimulus file, start/end unix time, and duration seconds.
- `parameters/experiment_parameters.csv` is generator-owned metadata and should stay compatible with existing notebooks/scripts.
