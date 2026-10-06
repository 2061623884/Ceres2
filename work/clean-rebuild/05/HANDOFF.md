# TASK05 single-dish implementation handoff

Current implementation; root owns release and local commits. Controlled evidence is distinct from live qwen3.8-27b, real browser and user acceptance, all currently unverified.

## Public behavior and authority

Actual Pi tools `search_dishes` and `propose_dish` only prepare a host proposal. Python validates current recipe, ingredient/SKU association and units under the final task/run/session fence. Existing TASK04 PurchaseService confirmation is unchanged in authority: exact displayed revision, fresh supply, caller-owned cart/ledger/receipt transaction, no model cart tools.

Minimal recipe fixture selects the exact staged tomato-and-egg recipe. Read `recipe-provenance.json` for source/destination hashes. No archived runtime code, DB, session, cart, or credentials are imported; no runtime staging/archive dependency. Existing isolated catalog includes six- and ten-egg sale packages.

`dish_service.py` computes recipe amount × people / baseline; piece coverage rounds fractional eggs up before dividing by whole-sale-package size. No g/ml/pc conversions. Pantry has null requirement/coverage/leftover and is initially unselected; selecting it means one sale package, never invented 30ml/50g or assumed at-home stock.

`GuideTask.conditions_json.dish_selection` retains dish ID, explicit people (null means default), chosen SKU per ingredient, and explicit ingredient selected booleans. This survives existing `amend` invalidation of plan_json. `plan_json` contains dish baseline/people/source and row ingredient/requirement/source/coverage/leftover/compatible specifications. No new tables or migration needed; public repeat-upgrade/hold checks preserve JSON facts.

`POST /guide/tasks/{id}/plan-revisions` retains `selection_only` for exact existing rows/positive quantities and adds `dish_update` for explicit people or ingredient→SKU choices with empty items. It reuses existing idempotency receipts/version gates/factual message rendering. Unselected pantry keeps truthful sellability/stock; only selected rows impose supply/freshness constraints. Revisions do not add, un-add, or infer cart ownership; TASK04 per-task/SKU ledger persists. Changing budget via task amend is not cart approval.

UI keeps original sheet and displayedPlanRef. It labels baseline versus explicit people, displays demand/whole eggs/package remainder and pantry unknowns, offers people and compatible-SKU controls, and submits precise revisions. Public API/SSE tests observe actual cart; DOM harness only simulates transport and is not browser evidence.

## Ownership and extensions

TASK05 owns dish_service, purchase extension, tests/data and this handoff. Shared guide/runtime/worker/App/saleGuide edits for TASK08 and TASK10 were applied by this unique owner from their exact requests. Foundation owns config/main/model registration/migrations. No TASK06 multi-dish merge or TASK07 supply optimization was implemented.

For TASK06, extend the same plan/confirmation ledger and preserve original per-target demand before compatible merge and sale-pack rounding; do not duplicate a confirmation service. Consider current single-dish field compatibility before introducing groups.

## Validation

Primary: `backend/tests/test_dish_public.py`; Tester raw runs under `work/ceres2-runtime-upgrade/05/test-runs/`.
DOM: `work/clean-rebuild/05/ui_dish.mjs`, compiled by retained `work/clean-rebuild/04-purchase/compile_ui.cjs`.
Final paired run/review status is recorded in TASK05 and later release evidence, not inferred from this implementation handoff.

## Pending TASK08 successor fixes at shared-owner transfer (18:25 UTC)

These are TASK08 review findings, not completed TASK05 requirements; current TASK05 candidate stays frozen at 18:19:16 and has source hashes in FINAL-CANDIDATE.json. Root instructs the new TASK06 shared-file owner to apply TASK08 owner's exact corrections BEFORE starting TASK06 shared edits. TASK08 owns design and tests; TASK05 implementer will not modify the frozen application files.

- Async comparison failure: older A's failed send must not erase newer B's already rendered cards/ref authority. Capture pre-send refs and remove only those refs on failure; preserve newly minted refs.
- Async comparison success order: stale A's success must not clear B's newer cards. Remove only A's captured old refs; admit response cards only if still present in fresh authoritative comparison snapshot.
- Reconnection: completed SSE run result messages/cards must actually render before displayed-reference promotion; merely updating task/plan state is insufficient.
- Protected comparison close: deadline/tool_budget must retire only the captured prior snapshot through existing compare-and-clear service, preserving a concurrent newer display. Do not publish partial explored products as a completed comparison.

TASK08 pending REDs/implementation requests are coordinated by implement_clean_category_comparison. Harness: work/clean-rebuild/08-comparison/ui_comparison_order.mjs (error/success/reconnect); public safety protected-close cases under backend/tests/. Read the TASK08 owner's latest exact integration request and Tester evidence before patching. Current captured shared files must not be mistaken for fixing these known successor findings.

### Exact TASK08 algorithm forwarded after final pair

From TASK08 owner at 18:25 UTC, apply only after its public/DOM RED is recorded:

1. Normal send success: await fresh authoritative `latest` BEFORE `setMsgs`. Build an allowed-ref set from `latest.product_cards`; prune existing cards by that set and filter `turn.product_cards` by it. Append/update `turn.messages` as current send does, then `applyAuthoritativeSnapshot(latest)`. An unrelated older A response with no cards preserves currently authoritative B cards; stale A refs cannot replace B; a truly empty current snapshot clears old cards.
2. Reconnect: consume the resolved turn in `.then(async turn => ...)`, performing the same terminal messages/cards merge gated by latest refs. Do not discard the turn; render before promoting refs.
3. Catch: capture `shownCandidates` before the try, then remove only that captured ref set from current displayed refs and each message's cards. Preserve newer refs minted by concurrent B.
4. Protected host close: when status is `deadline` or `tool_budget`, invoke `ComparisonService.clear(session_id, comparison_snapshot_refs)` in the already fenced final transaction. Existing CAS clear preserves concurrent newer display. Do not publish partial explored cards.

Root released TASK05 controlled technical scope at 18:26 UTC after 97/97 twice, stable scoped fingerprint, App DOM twice, typecheck/build and both reviews closed. These TASK08 successors are deliberately not included in that release. New TASK06 owner is now responsible for shared-file application; TASK05 implementer makes no further application edits or commits.
