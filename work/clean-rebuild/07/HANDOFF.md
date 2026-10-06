# TASK07 supply adaptation handoff

Implementation candidate, 2026-10-05 19:28 UTC. Root owns review, technical release and commits. Dedicated Tester owns every verification command. No push, archive/reference runtime import, production database or credentials.

## Public behavior

The actual Pi dish proposal still enters the Python purchase authority. A selected SKU is retained when missing/short; supply shortage is a successful factual preview rather than a provider failure. `plan_kind` distinguishes `full_plan`, `supply_preview`, and `partial_purchase`. A preview has `can_confirm=false`, and both full and row confirmation are blocked by `SUPPLY_SELECTION_REQUIRED`.

`gaps` preserve ingredient, selected SKU when known, group IDs, original requirement amount/unit, requested/available/shortfall integer sale packs, uncertainty attribute and legal compatible alternatives. Missing catalog, unknown Offer, unknown package specification, unavailable and shortage are distinct. No unknown pack quantity is filled with zero; missing pantry does not imply stock at home. A query exception still follows the real error path.

Compatible same-ingredient candidates use known matching units, actual stock, exclusions, whole-task budget, whole-demand package counts, total price and remainder. Existing same-store owner cart quantities reduce additional availability; task purchase ledger counts remain factual already-bought packages. Candidates never become selected automatically. Mixed sale packs are allowed when no one SKU covers demand. Choosing an alternative that matches another current row merges source contributions before package rounding.

## Decisions and authority

Existing `POST /guide/tasks/{task_id}/plan-revisions` adds:
- `coverage_intent: choose_partial`, with empty items and no dish edit fields: explicitly choose current available subset. Keeps gaps and group targets. No cart write.
- `coverage_intent: choose_alternative`, empty items plus exact current `gap_id` and nonnegative `alternative_index`: choose one displayed compatible option under existing plan/state/session version fences. Recomputes current facts, preserves other requirements and creates a new displayed revision. No cart write.

Historical `partial_ok` remains rejected. Generic `selection_only` cannot turn a preview into a confirmable plan. Only subsequent TASK04 confirmation adds goods; it checks current price, offer version, stock, ledger, owner/version/display and cart capacity, with receipt replay and at-most-once effects unchanged. Re-preparing a dish after a supply change requires a new explicit partial choice where gaps remain.

Single alternative SKU selections persist in protected `dish_groups`. A mixed selection persists its per-group source-demand shares in `pack_allocations` inside that same protected JSON: subsequent headcount edits retain all explicitly chosen pack specifications and scale their source amounts; explicit new specification choice removes the prior allocation. These are demand shares, never fractional sale-package purchases. Receipt-backed group purchase history and source contributions are preserved.

## Retained UI

Existing App sheet shows supply-preview/partial titles, group-addressed gaps, priced/remainder alternatives, explicit `选择可售部分`, and separate `确认加购`. Preview row toggles/confirmation are disabled. Alternative and partial click handlers only call the revision endpoint; confirmation remains its own action. Missing quantities stay unknown; partial uncovered amount is shown rather than a false positive remainder. Existing group people/spec controls, removal, purchase references and unrelated pages are retained.

## Data and verification

No schema or model-registration change: protected task conditions, plan JSON, command and confirmation receipts already support the additive facts. Tests construct minimal isolated products/Offers, remove only synthetic catalog/Offer records for missing/unknown cases and use exact small stocks for mixed packs. Existing synthetic-old/repeated-upgrade and receipt-safe hold tests remain applicable; TASK07 price-change regression explicitly repeats upgrade and receipt replay after partial purchase. No inflated production seed.

Public tests: `backend/tests/test_supply_public.py`, `backend/tests/test_supply_edges.py`. Actual retained App isolated DOM checks: `ui_supply.mjs`, `ui_alternative.mjs`. `progress.md` and `work/ceres2-runtime-upgrade/07/test-runs/` hold RED→GREEN and regression evidence. Final frozen paired verification and Standards/Spec review still required. Offline controlled Pi/DOM passing must not be called real qwen3.8-27b/provider, real browser, or user acceptance; those remain unverified.

TASK11 history is intentionally untouched. It may reuse the same current plan kind/gap/selection/confirmation contract after root release, but must never inherit previous partial-selection or cart authorization.

## Review corrections, 19:33 UTC

Both independent review axes were reported closed by root on exact short hashes `supply_service.py 14ba567f`, `purchase_service.py 3f24a499`, `test_supply_edges.py 7e95f54b`. Spec findings were reproduced publicly before fixing: pricing an alternative now runs the same merged projection as explicit selection (including existing compatible SKU demand), and persisting mixed allocations uses all surviving selected group contributions, including untouched sibling rows. Optional provenance-copy deduplication was left unchanged as nonblocking. Final paired validation is pending on this frozen source; no technical release claimed here yet.

## Final controlled evidence, 19:42 UTC

Supersedes the pending-validation statements above: dedicated Tester verified final paired behavior 150/150 twice, exit 0 (209.28s / 209.61s). Four source maps and current files are identical across 309 files; fingerprint `d7e6cd68b2817c910da7f2756a0fc740cb52b7ec7e7dfc6b27b4695abc20e5f9`. See `work/ceres2-runtime-upgrade/07/test-runs/final-supply-01/`, `final-supply-02/`, `final-supply-source-comparison.json`. Matched preview/alternative App DOM pairs, affected UI regressions, typecheck/build passed. Both review axes are closed. Ready for root technical release; this owner has no further production/test edits pending. User, live-provider and real-browser acceptance remain separately incomplete.

Root released TASK07 controlled technical scope at 19:42 UTC. Shared guide/runtime/App/purchase implementation ownership now transfers to TASK11. TASK07 owner is finished and will not edit those sources. Overall task remains 待验收; live-provider, real-browser and user acceptance are not implied by this release. No commit or push was performed by this owner.
