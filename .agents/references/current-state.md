# Current State

Purpose: collect known mixed migration state and practical caveats.

- The root README is minimal and encoded as UTF-16 little-endian.
- There are no project tests or test configuration currently present.
- The package is installed as `src` via `setup.py`; notebooks import modules such as `src.data_loading`, `src.plotting`, and `src.analysis_tools`.
- Some notebooks still reference legacy/non-current imports such as `src.two_p.*` or `src.utils`; route these through this file before treating them as authoritative.
- Several notebooks contain substantial orchestration and local analysis code. Prefer extracting reusable logic to `src/` when changing shared behavior.
- `scripts/stimuli` contains historical spelling variants such as `trayectory`; preserve existing paths/names unless a migration is explicitly requested.
- `setupAgents.md` is the source of truth for `coding.md`; regenerate rather than editing `coding.md` directly.
