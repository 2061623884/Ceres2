# TASK08 shared integration contract

Owner: TASK08 comparison model/service/component/tests. TASK05 uniquely owns guide API, Pi runtime/worker, App and saleGuide. Foundation owns registration/migrations. Tester exclusively runs validation. Approved seam is public HTTP/SSE and retained comparison cards.

## Service API (caller-owned transaction)

- ComparisonService(db, owner_id).search(session_id, arguments, view_context=None) -> products list, total. Arguments query/category_id/brand/packaging/pack_count_mode. Host applies current task conditions plus page category, without inventing missing product metadata. Limited to five displayed candidates.
- .publish(session_id, products, message_id, view_context=None) -> cards. Mint persistent candidate refs independent of runtime query refs. Save owner/task/session/state and effective page context. No plan/cart writes.
- .current(session_id, view_context=None) -> cards. Return empty on a changed owner/task/version/context. Used in session projection and next-turn displayed candidate context.
- .resolve(session_id, ref, displayed_refs, view_context=None) -> current product facts. Require ref in exact client-displayed set and matching current persisted scope; throw COMPARISON_STALE otherwise. Re-fetch SQL catalog facts under selected store; no old prices reused.
- .clear(session_id, expected_refs) -> retire that exact snapshot only. Capture current refs before runtime, then call in failed-run final transaction even for provider failures before tools. Concurrent newer displays survive; an empty comparison is published as an empty snapshot.

Runtime actual compare_products tool invokes service search, mints run-local refs into existing products map, marks comparison requested. Final comparison answer validates product_refs as existing runtime products then returns outcome comparison=True + products. Final host transaction publishes cards and response product_cards; query itself never returns purchase_proposal. Empty and error invalidate old snapshot. Context exposes comparison_candidates only after posted displayed_candidate_refs matches current persisted refs. propose_purchase resolves persisted candidate via host callback when not a run-local product, keeping final {sku_id,quantity} unchanged for PurchaseService.prepare.

Frontend types permit null brand/packaging/count/item volume/total volume/price/unit price. Component renders unknown explicitly. App tracks actually rendered current candidate refs separately from background state, posts displayed_candidate_refs; candidate button uses existing selection text. Clear all old message cards/refs on new comparison empty/error response; changed task/context invalidates refs. Restored current cards can be rendered then promoted; a background fetch must not silently promote unseen references.

## Evidence boundaries

Controlled real-Pi HTTP fixture is technical evidence only. Actual qwen3.8-27b provider configuration and real browser remain unavailable; no live/browser/user acceptance implied.
