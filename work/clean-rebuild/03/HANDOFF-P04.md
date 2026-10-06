# TASK03 → following purchase slices (controlled technical release)

Root accepted the controlled technical release at 2026-10-05 17:11 UTC: two identical-source 45-case runs, final DOM/typecheck/build and both independent review axes closed. Formal status remains 待验收; real qwen3.8-27b, real browser and user acceptance remain at TASK16. Root owns commits.

- Canonical owner entry is `GuideEntry`; previous sessions remain readable but cannot admit new runs/tasks. Never create a parallel active task in a historical session.
- `guide_lifecycle_service.transition` is the shared deterministic command boundary. `new_goal` supersedes the old task, `amend` increments its revision and clears an invalidated plan, `abandon` ends it. None mutate cart facts.
- Run admission stores exact input and original anchor before start. A semantic command caused by the run can advance its effective anchor; it does not rewrite the original admission anchor. Read-only work may continue after condition refinement, but its old final reply fails the authoritative revision fence.
- Final public messages, durable answer deltas and terminal event commit with the receipt under the session/task fences. Keep any future shopping proposal or cart commit under the same authoritative identity/revision discipline; do not use a model claim as permission.
- Explicit run stop targets one request. Shutdown/restart produces an honest interrupted receipt for owned unfinished execution; no automatic continuation or ambiguous write retry. Browser/SSE disconnect alone does not stop an admitted run.
- Actual Node Pi SDK still owns the agent loop. `guide_request`, `search_products`, `product_details`, `validate_general_text` are the present tools. Five completed outer tool batches and the original host admission deadline remain the limits. Do not reset the deadline for follow-up checks.
- Product refs remain host-minted and run-scoped. General text uses a separate scoped ref after an ephemeral same-model Pi check; it cannot carry business-write authority. See README for the semantic classifier's residual risk and future live validation requirements.
- Client public seams: create/read session, message pagination, tasks history/current command, status snapshot, POST runs detached admission, POST turns/stream, GET runs/{id}/events or /stream after_sequence, stop, and request receipt.
- App guide UI remains in ChatScreen. It allows concurrent messages, restores durable result/error states, uses one gray rolling action line and separate short-message IDs, and closes transport on unmount without implicit stop. App also contains narrow TASK13 contact-entry consumption and TASK15 operator route wiring; preserve those owners' contracts.

All verification commands belong to the dedicated Tester. Tests use synthetic stores/owners and a controlled HTTP model endpoint driving the actual SDK. No real provider credentials or historical database state have been imported.

## Coordinated ownership transfer

With root’s TASK03 release, TASK04 becomes the unique guide/runtime/App owner for the guide API and models, both Pi services, guide lifecycle/run services, Node Pi worker, guide client, and ChatScreen/App integration. TASK09 memory work must request exact hook patches from that owner instead of editing these files concurrently. Shared config, model aggregation, main and migrations remain the foundation owner's responsibility.

For TASK09, the stable integration points are the committed GuideTurnReceipt and public GuideMessage IDs. The final history/receipt commit is in PiProductTurnService.process; failed/stopped/protected states are explicit and must not be presented as successful business completion. A future durable memory job hook should be coordinated with TASK04 and the foundation owner under TASK09's approved source/version rules, rather than inserted into transport callbacks or delaying the main reply. This handoff does not implement or expand memory scope.

The shared migration file was changed by the foundation owner for TASK14 after the final TASK03 pair. RELEASE.json and CONSUMED-FOUNDATION.json intentionally retain the exact tested snapshot; later combined integration verification must cover that newer shared migration, without rewriting this evidence as having tested it.
