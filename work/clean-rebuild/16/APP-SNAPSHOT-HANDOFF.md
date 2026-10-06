# App snapshot ordering and plan controls handoff

2026-10-05 UTC. Scope: actual retained App public DOM with controlled HTTP/SSE; not real browser/provider or user acceptance.

## Changes

- Session identity, session version, task identity/state version, and read-admission ordering gate authoritative snapshots before destructive card filtering or plan display updates. Read ordering covers candidate publication at unchanged anchors.
- Late terminal text can still appear, while its cards are filtered against the accepted current snapshot. Displayed plan/candidate evidence continues to come from rendered UI.
- Successful local plan revisions advance the same gate and clear prior-version candidate cards.
- Budget quote sheet shows the current cap and exact proposed total. Explicit acceptance invokes only the budget plan revision; separate cart confirmation remains required.
- Existing plan rows expose positive integral sale-package quantity editing through selection_only, preserving other rows and dish identity. Full revision results replace previous optional plan metadata.

## Frozen sources

- frontend/src/App.tsx: 93879404d649fe12d1b2940288e1811d446735620a3b5905d899efc168ca5021
- work/clean-rebuild/16/ui_snapshot_ordering.mjs: 6ff031afcfd915de1abd5d1ed2f1d2bc56e6bed6b135726893cd4f46c11baf81
- work/clean-rebuild/16/ui_plan_controls.mjs: 3fedbd4f4b0bc791fdf9ddca7dc1c551b8b88a7663ad33a0d1fa5acc0717c93f

API/types for acceptPlanQuote, budget_quote, and complete revisePlan response are owned by final integration.

## Evidence

Dedicated Tester ran all commands; implementer ran no tests/build/typechecks. Evidence is under work/ceres2-runtime-upgrade/16/test-runs/.

- red-snapshot-ordering-02: delayed older GET replaces newly rendered task plan.
- red-snapshot-cards: delayed same-anchor GET removes newer comparison cards.
- red-plan-quantity and red-plan-budget: public controls absent before implementation.
- green-snapshot-plan and green-snapshot-cards: both fixed behaviors pass.
- Quantity controls pass, budget passes in green-plan-budget-02 after aligning its selector with the existing yuan formatter (14.00 元).
- Tester reports final App typecheck/build passed.
- Standards reviewer inspected frozen App hash and closed snapshot ordering, revision card invalidation, quote, and quantity findings.

Final matched integration re-run remains with Tester after the other TASK16 owners freeze. No commit or push performed. Root coordinates final source acceptance and commit; user acceptance remains separate.
