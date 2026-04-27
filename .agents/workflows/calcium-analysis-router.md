# Calcium Analysis Router

Purpose: route calcium-imaging notebook and `src/` analysis work to the correct owner layer.

Use this file when a task mentions calcium-analysis notebooks, Suite2p, dFoF, stimulus timing/alignment, rasters, significant traces, response classification, or plots.

## Read order

1. `.agents/references/current-state.md` if the task touches legacy imports or old notebooks.
2. `.agents/references/data-contracts.md` for shapes, canonical files, and writer stages.
3. `.agents/references/calcium-stage-map.md` for ordered workflow context.
4. `.agents/references/symbol-index.md` for public callable owners.
5. Owning `src/` module.
6. Notebook region only after owner context is clear.

## Task routing table

| Query content | Read first | Owner layer |
| --- | --- | --- |
| dFoF extraction, Suite2p `F.npy`, ROI filtering, baseline percentile, inactive ROI filtering | `calcium-stage-map.md`, `symbol-index.md` | `src/dff_extraction.py` |
| experiment loading, paths, optional artifacts, `stimuli_durations`, `stimuli_id_map`, Suite2p plane metadata | `data-contracts.md`, `symbol-index.md` | `src/data_loading.py` |
| trajectory timing, block logs, `stimuli_trace_60`, `stimuli_table`, trial chunks | `data-contracts.md`, `calcium-stage-map.md` | `src/stimuli_timeline.py` |
| trial-aligned traces, reliability filters, response classification, left/right index, z-scored traces | `symbol-index.md`, `data-contracts.md` | `src/analysis_tools.py` |
| rasters, movement onset lines, sorting, saved plot names, all-fish flat plots | `figure-rules.md`, `symbol-index.md` | `src/plotting.py` |
| Romano-style significant traces, `raster`, `deltaF_center`, transition-density maps | `data-contracts.md`, `symbol-index.md` | `src/significant_traces.py` |
| notebook-only orchestration or experiment-specific colors/order | `calcium-stage-map.md` | specific notebook under `scripts/calcium_analysis/` |
| file organization notebooks, rename/move operations | `current-state.md` | target notebook, with extra caution around paths |

## Ownership guidance

Notebooks choose experiment IDs, paths, colors, run order, and one-off visual composition. Reusable loading, timing, analysis, significance, and plotting behavior belongs in `src/`.

When editing a writer stage, verify the first downstream consumer. For example, changes to `stimuli_table` or `stimuli_id_map` should be checked against trial alignment or plotting callers.

Use `.agents/references/recent-changes-calcium.md` for meaningful handoffs.
