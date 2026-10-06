# TASK12 clean implementation record

Owner: implement_clean_simulated_orders. Current stage: implementation; first fresh public API red recorded by dedicated Tester, green candidate verification in progress. User acceptance remains pending.

## Selective provenance

- Existing frontend `src/SimulatedOrders.tsx`, `src/lib/orders.ts` and App checkout/orders wiring were retained by the clean workspace. Reviewed their actual HTTP contracts before building the new backend. Their old behavior/test outcomes do not establish acceptance here.
- Read-only design references: archived `models/cart.py`, `models/order.py`, `api/cart.py`, `api/orders.py`, `schemas/order.py`, and `services/checkout_service.py`. These supplied historical public contracts and transaction intent only. No old database, credentials, virtualenv, node_modules, runtime import, or full backend tree was copied.
- Fresh minimal `models/cart.py`, `models/checkout.py`, `services/cart_service.py`, `services/checkout_service.py`, `api/cart.py`, `api/orders.py` implement only currently called shelf/checkout/read endpoints. No CartOperation/turn record or unrelated old service machinery migrated.
- One canonical `app.mercury.models.SimulatedOrder` remains owned by the Mercury slice; no second order table. Foundation owns model aggregation, router registration and incremental migration. Older query-only rows keep unknown store as NULL; checkout always writes trusted cart store explicitly.

## Observable transaction behavior

1. Shelf cart writes bind cookie identity, a current cart version and a seeded offer.
2. Preview records current offer/version/quantity/return-policy facts without creating an order.
3. Confirmation requires explicit true, owner-owned immutable preview and idempotency key. Owner write fence precedes all checkout reads, serializing receipt replay and cart mutation in canonical SQLite.
4. One commit persists submitted order snapshot, only exact preview cart rows removed, cart version advancement and stored receipt. A changed cart or offer requires a new preview.
5. Precommit failure rolls all business writes back. A committed response lost after commit is recovered by replaying the same key. Another key cannot commit the same preview; the same key cannot commit another preview.
6. Orders remain publicly readable after recreating the app and are invisible to another owner. Frontend local orders are never imported.

## Fresh verification scope

`backend/tests/test_checkout_public.py` covers API journey, explicit confirmation, owner isolation, immutable offer snapshot, changed offers/cart, atomic failure and postcommit response loss, same-key concurrency, competing shelf add/checkout, key binding and app recreation. `backend/tests/test_checkout_migration.py` is maintained by foundation for additive synthetic P02 schema preservation and repeated upgrade. Tester owns all command execution and source hash records.

Shopping-write hold: precise HTTP red observed before wiring, then `SHOPPING_WRITES_PAUSED=true` dependency added to cart POST/PATCH/DELETE and checkout preview/confirm only. Public order/cart reads remain available; this is a shopping-write hold, not database-wide immutability.

Pending: two independent final behavior passes, actual browser journey and Standards/Spec review. No real payment or model invocation is involved in TASK12. No prior test report is inherited.

## Review correction: pre-TASK12 nonempty snapshot projection

Standards review found that P02 query-only snapshots have authoritative name, quantity and unit price but no display line total/image/offer version. An empty migration fixture did not expose this. New public test starts with the actual older table shape and a nonempty two-unit snapshot, upgrades twice, reads list/detail and verifies exact stored snapshot bytes after the reads. Dedicated Tester observed the missing-field HTTP RED before implementation.

The read projection now derives line total only from recorded quantity × recorded unit price, and returns NULL for unknown image/offer version. It never reads a current catalog offer to enrich history and never updates stored snapshot JSON. Mercury owner agreed this projection contract. Frontend contract explicitly allows unknown offer version; checkout previews still require their known trusted store.

A controlled jsdom harness renders the actual public-response artifact using the real retained components/client. It checks finite historical totals, exact order-bound contact control, no confirmation during preview load, explicit confirmation payload and receipt screen. This is DOM-only evidence, not a real-browser/layout or full live-server shelf journey. Final corrected backend/DOM/type/build passes are owned by the Tester.

Fresh corrected verification reported by dedicated Tester: final-checkout-01/02 each 12 passed; dom-orders-03/04 passed with authored harness source hashes; final-frontend-typecheck and final-frontend-build passed. All source snapshots stable. Real browser and user acceptance remain unverified; Standards correction awaits reviewer recheck.

Root accepted the scoped technical release at 2026-10-05 16:14 UTC after both review axes closed the projection correction. Overall TASK12 is now pending acceptance; actual browser/user checks remain reserved for TASK16. See release-source-manifest.json and task13-handoff.md. No application source changed for this status/handoff update and no commit was made.
