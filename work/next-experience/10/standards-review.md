# Independent Standards review

Recorded 2026-10-06 UTC. This is review evidence, not TASK acceptance or a second current-status tracker. Reviews were read-only; the reviewer ran no tests, builds, installations, provider calls, or source edits. This report is saved only in the integration checkout, not a frozen candidate.

## Reviewed scope

- Original complete commit list and production/data diff: `64ca7b6b9a7aa113aa42d54270604913f6c19d58...e267fc9ae83423212ab4fc382e1d039d090e785f`, inspected in `next-final-candidate`.
- Corrective review: `e267fc9ae83423212ab4fc382e1d039d090e785f...7067f3f17c67e89b57b41e292805dd80b9799789`, inspected in `next-review-fixes`.
- Narrow final review: `7067f3f17c67e89b57b41e292805dd80b9799789...f272fd8d0db91c5848a81bdd2bd19fd972b4d8ec`, inspected in `next-review-fixes`.
- Standards sources: root and frontend `AGENTS.md`, `docs/agents/issue-tracker.md`, domain reading rules, glossary, applicable ADRs and task/contracts. Tooling-enforced formatting was not treated as a review finding.

## Original documented-rule findings and closure

1. **P2: lost expression failure causes.** At the original candidate, `runtime/pi/src/result-expression.ts:72,81,99` discarded parsing, validation and provider exceptions into `stop()`/`failed`; `backend/app/services/result_expression_runtime.py:22` discarded stderr. This violated the root requirement to preserve original causes when converting errors. **Closed at 7067f3f:** the first safe diagnostic category, allowlisted cause class and fingerprint survive cancellation fallout. The host validates and logs the diagnostic internally; stderr storage is bounded and logs only an allowlisted marker/hash. Raw provider text, credentials and diagnostics are not forwarded into user events. Unchanged by f272fd8.
2. **P3: unused optional hook.** `frontend/src/lib/resultIntroduction.ts:7,26` introduced `onAccepted` without a caller, contrary to the prohibition on unused optional hooks. **Closed at 7067f3f:** definition and invocation removed. Unchanged by f272fd8.

No P0/P1 Standards finding was identified.

## Heuristic judgments, separately recorded

- **Duplicated Code:** `backend/app/services/purchase_service.py:146–163` duplicated plan construction/finalization in `prepare:117–144`. Extraction is **deferred, not a blocker**: existing budget/history ordering differs and supply-preview changes eligibility/gaps. Refactoring solely for deduplication would enlarge this correction's transaction surface.
- **Speculative Generality / Duplicated Code:** `frontend/src/role-chat.css:26–32,52–66` contained three unused selectors, with `guide-glass-bubble-ai` repeating `guide-glass-bubble`. **Closed at 7067f3f:** unused selectors removed.
- **Divergent Change:** `frontend/src/App.tsx:1107–1163,1941–2039` embeds expression lifecycle and persisted navigation responsibilities in large UI components. Extraction is **deferred, not a blocker**: moving snapshot/interaction/opening/view fences during this correction would add unrelated lifecycle risk. No general workflow abstraction is recommended.

Line references above identify the original e267fc9 hunks.

## Corrective review conclusions

At 7067f3f, both documented violations were closed. The constrained-search, quantity, compound-policy-reference and message-publication changes introduced no new actionable Standards violation or safety regression by static inspection. This conclusion did not substitute for the separate Spec review, which subsequently identified the page-scope issue.

At f272fd8, `product_search` has a real production caller and `scope_to_page=False` addresses that caller's demonstrated requirement. Comparison retains its default page fences. Both paths reuse current-task constraint filtering. These additions are not unused/speculative hooks or generalized configuration. No new documented-rule violation or actionable Standards regression was found; prior closures and justified heuristic deferrals remain intact.

## Evidence limits

Tester-reported 111 affected API, 6 diagnostic and 37 controlled DOM/client/build checks belong to the 7067f3f snapshot; 52 targeted cross-category/constraint/comparison/runtime checks belong to f272fd8. They are separate scoped evidence, not this reviewer's execution and not a disjoint combined total. At the final Standards re-review, the complete corrected-candidate sweep was pending. Source equality, restart and complete-suite results must be established by the Tester's final records. Real-provider, real-browser, natural-language quality, independent holdout/V3 comparison where required, and user acceptance remain separate gates. Static Standards closure does not claim runtime correctness, external acceptance, or deployment readiness.

## Fixture-only re-review, 2026-10-06 11:47 UTC

Independently inspected `f272fd8d0db91c5848a81bdd2bd19fd972b4d8ec...116414c76060eae82c08966b521816f4d4302c3e` in `next-review-fixes`, including the unchanged provider hook and purchase authority context. Only `backend/tests/test_purchase_safety.py` and the corrective report changed; no production code changed.

No assertion weakening or new Standards concern was found. Budget quote, confirmation-disabled, retained-budget and empty-cart assertions remain intact. The static banned-SKU case now explicitly checks empty actual search output, no recommendation evidence, no plan, retained exclusions and empty cart. The separate prepare-time case obtains a real scoped reference, changes authoritative catalog brand data deterministically, and retains `EXCLUSION_CONFLICT`, unchanged exclusions, no plan and empty cart assertions. The fixture scripts the external provider boundary; it does not mock the business search or purchase guards.

No tests were run by this reviewer. Tester-reported 48/48 affected checks and 242-file equality are scoped evidence. The previous full 424-pass/1-failure result remains historical failure evidence. The newly frozen complete run remains pending; this fixture review closes neither that run nor external acceptance gates. This addendum changes only the integration report, not the frozen candidate.
