# Social Filters Router

Purpose: dispatch tasks to the smallest workflow and reference docs needed for this repository.

Use this file when starting any task after reading `AGENTS.md` and `coding.md`.

## Read this first

1. Classify the primary target: calcium analysis, stimulus workflow, docs/workflow maintenance, or repo tooling.
2. Open the matching workflow router.
3. Open the smallest semantic reference named by that router.
4. Open owning modules before notebooks or long scripts.

## Workflow profile dispatch

| Target or query content | Open first |
| --- | --- |
| `scripts/calcium_analysis/*.ipynb`, dFoF, Suite2p, stimulus alignment, trial-aligned traces, significant traces, rasters, response classification, z-score baselines | `.agents/workflows/calcium-analysis-router.md` |
| `src/data_loading.py`, `src/dff_extraction.py`, `src/stimuli_timeline.py`, `src/analysis_tools.py`, `src/plotting.py`, `src/significant_traces.py` | `.agents/workflows/calcium-analysis-router.md` |
| `scripts/stimuli/*.py`, stimulus JSON configs, trajectory CSVs, PsychoPy projection, timing logs | `.agents/workflows/stimulus-workflow-router.md` |
| Agent workflow docs, handoff logs, `coding.md`, routing rules | `.agents/user-guide.md`, then relevant `.agents/references/*` |

## Cross-workflow invariants

- Apply `coding.md` first, then repo-specific router and reference rules.
- Prefer package/module edits over orchestration-layer edits.
- Preserve canonical outputs, stage semantics, and legacy filenames unless migration is explicit.
- Do not treat wrappers or notebooks as business-logic authority when reusable owners exist.
- Fix semantics at the writer stage, not in downstream consumers.

## Compact scaling rule

Add an entry to an existing profile when the task uses the same owners and validation surface. Create a new profile only when it has separate entrypoints, stage order, semantic references, and handoff needs.
