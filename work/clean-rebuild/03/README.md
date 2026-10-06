# TASK03 clean lifecycle slice

Owner: implement_clean_responsive_runs. Started 2026-10-05 16:11 UTC after root released P01 controlled technical scope. Stage: final source frozen at 2026-10-05 17:04 UTC after review fixes; dedicated Tester completed two identical-source 45-case runs (21 P01 regressions and 24 new P03 cases), plus final actual-App DOM and typecheck/build evidence. Root accepted the controlled technical release at 2026-10-05 17:11 UTC after both independent review axes closed. Formal status remains 待验收. Real qwen3.8-27b, browser and user acceptance remain unverified at TASK16.

Source starts from root baseline 49ce511 plus the uncommitted P01/02/12 foundation integration. Initial owned source hashes are in INITIAL-SOURCE.sha256. Root alone coordinates commits.

## Selective migration ledger

- Read-only source of business intent: current TASK03, proactive-upgrade-spec sections 2–3, PROJECT, GLOSSARY, current P01 handoff.
- Existing P01 actual SDK worker and host reference renderer are extended in place; no archived runtime, database, dependency directory, credentials or sessions are imported.
- Reused retained ChatView styling, input, loading dots, message bubbles and saleGuide SSE client; no page redesign.
- New persistence is additive and owned by the foundation maintainer: canonical entry mapping retains old session IDs/history; task conditions; run input/original anchor/process incarnation; event journal and command receipts. Synthetic fixtures only.

## Behavioral seams

POST sessions resolves the owner's canonical entry without deleting older sessions. POST /sessions/{id}/tasks/current accepts versioned, idempotent new_goal/amend/continue/abandon commands; natural text uses actual Pi semantic routing into that same service. GET /tasks exposes owned history. Progress snapshot is host-only. Query runs remain bounded to original admission deadline and five SDK tool batches. Event sequence is durable, and reconnect reads after an explicit sequence. Restart only interrupts previous-process unfinished records, never redoes a possibly ambiguous operation.

## Review-driven boundaries (2026-10-05)

- Canonical entry is an authority boundary, not merely a UI convenience. Earlier owned sessions remain readable; they cannot admit new runs or create another active task.
- Runs are registered durably before worker start and tracked by this app/engine. Shutdown immediately cancels its own runs in memory, attempts the persistent fence with a short SQLite busy timeout within the remaining original deadline, and always performs a bounded join. A database call already blocked can outlive the join; it remains tracked and is checked again before publication. If a writer prevents interruption persistence, the same-process next startup flushes the pending interruption; an actual process restart uses incarnation recovery. This is not a guarantee that arbitrary SQLite or process shutdown completes in 15 seconds. Reopening a session exposes failed/interrupted input and status, without restarting it. Initialization generation guards prevent transports from starting after the panel closes.
- Durable event batches and public messages commit with the terminal receipt. Sequence replay does not invoke the model again. Progress and unrelated general questions do not stop an existing shopping run. Refinements keep the original run anchor immutable and fence stale final facts.
- Host failure diagnostics retain sanitized traceback file basenames, function names, line numbers, cause kinds and message hashes. They never log source lines, exception bodies, provider responses or credentials. Logging occurs before the failed terminal becomes visible.

## General text and grounded business authority

The actual Pi worker first semantically routes the message through `guide_request`, using the same deterministic task-command service as explicit controls. It is not a keyword-only conversational router.

General explanations receive no merchant task, product facts or business-history context. They may use previously approved general explanation text. Proposed natural short messages go through `validate_general_text`: a separate ephemeral actual Pi Agent, using the same configured model, no tools and no merchant context, checks merchant-specific or execution claims. The validation call runs inside one of the existing outer tool batches, is observable as a model call, shares the original 15-second deadline and abort, and has no retries or fresh budget. Five rounds means five completed outer SDK tool batches, not five total provider calls.

The host mints a run-scoped general reference before validation; only an approved reference can be used in the final general answer. Final model text cannot append unchecked prose. General explanations are visibly identified in the UI. Business facts still use host-verified product references and host rendering. This slice cannot produce a cart/order execution receipt or commit a cart write.

The semantic classifier is defense in depth, not a proof that arbitrary natural language contains no incorrect or merchant-related claim. False approvals/rejections remain a model-quality risk, requiring live qwen3.8-27b evaluation in TASK16. Reference scope, task versions, isolation, and absence of business-write authority are deterministic boundaries. Controlled provider tests establish the protocol and known adversarial paths, not universal NLP safety or live-model quality.

## Final controlled evidence

The dedicated Tester reports final-guide-05 and final-guide-06 each passed 45/45 (85.27s and 84.55s) against identical scoped source fingerprint `dabe85a7e9cadddf81926b1b917d0f80dee6f74a2af2fe940a09534196d7afa1`. The verified comparison is `work/ceres2-runtime-upgrade/03/test-runs/final-guide-source-comparison.json`. Final DOM, frontend/runtime typecheck and build also passed. See RELEASE.json for owned source/test hashes and CONSUMED-FOUNDATION.json for shared references. No live-provider/browser/user-acceptance claim is made.
