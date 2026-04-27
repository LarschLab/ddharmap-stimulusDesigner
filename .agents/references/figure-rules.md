# Figure Rules

Purpose: route plotting changes to the correct owner.

## Ownership

- Reusable raster rendering, sorting, movement onset lines, legends, and saved plot filenames belong in `src/plotting.py`.
- Significant trace diagnostic plotting belongs in `src/significant_traces.py`.
- Notebook cells may set experiment-specific colors, line styles, stimulus order, figure size, and one-off figure composition.

## Edit rules

- Fix duplicated plotting bugs in `src/plotting.py` before editing multiple notebooks.
- Keep binary raster and continuous dFoF colorbar labels distinct.
- When changing movement line placement, verify whether the input is seconds or frames before changing division by `fps_2p`.
- When saved filenames or folder names change, update `data-contracts.md` if downstream consumers depend on them.
