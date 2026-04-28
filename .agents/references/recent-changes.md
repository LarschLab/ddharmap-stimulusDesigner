# Recent Changes

Purpose: route meaningful handoff logs.

- Calcium analysis work: `.agents/references/recent-changes-calcium.md`
- Stimulus workflow work: `.agents/references/recent-changes-stimulus.md`
- Agent workflow/documentation work: append this index only when routing or maintenance conventions change.

Use logs for handoff value, not for routine completed edits.

## 2026-04-28

- Date: 2026-04-28
- Short label: Recent-change logging rule clarified
- Slice goal: Ensure future agentic workflow changes and stimulus GUI/runtime edits are captured in the appropriate handoff log.
- Passes completed: Updated `.agents/user-guide.md` to require recent-change entries after meaningful changes, and updated `.agents/workflows/stimulus-workflow-router.md` to route stimulus designer GUI work and explicitly require meaningful stimulus handoffs.
- What changed: Agents should now log meaningful changes that affect workflow behavior, artifact contracts, public callable surfaces, GUI/runtime behavior, migrations, known limitations, or follow-up validation expectations.
- What remains broken: Existing older edits may still be missing historical log entries.
- Remaining in-slice work: None.
- Next likely breakpoint: Agents may still skip logs for work they consider routine; use the revised meaningful-change criteria to decide.
- Rerun implications: Documentation-only workflow change; no tests required.
