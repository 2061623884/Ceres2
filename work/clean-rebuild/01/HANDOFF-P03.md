# TASK01 → TASK03 handoff

Released by root at 2026-10-05 16:10 UTC for controlled technical scope. Both independent reviews cleared; final 21-case public behavior suite passed twice against identical scoped source. Real qwen3.8-27b, browser and user acceptance remain open at TASK16. No archived pass is inherited.

## Ownership transfer after root commit

TASK01 owns `backend/app/api/guide.py`, `backend/app/models/guide.py`, both `pi_product_*` services, `runtime/pi` source/manifests and `backend/tests/test_runtime_pi_product_query.py`. Root may assign these to TASK03 after hash verification and local commit. `core`, identity/catalog/store, model registry, migrations, dependency manifests and main remain foundation/shared-owner files: coordinate changes instead of editing them concurrently.

## Existing seams to preserve

- `PiProductTurnService(db, owner_id).process(session_id, body, run_id=..., deadline=..., progress=...)`: body contains request_id/message/expected task and session versions/view_context. Owner originates only from canonical cookie identity.
- `PiProductRuntime(catalog, assert_current, run_id=...).run(message, should_stop=..., on_phase=..., deadline=...)`: deadline is absolute monotonic time captured at HTTP admission. Same deadline includes reservation/startup/model/tools. Never refresh the 15-second budget at worker startup.
- Node JSONL start/tool_result and all worker events/tool_call/result/error carry host opaque run_id and per-direction contiguous sequence. Actual Pi Agent 1.0.3 executes only search_products/product_details. Worker gets no owner/database access parameters. Host mints references and renders facts; waiting uses finite clarification slots.
- Public routes: create/read sessions, messages, supply-context CAS, turns/stream, turns/stop, and GET turns/{request_id} receipt. SSE types accepted/progress/answer.delta/turn.completed/turn.stopped/error retain protocol_version/run_id/sequence/session_id/target_task_id/payload.
- Shared session/task original anchor is guarded by SQL UPDATE CAS in the final transaction before inserting both public messages and completed receipt. Stop writes persistent receipt status; final commit obtains the database lock and observes stop before persisting. Keep owner/session/digest checks before replay and never reuse an old anchor as new authorization.
- Unexpected host failures log only run id, allowlisted kind and cause hash. Provider diagnostics never expose raw provider bodies, credentials or stderr. Preserve this behavior when reorganizing the stream adapter.

## Minimal current persistence, not a complete TASK03 implementation

`guide_sessions`: owner, entry context, current_task_id, session_version, store/zone. `guide_tasks`: owner/session, state_version, current_step/status and optional plan_json. `guide_messages`: owner/session/task, globally ordered session sequence, public content and request_id. `guide_turn_receipts`: unique session/request, run_id, owner, body digest, status and terminal result.

TASK01 intentionally does not implement one-session-per-owner, active-task transitions, condition revisions, progress query, durable run input/anchor columns, event replay pagination or restart recovery of unfinished execution. Current create-session always creates a new session. Running work uses an in-process daemon thread and one Node worker; SSE disconnect does not itself cancel it, but process restart does not resume it. A stop before receipt reservation can return cancelled=false; TASK03 must explicitly test and settle admission/stop races. Completed receipts and public messages are durable and readable.

## Required regression protection

Retain the 21-case public suite, particularly two-user denial, idempotency/body conflict, five completed tool batches, deadline from HTTP admission including blocked DB admission, explicit in-flight stop, changed revision during exploration, competing revision at first history write, forged tool/ref rejection, safe clarification rendering, empty-selection semantics, real SDK IPC and secret-bearing host diagnostic fault. Add TASK03 public lifecycle tests red-first with the dedicated Tester. Use clean synthetic migration fixtures; no old database/session/cart/checkpoint/credential imports.

Use RELEASE.json for exact owned hashes and CONSUMED-FOUNDATION.json for dependency references. Root owns local commit and follow-on release; implementation files have not changed since final verification.
