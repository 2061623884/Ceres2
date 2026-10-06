# TASK09 shopping → aftersales → shopping

## Scope and current authority

Source baseline: `ec221f939ef711158f0cd9109d88feec0c94089e`, including released TASK02 policy and TASK03 single joint role/capability decision. This slice reuses existing cart, checkout, order, Mercury, proposal/application/receipt, and human services. No order database is imported, no business state/table is added, and no model receives application authority.

The existing App already exposes separate cart and simulated-checkout confirmation, exact-order contact, a concrete aftersales proposal and separate submission control. Released TASK03 already handles pure return as navigation only and compound return as one explicit page choice plus the full original request and stable request ID. No App/navigation or Prompt/runtime rewrite was needed. The destination runs its normal fact reads; neither a navigation result nor a selected order grants purchase/application consent.

## Gaps fixed after observed RED

1. A direct proposal failure was only a transient UI error. Public case reread returned no failure, so leaving Mercury hid it. `AfterSalesService.record_failure` appends a safe order-bound explanation to existing case conversation history. It does not change responsibility, query state, proposal validity, application status, or receipt identity. Existing query execution retains responsibility for publishing its own errors.
2. A lost confirmation response could leave an actionable local proposal after the application had committed. `AfterSalesPanel` now reads the canonical aftersales endpoint after a proposal/confirmation error. It never reposts. A committed receipt replaces the old card; a still-valid proposal remains available for a later explicit action. A failed recovery read is visible and asks the user to check the receipt before resubmission.

Failure narration is limited to known business error codes or a generic service-failure sentence; raw provider/exception content is not copied. Owner, selected order and selection version are checked. Unknown/foreign proposal IDs, malformed input and stale requests do not write narration. An active query owns publication rather than racing with this helper. Existing human responsibility fencing and asynchronous ticket entry remain unchanged.

A postcommit response failure is reconciled against the canonical receipt before narration. It says a receipt exists and that the application is not approved or refunded, never falsely claims the application was not submitted. Historical failure text remains in the conversation after later shopping; it cannot itself authorize a retry.

## Controlled fixture provenance

`backend/tests/test_next_shopping_return_public.py` creates all orders through current public cart/checkout endpoints. The full journey uses the real Pi SDK against the inherited loopback model fixture, then current Mercury queries and LangGraph application handling. Static product fixtures are current test catalog/Offer rows, not imported historical orders or state.

The suite covers explicit cart vs independent checkout, exact new-order query, proposal vs explicit application, receipt replay, unchanged order snapshots, user-chosen compound return, original text/request ID, current goods exploration, denied unshipped-line return, precommit failure, postcommit response loss, foreign/malformed/stale boundaries, and human-held application protection. The pre/postcommit injections are controlled service-boundary faults, not real provider outages. The inherited test client's raised exception is intentionally observed before querying the public persisted outcome.

`ui_application_recovery.mjs` executes the actual component and client adapter with controlled HTTP responses. `ui_shopping_return.mjs` executes the actual App controls across cart, checkout, order contact, application, compound return and reopen. These are DOM/client checks, not an actual browser or a second source of business truth; backend assertions are separate.

## Evidence and limits

Tester owns all execution and raw records under `work/next-experience/10/` on integration.

- `next09-red-01`: public denied-application history RED, empty messages after rejection.
- `next09-green-01`: that durable-history case GREEN; the newly added full journey caught a fixture omission of explicit role entry. The fixture was corrected to choose Mercury through the public navigation endpoint; the production role gate was not weakened.
- `checks/next09-dom-red`: response-loss recovery RED, canonical receipt absent from rendered UI.
- `checks/next09-dom-green`: recovery and inherited aftersales DOM GREEN, frontend build and strict typecheck passed.

Expanded public/inherited and full-App DOM results are added only once reported by Tester. Real Kev and main-model behavior/latency, real browser/layout interaction, natural-language review and personal acceptance remain unverified. No live provider, credential file or real payment/refund was used. Current TASK state remains owned by the integration task index.

### Full-App checkpoint

Tester `checks/next09-app-journey` passed all actual-App controlled journey assertions. It also emitted a React warning about updating ShoppingApp while ShelfScreen renders. Static inspection locates the inherited category-load callback in App's ShelfScreen, which calls parent `onCategoryChange` inside `setActiveCat`'s updater. TASK09 does not edit App; the warning was reported to its sole owner and root. Passing assertions do not erase this warning or establish browser rendering quality.

The first expanded backend run (`next09-green-02`) passed 39 cases and failed one test assertion that incorrectly expected conditions in the SSE projection. The test now reads conditions through the existing canonical session GET instead. No product contract was changed to satisfy either fixture correction.

### Final controlled checkpoint

Tester `next09-regression-final`: all 40 current public journey plus inherited aftersales/human/order cases passed in 11.06 seconds against unchanged product/test source. The six new TASK09 cases are included, not added again to the count. New recovery DOM, inherited aftersales DOM, actual App journey, frontend build and strict typecheck passed in the separately named records above. Integration base was fast-forwarded to `b02ddc6` before freeze; that sync changed TASK documentation only. Root classified the observed inherited React warning as non-blocking technical debt pending final review, not a reason to suppress logs or expand this slice.

### TASK04 composition and freeze

Before commit, this branch fast-forwarded to integration `5b820f5c24a417aec5046f0810f53d966ddbd190`, adding the disjoint released TASK04 source with no conflict. TASK09 source stayed unchanged. Tester then reported:

- `next09-final-public`: 6/6 TASK09 public cases passed on this composed candidate.
- `checks/next09-final-runtime`: runtime typecheck and build passed.
- `checks/next09-final-ui`: frontend build, strict typecheck, recovery DOM and full-App shopping/return journey passed.

The 40-case inherited run remains scoped to its pre-TASK04 candidate; it is not relabeled as a full postcomposition regression. The documented React warning persists. Independent Standards/Spec review and final same-candidate broader regression remain separate gates.
