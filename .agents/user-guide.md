# Stimulus Designer Agent Workflow Guide

## User Guide

Use short task prompts that name the target and intended outcome. Helpful targets are the GUI, a primitive type, export files, PsychoPy playback, README screenshots, or a specific stimulus JSON/script.

Good examples:

- "Fix Bezier arc preview behavior in the stimulus designer."
- "Explain Export CSVs versus Launch PsychoPy in the README."
- "Update the PsychoPy playback screen settings."
- "Add a regression test for mirrored point-path exports."

Expect agents to read `AGENTS.md`, `coding.md`, the top-level router, then the smallest relevant workflow/reference doc.

After meaningful changes, agents should report the validation they ran and append `.agents/references/recent-changes-stimulus.md`. A meaningful change affects GUI/runtime behavior, artifact contracts, public callable surfaces, generated outputs, docs workflow, or validation expectations.

## Developer Guide

Keep workflow docs compact and stimulus-focused. Add a new workflow profile only when a task family has distinct entrypoints, owner layers, stage semantics, and validation surfaces.

When changing the public stimulus-design callable surface, update `.agents/references/symbol-index.md`. When changing trajectory CSVs, metadata files, or timing logs, update `.agents/references/data-contracts.md`.

`coding.md` is generated from the appendix block in `setupAgents.md`. Edit the appendix block, then run:

```bash
python scripts/sync_coding_doc.py
```

Do not put repo-specific ownership rules in `coding.md`; keep them in `AGENTS.md`, routers, and `.agents/references/`.
