# TASK06 multi-dish demand handoff

Controlled technical release, 2026-10-05 19:11 UTC. Root verified both 134/134 runs, stable 304-file source snapshots, DOM pairs/regressions, typecheck/build and closed independent reviews. See RELEASE.json. Root coordinates local commits; no push. Live qwen3.8-27b, real-browser and user acceptance remain unverified. Overall task remains awaiting acceptance.

## Observable behavior and public contract

- Actual Pi `propose_dish` adds `operation: append | update` and optional exact `group_id`. Append requires an explicitly selected new dish in the tool/prompt contract. Default update preserves other groups and resolves an unambiguous recipe or exact retained group. Querying a suggested recipe does not append a target. An old ID cannot revive a removed target.
- Stable groups, original recipe/people sources, selected SKU and ingredient-selection flags live in existing `GuideTask.conditions_json.dish_groups`. Generic condition commands cannot overwrite host-owned `dish_groups` or legacy `dish_selection`. Existing single-dish JSON upgrades on its next explicit revision; the previous single-dish projection remains available when there is one group.
- `plan.groups` and `targets` expose the source groups. Rows carry original `contributions` with group, ingredient, SKU, selected flag and amount/unit/source. Known compatible demand is summed before piece rounding and whole-sale-package ceiling. Different selected SKUs stay separate; unknown pantry amounts remain null with distinct source contributions and do not imply stock at home or recipe coverage.
- Existing `POST /guide/tasks/{id}/plan-revisions` adds `group_update` and `group_remove`, exact `group_id`, empty `items`, and people/selections for updates. These share TASK04 revision/idempotency/version/display rules. Removing a group, including the last one, leaves the actual cart and earlier purchase evidence intact.
- The retained App sheet has group-specific people and compatible-SKU controls, source demand, removal and shared purchase references. Existing single-dish UI remains available. Shared purchases render once with all original group names, including subsequently removed sources.

## Purchase authority and immutable source evidence

TASK04 remains the only confirmation/cart transaction. No new cart mutation or model confirmation authority was introduced. Existing task/SKU PurchaseLedger still controls exact added and remaining sale packages.

Each successful group-backed confirmation adds `group_purchases` to its durable PurchaseConfirmation result: operation ID, actual SKU/name/packages added, and original selected group/contribution snapshots. `plan.purchase_ledger` projects those owner/task-scoped receipts. This deliberately does not claim that one shared package was separately bought for every group, does not allocate fictional fractional sale packages, and does not infer group ownership from the cart. Old receipts lacking group data are preserved and are not assigned invented historical groups. Generic mutable conditions cannot forge this receipt-backed history.

## Storage, fixtures and successor scope

No new tables or columns: existing task, plan, command and confirmation JSON carry these additive fields. Public repeated-upgrade and synthetic-old JSON checks cover compatibility and original cart/ledger/replay facts. New-group re-planning retains the shared budget, exclusions and chosen specs; insufficient budget or exclusions abort the new proposal without partial target mutation.

`import_recipes.py` selects exact staged tomato-and-egg and egg-fried-rice objects into `data/fixtures/recipes.json`; `recipe-provenance.json` records source/destination hashes. Existing catalog already has rice/scallion. No archived runtime, database, credentials, or runtime staging dependency was introduced.

TASK07 may extend demand/supply handling through these same group/contribution/confirmation contracts. This ticket does not implement supply optimization, silent spec replacement, or partial-plan auto-selection. Preserve explicit selected SKUs and original contribution units when adding those behaviors. The independent Task04 ledger remains authoritative even if a removed group no longer has a current plan row.

## Validation evidence

Tests are `backend/tests/test_multidish_{public,edges,removed_target,compatibility}.py`; existing TASK05/04/03 and comparison regressions are relevant to shared-source changes. Actual retained App DOM scripts are `ui_multidish.mjs` and `ui_group_ledger.mjs`, compiled by the existing TASK04 harness. Tester owns every command.

See `progress.md` and raw `work/ceres2-runtime-upgrade/06/test-runs/`. Proven RED→GREEN slices: append/aggregation; targeted group revision/removal after row purchase; immutable source receipt/UI; missing second recipe; reserved condition fields; removed-target revival. Added implemented-behavior regression coverage is explicitly not claimed as preimplementation RED. Final paired evidence and two-axis review outcomes must be recorded separately before release.

Before TASK06 changes, this owner applied TASK08's exact reviewed completion-order, reconnect and protected-close hooks after independent RED. Those successor fixes have their own TASK08 evidence and must not be erased by later shared-source edits.

## Final review correction and ownership transfer

Unrelated row checkbox changes now preserve every unchanged per-group selected flag. A deliberate shared-row toggle changes that row's contributors and recalculates known demand/default sale packages before supply/budget validation. A separately selected package quantity remains explicit. This prevents excluded groups from silently returning or being falsely attributed in a purchase receipt. Public RED/GREEN, explicit quantity and budget regressions cover the rule.

The verified final-source fingerprint is `f3f92bbbecb18f4bff18d92a2cb2175056241bf53698f9b5792a177b9ab8f62d`; raw source reconciliation is `work/ceres2-runtime-upgrade/06/test-runs/final-multidish-source-comparison.json`. The two late test-only cases are included in both final runs and in FINAL-CANDIDATE.json. No application source changed after final review closure.

Root transfers unique shared guide/runtime/worker/App/saleGuide/purchase ownership to the next TASK07 implementer. This TASK06 implementer makes no further application edits or commits. Preserve the TASK08 comparison race/reconnect/protected-close hooks and receipt-backed group purchase evidence while extending supply behavior.
