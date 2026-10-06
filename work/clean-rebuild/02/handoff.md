# TASK02 canonical query handoff

## TASK13 order integration

`app.mercury.models.SimulatedOrder` is the only order ORM authority. It shares `Base` and business SessionLocal with Owner and MercuryCase. Fields: order_id, owner_id, status, total_fen, snapshot_json, created_at, delivered_at; TASK12 required additive store_id nullable and version=1. Pre-TASK12 unknown store stays NULL; no invented demo mapping. Snapshot item fields consumed by MercuryOrderService: sku_id, name, quantity, unit_price_fen, returnable, return_policy_source. Reads always scope order_id AND owner_id. No order is seeded automatically for a visitor.

Mercury public list and selection bind the canonical ID. Selecting with expected selection_version increments both selection_version and responsibility_generation, resets visible query status, and is rejected during active run or non-agent responsibility. Existing UI and API names remain: /api/v1/mercury/orders and /sessions/{id}/order. Independent browser order entry prefill integration is not established by this ticket's DOM race test.

## TASK15 responsibility and case integration

`app.mercury.models.MercuryCase` in the same business DB owns case_id, owner_id, order_id, selection_version, responsibility (agent), responsibility_generation, active_run_id/active_until, messages_json, query_status and tool_rounds. Do not introduce a second case/owner authority. `CaseStore.reserve_query` atomically permits only agent responsibility and idle/expired lease. Query publication checks owner, selected version, responsibility generation and run ID in one update; release matches its own run ID. Lease is 30 seconds for crash recovery; exploration stays 15 seconds and 5 rounds.

Official SqliteSaver at shared Settings.mercury_checkpoint_path stores execution state only. Case IDs never authorize access; public endpoints verify canonical ownership before graph access. Human hold/generation changes must be canonical business transactions. No business write/receipt API is provided here. TASK14/15 must enforce their own generation and confirmation fences within the business write transaction; graph state is never an authorization substitute.

Query graph supports order-selection interrupts and request_clarification(slot=query_topic|item) with host-owned prompts. Each new user input resumes from checkpoint using a new bounded run. Model prose is not displayed as factual approval: final text is rendered from authoritative reads. Missing facts remain awaiting_details; failed reads remain query_failed. Future richer output must retain this truthful boundary.

## Evidence and remaining gates

Root accepted scoped technical result at 2026-10-05 16:14 UTC after both review axes closed. Dedicated Tester 14/14 independent final passes have identical source fingerprint; actual OpenAI SDK controlled HTTP and fresh DOM race harness passed. qwen3.8-27b live quality, real browser/layout and user acceptance remain TASK16 gates. Old archived results are not inherited.
