# TASK04 → TASK05 / TASK08 purchase seam

Root released TASK04 controlled technical scope at 2026-10-05 17:55 UTC: baseline88×2 plus separately validated UI and consumed memory successors; see RELEASE.json. Formal status remains 待验收. No live qwen3.8-27b, real browser or user acceptance is claimed.

## Current concrete path

- Actual Pi worker exposes `propose_purchase(ref, quantity)` after `guide_request` + actual product retrieval. Python only accepts refs minted by the current run, resolves canonical SKU, and prepares the plan under the final task/session/run fence. Final `purchase_plan` references the staged host proposal. It never writes cart during model exploration.
- `PurchaseService.prepare` currently handles one explicitly selected direct SKU; it calls deterministic `facts`, projects current Offer and fixture-backed Store delivery, reads per-task/SKU added ledger, increments task revision, and stores `GuideTask.plan_json`.
- Plans contain bundle rows with selected/added/remaining counts, integer fen and sale packages, package size/unit, current offer version, store/zone/delivery version, plan ID/version and the persisted factual message ID. No clock-based expiry is invented: expires_at is null; revisions and supply changes invalidate approval.
- `render_plan` makes factual item/count/unit-price/remaining/total text part of the persisted reply. A model-ready sentence alone is not a displayed offer.

## Authority and writes: preserve exactly

- App has a separate `displayedPlanRef`. It is recorded after a real factual sheet render, never merely after fetching newer state. Changed restored/background snapshots visibly reopen the sheet before the reference is promoted. Every chat sends it independently from the run's latest general admission anchor.
- Text confirmation currently recognizes a narrow explicit phrase set, including “就按这个加购”. It requires exact current displayed `{task_id,plan_id,plan_version,state_version,session_version}`. A future model-identified explicit confirmation must pass the same host gate; model output is not approval.
- Button `POST /api/v1/guide/tasks/{task_id}/confirm` and row `POST /api/v1/guide/tasks/{task_id}/items/{sku_id}/add` use the same `PurchaseService.confirm` UoW and idempotency header. Text finalization calls that UoW before one commit that also records messages, events and final run receipt.
- `CartService.add_in_transaction` never commits. The host owns commit/rollback across cart, PurchaseLedger, PurchaseConfirmation, task state and run receipt. Shelf direct commands retain their own commit and use the same private row writer. Do not call internally committing `mutate` or possibly creating/committing `get_cart` within confirmation.
- Replay of same owner/key/body precedes stale and shopping-write-hold checks; changed body conflicts. Task state and remaining counts prevent second-key/cross-entry duplication. Row subset amounts are bounded by the selected outstanding row; this does not permit supply-shortage partial procurement.
- The current ledger tracks actual amounts added for this task/SKU. It survives selection/quantity changes and is not inferred from global cart counts. Goal replacement/abandonment does not delete cart facts.
- Revision endpoint accepts `coverage_intent: selection_only`, not historical hard-coded partial_ok. It preserves SKU set, recomputes authoritative facts, retains ledger, increments plan/task versions, and persists a newly factual message. Additional dish/supply revisions must keep their own explicit semantics.

## TASK05 / TASK08 boundaries

TASK05 should extend the existing plan's rows and provenance for deterministic recipe requirements, selected specification and servings; do not create a second confirmation system. The source/units/rounding/pantry contracts remain in purchase-contract-map.md. Current direct `prepare` may need a small shared final plan-publication seam when the actual recipe caller exists.

TASK08 should add owner/task/context/version-scoped persisted displayed candidate evidence for cross-turn selection. Current random product refs remain run-local. No global reference registry, copied historical selection database, or fabricated unknown metadata. Its selected canonical SKU must enter this preparation/confirmation contract.

Only one owner may edit guide/runtime/worker/App at a time. Root transferred unique ownership to TASK05; TASK08 supplies exact integration patches through TASK05. TASK10 automatic extraction enqueue hook also goes through TASK05 after its own RED and module readiness. Shared models aggregation, migrations, main/config remain foundation-owned. TASK09 memory source remains its owner's concern; list/one-write/latest-ref/context hooks are already coordinated into guide/runtime.

## Validation and scope

Public new tests: test_purchase_public.py, test_purchase_confirmations.py, test_purchase_safety.py, test_purchase_migration.py. Supplemental failure injection is only at the approved purchase confirmation UoW. DOM harnesses cover retained App buttons, explicit text, exact mock cart amounts, restoration and unseen-plan authority; they are not real browser evidence. Actual backend cart counts are separately asserted through HTTP/SSE tests.

No archived runtime code/database/credentials were imported. Source release includes clean uncommitted implementation, consumed foundation fields, actual Pi lockfile and controlled HTTP provider fixture. qwen3.8-27b and real browser remain blocked for final TASK16 verification, not silently replaced.
