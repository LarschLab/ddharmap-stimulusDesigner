# Social Filters Agent Workflow Guide

## User Guide

Use short task prompts that name the target and the intended outcome. Helpful targets are a notebook name, a `src/` module, a stimulus JSON/script, or an artifact such as `dFoF`, `stimuli_table`, `raster`, or trajectory CSVs.

Good examples:

- "Fix the stimulus timing mismatch in `Exp3_rocking_2_several_fish.ipynb`."
- "Add a smoke check for `load_2p_experiment` data contracts."
- "Update the rocking trajectory generator to preserve the same CSV columns."

Expect agents to read `AGENTS.md`, `coding.md`, the top-level router, then the smallest relevant workflow/reference doc. For notebook tasks, agents should inspect package owners before editing notebook cells.

After meaningful changes, agents should report the validation they ran. If work stops with known remaining breakage, they should append the relevant recent-changes log under `.agents/references/`.

## Developer Guide

Keep the workflow docs compact and routed. Add a new workflow profile only when a task family has distinct entrypoints, owner layers, stage semantics, and validation surfaces.

When changing the public analysis surface in `src/`, update `.agents/references/symbol-index.md`. When changing canonical outputs or array/table shapes, update `.agents/references/data-contracts.md` and the relevant stage map.

`coding.md` is generated from the appendix block in `setupAgents.md`. Edit the appendix block, then run:

```bash
python scripts/sync_coding_doc.py
```

Do not put repo-specific ownership rules in `coding.md`; keep them in `AGENTS.md`, routers, and `.agents/references/`.
