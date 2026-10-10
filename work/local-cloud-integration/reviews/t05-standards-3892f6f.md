# T05 frontend integration: independent Standards review

## Fixed scope

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T05-ui`, clean at inspection.
- Baseline: `8186897ee58d7bf0702b17cfe86509c32c27ccfa`.
- Frozen HEAD: `3892f6fbcafd9fc438edcb878ecd2a0c4799ae93`.
- Exact diff: `git diff 8186897ee58d7bf0702b17cfe86509c32c27ccfa...3892f6fbcafd9fc438edcb878ecd2a0c4799ae93`.
- Commits: `git log 8186897ee58d7bf0702b17cfe86509c32c27ccfa..3892f6fbcafd9fc438edcb878ecd2a0c4799ae93 --format='%H %s'`; two commits, a9c9c51 and 3892f6f. Full list and diff saved alongside this report.
- Standards: root AGENTS and frontend/AGENTS, T05 TASK/integration spec, applicable canonical-authority and domain conventions. Twelve requested smell heuristics considered; repo overrides and tooling exclusions respected. Frontend callers, existing async fences and independent test/journey source were read without execution.

## Findings (under 400 words)

Hard documented violations: none established.

Judgment finding P2, asynchronous operation identity is incomplete: `frontend/src/SimulatedOrders.tsx:100–109`, new `advance()`, applies `setSelected(current)` on success and `setSelected(null)` on failure without checking the currently selected order/view generation. The Back control (line 116) and order-list selection remain enabled. A reproducible sequence is advance order A, return to the list, open order B, then settle A's request: late success replaces B with A, while late failure clears B and assigns A's error to B's view. The visible “联系墨墨” action can then target the wrong order from the user's perspective. Retain an operation/view-generation identity and captured order ID; update A in the list independently but only update detail/error state if that operation still owns the active view. Invalidate on back/navigation/unmount. Add delayed-success and delayed-failure DOM regressions. This is an engineering correctness judgment, not an invented hard AGENTS style rule or a source-side transaction failure.

No other independent smell warranted a finding. Mercury's newer contact initialization explicitly waits for prior selection writes to settle, uses generation readiness before send/handoff, and guards late reads. Product details suppress stale fetch completion. AfterSales additions reuse selection/case generation fences and canonical proposal confirmation; receipt IDs preserve idempotency.

HumanPhotos binds authenticated fetches to ticket/token dependencies, rejects inactive results and revokes both stored and late-created object URLs. Ticket applications/photos render actual linked evidence rather than inferred order-wide evidence. Typed question selection has a synchronous submission latch. SSE replay deduplicates run sequences; stable interim message IDs deduplicate message insertion, and mixed navigation actions remain explicit and opening-scoped.

Existing visual structure is retained while misleading product/delivery claims are replaced with demo wording; prices, quantities and order snapshots use server fields. No backend/authority changes occur.

Outcome: zero hard violations, one open P2 judgment finding. Reported DOM/typecheck/build GREEN is distinct from real Chromium, which remains pending. This reviewer ran no tests, builds, browser, installation or product edits; no browser acceptance is inferred.
