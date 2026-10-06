# TASK12 → TASK13 scoped technical handoff

Fresh clean-rebuild technical release accepted by root on 2026-10-05 16:14 UTC. Scope: deterministic business transaction, public API, additive migration, controlled DOM and closed Standards/Spec review. Actual browser journey and user acceptance remain held for TASK16. No archived pass is inherited and no commit is made by this owner.

## Canonical authority

- Import the sole `SimulatedOrder` from `app.mercury.models`; do not create a second order table or frontend-derived authoritative order.
- Fields: order_id, owner_id, nullable store_id, version, status, snapshot_json, total_fen, created_at, nullable delivered_at. TASK12 creates `submitted`, version 1, known trusted store; historical P02 rows can have unknown store. Status/return facts cannot be changed by client selection.
- Recorded items always include sku_id, name, quantity, unit_price_fen, returnable and return_policy_source. TASK12 snapshots additionally include line_total_fen, image_path and offer_version. P02 historical snapshots can omit these display metadata fields.
- The public checkout order projection derives line total from recorded quantity × unit price, uses null for unknown image/offer version, and never changes immutable stored snapshot bytes or enriches from current catalog prices.
- Python canonical business database is the sole authority. Mercury checkpoints may hold references only. Owner comes from the existing trusted anonymous cookie boundary; order buttons supply only an order reference, never owner authority.

## Public contracts available now

`GET /api/v1/orders` → `{items: SimulatedOrder[]}` and `GET /api/v1/orders/{order_id}` are owner-scoped. Missing/foreign order returns 404. Existing `SimulatedOrdersScreen` has an exact `data-contact-order-id` control, but intentionally only shows an unconnected notice; TASK13 owns connecting the actual Mercury entry.

`POST /checkout/preview` takes expected_cart_version. `POST /checkout/confirm` takes preview_id, idempotency_key and confirmed:true. Prefix both with `/api/v1`. No P13 action should invoke checkout confirmation implicitly.

Checkout commits order + exact preview cart deduction + receipt in one transaction. Same owner/key replays identical receipt; conflicting preview/key or stale cart/offer is rejected. `SHOPPING_WRITES_PAUSED=true` gates cart mutations and checkout preview/confirm, leaving reads available. This is a shopping-write hold, not database-wide immutability or an aftersales authorization gate.

## Evidence and boundaries

- `test-runs/final-checkout-01` and `final-checkout-02`: 12 passed each, stable source fingerprints.
- `dom-orders-03` and `dom-orders-04`: finite historical total, exact order contact target, preview without confirmation, explicit confirmation and receipt screen; DOM-only.
- `final-frontend-typecheck` and `final-frontend-build`: passed.
- Public red precedes implementation; historical nonempty-snapshot projection regression has a separate red/fix/retest trail.
- `release-source-manifest.json` separates owned source/tests from consumed shared references. Shared files may advance under their owners; Tester frozen-run manifests determine exact applicability.
