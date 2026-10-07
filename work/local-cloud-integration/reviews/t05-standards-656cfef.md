# T05 order-race correction: independent Standards delta review

Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T05-ui`, clean at inspection.

Reviewed delta: `git diff 3892f6fbcafd9fc438edcb878ecd2a0c4799ae93...656cfef8e0c0a5cd23d812c3e4840b64cb4c8495`.

Commit command: `git log 3892f6fbcafd9fc438edcb878ecd2a0c4799ae93..656cfef8e0c0a5cd23d812c3e4840b64cb4c8495 --format='%H %s'`. Two commits, ec75d0f and 656cfef; exact diff/full SHAs saved alongside this report. Implementation handoff read from `t05-656cfef-review-handoff.md`; it is supporting context, not inherited review clearance.

## Result

The previous P2 judgment finding is resolved. The only production change is `SimulatedOrders.tsx`: a view generation advances on opening detail, returning to the list and unmounting. Detail-read responses check that generation. Order advancement captures both generation and order ID; late success still updates the authorized order A's list row, but changes selected detail only if it still owns the current view/order. Late failure similarly cannot clear or assign its error to newly opened order B. The authorized server action is neither cancelled nor automatically retried.

The new public DOM regression holds A's response while navigating to B, then checks both late-success and late-failure variants, B's contact target and exactly one advance request. The browser journey changes only its synthetic PNG bytes; no product image-input policy or evidence scope is altered. All changes have direct current callers and test justification, with no unnecessary abstraction.

Hard documented violations: none open. Judgment/smell findings: none open at `656cfef8e0c0a5cd23d812c3e4840b64cb4c8495` for this reviewed scope. Applicable root/frontend standards and smell baseline remain those in the preceding fixed review; the full UI was not redundantly re-reviewed.

The parent reports both race variants and related DOM/typecheck/build GREEN. This reviewer performed no tests, browser execution, builds, installations or product edits. Real CUA browser verification remains pending; neither the earlier failed raw Chromium launch nor these controlled DOM results are browser acceptance. Independent Spec and final integration gates remain separate.
