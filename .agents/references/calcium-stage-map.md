# Calcium Stage Map

Purpose: preserve the ordered calcium-analysis workflow across notebooks and `src/` modules.

Use this file when changing stage behavior, canonical artifacts, or notebook orchestration.

## End-to-end stages

1. Suite2p plane inputs: `*_F.npy`, `*_iscell.npy`, `ops.npy`, `stat.npy`.
2. dFoF extraction: `src/dff_extraction.py` filters cells, dim/unstable/inactive ROIs, computes frames x neurons dFoF, and returns retained ROI indices.
3. Experiment loading: `src/data_loading.py` builds fish/experiment paths, loads merged dFoF and optional artifacts, loads Suite2p plane metadata, and derives stimulus timing.
4. Stimulus timing/table: `src/stimuli_timeline.py` reads trajectory CSVs and block logs, then creates `stimuli_trace_60`, `stimuli_table`, and `stimuli_id_map`.
5. Trial alignment: `src/analysis_tools.py` and `src/stimuli_timeline.py` build trial-aligned or chunked matrices from dFoF/raster data.
6. Filtering/significance: reliability filters live in `src/analysis_tools.py`; Romano-style significant traces live in `src/significant_traces.py`.
7. Response metrics: response classification, left/right index, groupwise onset order, Venn-style overlap, and z-score baseline helpers live in `src/analysis_tools.py`.
8. Figures/artifacts: reusable raster and summary plotting lives in `src/plotting.py`; notebooks choose experiment-specific colors, order, and calls.

## Key outputs by stage

- dFoF extraction: dFoF matrix and retained ROI indices.
- loading: experiment dict with `dfof`, `stimuli_durations`, `stimuli_table`, `stimuli_id_map`, `paths`, optional `raster`, `deltaF_center`, `z_traces`, and ROI index arrays.
- timing: `stimuli_table` rows with block/trial/name/id/onset/offset/time/frame fields.
- significance: `raster` and `deltaF_center` saved together when persisted.
- plotting: sorted raster PNGs and diagnostic figures under experiment plot folders.

## Navigation notes

Use `data-contracts.md` for shapes and filenames. Use `symbol-index.md` to find the owner function before editing notebooks.
