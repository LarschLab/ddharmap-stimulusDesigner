# Refactor Loop Policy

Purpose: prevent superficial cleanup that leaves the same owner slice inconsistent.

## Default working unit

Use one semantic owner as the working unit: a loader, timing function, plotting helper family, significant-trace pipeline, stimulus generator, or one notebook orchestration slice.

## Required loop

1. Identify the owner and first downstream consumer.
2. Make the narrowest owner-layer change.
3. Remove only dead code created by the change.
4. Run the smallest relevant validation.
5. Update reference docs/logs only when public behavior or handoff state changes.

## Stop conditions

Valid stop conditions: validation passes, a required input/data artifact is unavailable, or continuing would cross into a different owner.

Invalid stop conditions: one cleaned cell while adjacent cells in the same owner slice still contradict it, static reasoning without validation, or editing a consumer while the writer remains wrong.

When stopping with remaining breakage, append the relevant workflow recent-changes log.
