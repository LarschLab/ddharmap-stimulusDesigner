# Refactor Rules

Purpose: keep edits inside the real owner boundary.

- Keep notebooks orchestration-thin: path selection, parameters, experiment-specific ordering, and calls.
- Move reusable analysis, timing, loading, significance, and plotting behavior into `src/`.
- Keep stimulus-generation behavior in `scripts/stimuli/` generator scripts and JSON configs.
- Keep projection runtime behavior in `scripts/stimuli/try_projection.py`.
- Do not add notebook-local helpers when the logic should be reused across experiments.
- Preserve canonical outputs, filenames, variable names, and stage order unless explicitly migrating them.
- Do not patch downstream consumers to compensate for upstream timing, shape, or artifact bugs.
- Prefer targeted import/smoke checks over broad notebook rewrites.
