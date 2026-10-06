# Snack selection fixtures, next-snack-v2

Owner: TASK01 / implement_next_snack_flow. Consumers: TASK01; subsequent TASK04/TASK08 request additions through this owner.

## Authority and provenance

The prior fixture catalog and Offer source is the tracked Ceres2 baseline 64ca7b6, imported by the existing explicit seed. The source history and image limitations remain in work/clean-rebuild/migration-ledger.md. No old session, cart, order, checkpoint or runtime database is imported.

These are demo product combinations, prices and inventory, not claims about real retailer stock, real brands, nutrition or fulfilment. The added 35g package is an explicitly simulated fixture, identified as demo in both catalog and Offer. It is the single missing same-type/package difference needed for multi-selection; no broad catalog expansion is introduced.

| SKU | Change/source | Sale package | Price and initial Offer | Covered difference |
|---|---|---|---|---|
| demo:snack-original-potato-chips-70g-bag | Existing demo source; Chinese type label derives from existing product name/usage tags | 70g, one bag | Existing590 fen,30 simulated units | SN-normal chips type |
| demo:snack-soda-crackers-100g-box | Existing demo source; label derives from existing product name/usage tags | 100g, one box | Existing690 fen,20 simulated units | SN-normal second business type |
| demo:snack-original-potato-chips-35g-bag | New bounded demo fixture, next-snack-v2 | 35g, one bag | 350 fen,8 simulated units | PKG-price distinct SKU/package; multi-selection |

The seed refreshes only the newly released type_label on an existing catalog row. It inserts absent SKU/Offer rows as before, never resets existing Offer price, version, sellability or stock. The public repeat-import test sets inventory to4 and verifies it survives reseeding.

## Reproducible scenarios and unknowns

- SN-normal: shipped seed -> generic snack question -> eligible types -> concrete package options.
- SN-missing-information: selected product with no sale-package count -> one quantity question -> current plan. No guessed count.
- SUP-insufficient/no-match: isolated tests change Offer price/version/availability or set budget/quantity; stale choices reject and original constraints remain.
- SUP-unknown-safety: catalog has no complete allergen/nutrition evidence. An allergy/dietary hard constraint therefore yields no qualifying supply; ingredient matching IDs are not complete ingredients.
- PKG-price:35g and70g offers are separate SKUs, and shown prices are per sale package, never per unspecified serving.
- Changed safety evidence before confirmation: a controlled test-only explicit complete-allergen statement is changed to include peanut; the public confirm endpoint must reject without cart writes.

Controlled setup/fault injection is in backend/tests/test_next_snack_public.py; assertions use public guide/SSE/session/cart interfaces. Synthetic test-only allergen evidence is never copied into the shipped catalog. Runtime code imports no test fixture logic.

Data and prompt changes are separate commits/evidence; additional products are not counted as model-quality improvement. Actual provider, real browser and user acceptance remain pending.
