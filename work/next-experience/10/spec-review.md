# Independent Spec-axis review

Reviewer: review_final_spec. Report date: 2026-10-06 UTC.

This report preserves the original findings and subsequent review decisions. It is not a test result or user-acceptance claim. Review was read-only; this report is written only in the integration checkout, not a frozen candidate. No application tests, builds, credentials, or external requests were used by this reviewer.

## Reviewed revisions

- Original fixed baseline: `64ca7b6b9a7aa113aa42d54270604913f6c19d58`.
- Original candidate: `e267fc9ae83423212ab4fc382e1d039d090e785f`; review covered the phase-wide baseline-to-candidate change, the commit list, approved specification, tickets, and relevant public contracts.
- First corrective candidate: `7067f3f17c67e89b57b41e292805dd80b9799789`; re-review covered its delta from the original candidate and the three findings below.
- Final corrective candidate reviewed: `f272fd8d0db91c5848a81bdd2bd19fd972b4d8ec`; re-review covered its appended delta and the introduced page-scoping regression.

Specification references below are to `docs/plans/ceres2-next-experience-spec.md` at the original candidate.

## Original findings at e267fc9

1. **P1: Dietary and drink constraints bypassed by ordinary comparison/search.** Spec line 39 requires that hard constraints not be silently relaxed; line 125 requires evidenced dietary facts. `backend/app/services/comparison_service.py:38–75` did not apply `safety_mismatch` or `drink_filter_mismatch` outside activity mode. `backend/app/services/pi_product_runtime.py:105–110` similarly used unconstrained catalog search. Users could receive unsafe or attribute-unknown recommendations even though later purchase validation rejected them. Required correction: enforce current constraints on these recommendation paths and add public coverage.

2. **P2: Known quantities required redundant entry.** Spec lines 38–41 require preservation of quantities and direct progress when information is sufficient. `product_question_service.py:98` omitted known quantity information for ordinary product questions. `frontend/src/QuestionChoices.tsx:13,24,38–40` left fields blank and blocked list creation until re-entry. Required correction: preserve a known total without multiplying it across multiple selections.

3. **P2: Compound shopping and policy outputs could not both surface.** Spec line 145 requires preserving complex multi-goal requests. `pi_product_runtime.py:334–353` returned mutually exclusive shopping or policy outcomes, and `pi_product_turn_service.py` published only that outcome. Even valid queries for both parts of “来点零食，也说明退货政策” discarded one result. Required correction: bounded composition of independently validated references and persistent public messages.

No unasked scope creep was identified.

## Re-review at 7067f3f

- Dietary/allergen and drink predicates were added to ordinary comparison/search. The original safety finding was addressed, but callback reuse introduced the regression below.
- Quantity correction accepted: `known_total_quantity` is distinct from explicit per-option quantities. A single selection reuses the total; multiple selections require an explicit allocation. Explicit edits and clearing survive selection changes; text selection follows the same distinction.
- Compound correction accepted: supported shopping outcomes can attach a current validated `policy_ref`. The host separately persists the actionable question/shopping result and policy message, preserving source, conditions, and authorization boundaries. Forged references are rejected before result publication.

**New P2: Raw search inherited comparison-only page-category restrictions.** `pi_product_runtime.py:106` routed raw search through the comparison callback; `pi_product_turn_service.py:135` supplied browser `view_context`; `comparison_service.py:44–47` prioritized the displayed shelf category. An explicit new beverage request from a fruit shelf returned false no-match despite valid supply. This conflicts with spec line 35's specific-product access and line 173's inherited-business preservation. Required correction: share authoritative task constraints without imposing comparison-only presentation scope on raw search.

## Final re-review at f272fd8

**All reported Spec findings closed in inspected source.** Raw search now uses a distinct `product_search` callback with `scope_to_page=False`. Comparison retains its existing `view_context` and default page fence. Only the raw-search presentation-category restriction is bypassed: authoritative task category/query, dietary/allergen evidence, drink filters, activity restrictions, and store authority remain enforced. Four added public scenarios cover query-only/explicit-category cross-shelf requests and sufficient/unknown dietary evidence. Quantity and compound corrections remain unchanged. No further Spec blocker or scope expansion was identified in this delta.

## Evidence and acceptance limits

Tester reported scoped results for the first correction (111 affected API cases, 6 diagnostic cases, and 37 controlled DOM/client scenarios plus build/typecheck) and 52 constraint/comparison/safety/runtime-query cases for the appended correction. These are Tester reports, not reviewer executions, and earlier results are not automatically same-candidate evidence for f272fd8.

At this review's completion, integrated freeze/equality and the final complete corrected-candidate regression/restart sweep remained separate pending gates. Real Kev/main-model sampling, real browser journeys, natural-language review, independent unseen holdout, frozen-V3 comparison, and user acceptance remained open. Source-review closure does not imply any of these gates passed. Subsequent test status belongs to the integration handoff and TASK records.

## Narrow fixture-only re-review at 116414c (2026-10-06 11:47 UTC)

Reviewed `f272fd8d0db91c5848a81bdd2bd19fd972b4d8ec...116414c76060eae82c08966b521816f4d4302c3e`. Only `backend/tests/test_purchase_safety.py` and the corrective report changed; production source is unchanged.

**Accepted: no acceptance weakening identified.** The budget quote, disabled-confirmation, retained-budget, and empty-cart assertions remain intact. The static excluded-SKU case now checks the correct public behavior: supported no-match, no recommendation evidence, no plan, unchanged exclusion, and no cart mutation. The separate preparation test first obtains a real scoped reference, then changes authoritative catalog brand identity before proposal. It retains exact `EXCLUSION_CONFLICT`, unchanged conditions, no-plan, and empty-cart assertions, preserving downstream stale-evidence protection rather than replacing it with early filtering alone.

The earlier full run of 424 passed / 1 failed remains failure evidence: its obsolete scripted provider indexed a banned SKU after search correctly filtered it out. Tester-reported 48/48 affected cases and the integrator-reported 242-file equality are scoped evidence, not a substituted full pass. The new full snapshot `0c752a2` still requires its own completed full result. External acceptance gates above remain open. This narrow review ran no tests and changed no product source or frozen snapshot.
