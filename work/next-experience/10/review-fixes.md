# Final-review corrective candidate

Base: `e267fc9ae83423212ab4fc382e1d039d090e785f`. This file records implementation decisions, not current TASK status or acceptance. The integrator owns current TASK records; Tester owns commands, hashes, and final verification records.

## Spec axis

- Ordinary Pi search now uses the existing session-scoped comparison search. That search applies the same evidenced safety and drink predicates already used by exploration/purchase, plus the active product type. Active conditions remain authoritative; no new allergy inference or condition relaxation. Direct product details retain their factual projection.
- Product questions carry `known_total_quantity` separately from actual per-option `known_quantities`. One selected SKU can reuse the total. Multiple selections require explicit per-SKU quantities; changing one to many cannot multiply an implicit amount. Explicit edits, including empty input, remain explicit. Text selection follows the same single-versus-multiple distinction.
- Existing shopping result kinds may include one `policy_ref` from the current policy query. Both references are validated before publication. The host emits two existing-protocol messages, persisting the question and the complete policy independently; no new routing call, business workflow, write authority, or App lifecycle is introduced. Plan rendering occurs before composition, so the shopping message reflects the authoritative prepared plan.

## Standards axis

- Expression parse, validation, provider, abort, timeout, unit, and tool-call failures retain a bounded code, allowlisted cause class, and SHA256 fingerprint. The first cause survives cancellation fallout. The host validates and logs this diagnostic internally; no provider text, stack, prompt, credential, or diagnostic is added to user events.
- Worker stderr is drained into a bounded tail and journaled only as an allowlisted marker and fingerprint. Public failure/receipt behavior remains unchanged.
- Removed the unused introduction `onAccepted` callback and three unused CSS selectors.

## Heuristic decisions

- Deferred purchase finalization extraction. The two existing callers have different budget/history ordering, and supply-preview mutates eligibility/gaps before finalization. Sharing this is not necessary to close a behavioral or hard-rule defect; changing the ordering or introducing flags solely to deduplicate would enlarge this correction's transaction/history surface.
- Deferred App expression/navigation extraction. Current code depends on snapshot, interaction, opening, and view fences with existing race coverage. No App production change is needed for the corrected messages protocol. Moving those boundaries during this corrective pass would add unrelated lifecycle risk.

## Behavioral evidence and fixture provenance

Tester alone executes all checks. New public regression files cover constrained reads (including supported empty results), known quantity behavior, compound delivery/reference rejection, and safe expression diagnostics. Two actual-App DOM scripts cover quantity transitions and simultaneous question/policy delivery with remount restoration.

- Constraints: six RED cases established unsafe candidates; initial focused cases GREEN. One inherited fake provider assumed the now-filtered search still returned an unsafe item and crashed. It now uses an intentionally invalid reference when the constrained result is empty, retaining the original invalid-reference/no-cards/no-plan assertions. Parent approved this fixture-only adaptation. Two explicit supported-no-match cases were added.
- Quantity: two API RED cases and one App RED established absent amount/redundant input and multiplied text-selection quantities. The affected API batch of 28 and quantity/snack/drink DOM plus frontend build/typecheck passed before the later diagnostic cleanup; final equality/rechecks remain Tester's responsibility.
- Compound: two API RED cases established omitted policy and ignored forged optional reference. Initial UI fixture changed task identity without session-version advancement; it was corrected to use the already-active task, preserving all assertions. The compatibility DOM then passed. A later API fixture was corrected to request `include_messages=true` when verifying persisted messages; it does not weaken persistence assertions.
- Diagnostics: six RED cases established missing categories for parse, unit, validation parse/rejection, provider failure, and worker stderr. Facts and no-delta checks remain in the GREEN tests.

Intermediate captures affected by disjoint source edits are not final-candidate evidence. Require fresh runtime build, current-source regressions, UI/build/typecheck, freeze/equality, and both independent reviewer rechecks before release.

No real provider, credentials, private holdout, browser/user acceptance, V3 comparison, remote push, or deployment was performed or claimed by this implementation owner.

## Held-snapshot verification (2026-10-06 11:21 UTC)

Tester confirmed unchanged source through the fresh snapshot:

- `review-diagnostics-green`: 6/6 safe-diagnostic cases, 8.89 seconds.
- `checks/review-fixes-runtime`: runtime typecheck/build passed.
- `checks/review-fixes-ui-all`: frontend build/strict typecheck and 37 controlled DOM/client scenarios passed, including both review harnesses.
- `review-fixes-combined`: combined API regression 111/111, 154.35 seconds. Three real 30-second timeout/SQL-stall cases were deliberately left for the final complete candidate run; no earlier pass is inherited for them.

These records live in the integrator's `work/next-experience/10/` evidence area. Counts are scoped records, not a claimed disjoint total. Commit/equality, independent Standards/Spec rechecks, final full-suite/restart run, and external acceptance gates remain separate.

## Re-review correction: explicit search versus comparison page scope

Independent Spec re-review of `7067f3f` found that sharing comparison's callback had also imposed its shelf category on raw `search_products`. An explicit new beverage goal opened from a fruit shelf could therefore falsely report no match. The original three Spec findings were otherwise closed; Standards closed its findings and accepted the heuristic deferrals.

Four public cross-shelf cases produced 2 RED positives and 2 passing dietary negatives. The correction keeps one current-condition filter authority, with a real raw-search callback selecting non-page-scoped search. Comparison keeps its existing page and displayed-reference fences. Active task category and dietary conditions are still applied in both paths; ignoring presentation context does not relax them. Query-only and explicit-category raw searches are both covered. `7067f3f` equality is historical evidence, not final release approval.

Tester confirmed the appended correction with `review-cross-category-green`: 52/52 constraints/comparison/comparison-safety/runtime-product-query cases passed in 146.43 seconds with unchanged source. Earlier 111/6/37 captures remain scoped to `7067f3f`; only the corrected final full sweep can establish complete same-candidate verification.

## Full-sweep fixture correction: early exclusion versus prepare-time revalidation

The frozen corrected full run finished 424 passed / 1 failed, with stable source. The failed legacy node was `test_purchase_safety.py::test_plan_preparation_applies_budget_and_exclusions_before_display[conditions1-EXCLUSION_CONFLICT]`: its scripted provider indexed a banned SKU after constrained search correctly returned no candidates, causing `PI_PROVIDER_ERROR` before the intended preparation check.

No production change is made for this fixture failure. The budget-quote assertions remain unchanged in their own named case. The original static `exclusions=['pi-cola']` semantics are covered explicitly at the public search boundary, asserting no recommendation, no plan, unchanged exclusion, and empty cart. A separate clearly named preparation-revalidation case uses a real scoped search ref, then deterministically changes authoritative catalog brand identity before proposal; it retains `EXCLUSION_CONFLICT`, no-plan, and empty-cart assertions. This preserves both early filtering and the downstream stale-evidence guard instead of weakening either.

Tester verified the fixture-only correction in `review-purchase-fixture-green`: 48/48 purchase safety/public/confirmation/migration and constraint cases passed in 46.04 seconds with stable source. A new immutable final full sweep is still required; the prior 424/1 result is retained as failure evidence, not combined into a final pass.
