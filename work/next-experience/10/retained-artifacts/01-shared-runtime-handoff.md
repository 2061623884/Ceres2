# Shared Pi/runtime ownership handoff

Owner transfer: from implement_next_snack_flow to implement_next_context_modules, authorized by the parent on2026-10-06. This is a pending adapter contract, not an implemented or tested production change. TASK01 release remains84181e9; no runtime edits were made for the items below.

## Pending TASK08 activity guard

Consumer: implement_next_activity_flow, isolated next-08 branch. TASK08 is not a business prerequisite for TASK05. The new owner should provide/review the bounded patch on the consuming08 branch only until its release, rather than mixing it into the semantic-equivalence baseline for05.

TASK08 owns three explicitly simulated AC finished-product records, a fixed light-meal entry endpoint, membership filtering and atomic composition with the existing lifecycle. Its shared helper activity_mismatch(product, conditions) requires both metadata.activity_ids membership and finished_product=true. ProductQuestionService can query without category_id only while this fixed activity scope is active, and shows direct products rather than a cross-type question. Current budget, quantity, safety and other applicable constraints remain authoritative. A user-directed new_goal exits the activity through existing task semantics.

Known missing boundary: PiProductRuntime.search_products currently reads the raw CatalogService, and search_dishes/propose_dish can bypass the finished-product boundary. Guarding only route_result.conditions is insufficient because a model can omit guide_request. Use the current Python task authority.

Proposed minimum two-file adapter, reusing existing callbacks and adding no runtime tool/schema:

1. backend/app/services/pi_product_turn_service.py supplies a required activity_active() callback to PiProductRuntime. It reads the current owned session/current GuideTask conditions each time and returns whether activity_id is active. Do not capture a stale boolean at turn start; an explicit guide_request new_goal must be observed immediately. Do not serialize full navigation metadata into Pi context.
2. backend/app/services/pi_product_runtime.py stores that callback. When active:
   - search_products uses the existing explore_products host callback as a read-only constrained search, without publishing a question. Take its eligible products (first five plus actual total), then use the existing per-run product reference machinery. This preserves activity membership, quantity, budget and dietary constraints even when guide_request is omitted.
   - search_dishes and propose_dish reject with ACTIVITY_SCOPE_CONFLICT before recipe expansion/preparation. Once the user explicitly changes goals, the normal existing recipe path works again.
   - product_details fetches current facts and verifies the SKU still belongs to a fresh constrained explore result before returning it. A changed membership or current condition must not be treated as eligible activity supply.

Outside an active activity, keep the existing search/details/recipe behavior unchanged. No generic tool-policy engine, pending store, new model call or second business authority is needed. PurchaseService.facts retains final membership/safety validation.

TDD status: TASK08 first entry RED confirmed404; its first GREEN and dedicated runtime RED are still pending at handoff. TASK08 will author public actual-Pi tests for omitted-guide_request raw search, recipe expansion rejection, hard-condition preservation and relevant freshness/exit behavior. Wait for the sole Tester's RED before implementing. Send the resulting scoped patch to08 for its controlled candidate; do not introduce an08 dependency into05.

## Pending TASK04 prompt clauses

TASK04 confirms these approved changes are still unwritten; no worker.ts edits were made by04:

- Change “零食泛需求和具体类型选购” to “零食或饮品泛需求和具体类型选购”.
- Extend the existing ordinary amend-field guidance brand/packaging/pack_count_mode/category_id/query with flavor and spec. spec is typed {quantity:number, unit:string}, not concatenated display text.

These clauses belong to the consuming drink slice. Coordinate their application with04 and preserve them when modularizing the prompt. Do not count changed fixture coverage as a model-quality improvement.

## Other shared delegated work

-04 owns bounded DR filter_options and beverage metadata, optional QuestionChoices filter display, beverage-only final factual filter guard and one demo lemon-cola contrast. Existing answer DTO/identity/receipt/confirmation contract stays unchanged. Category label/filter checks must tolerate08's absent category_id. Filter controls render only for products questions, not quantity continuations.
-08 owns AC records and activity-specific scope hunks, plus the narrow existing transition(commit=False) composition required to publish task/question/receipt atomically. Old callers keep default commit behavior. No simultaneous independent rewriting of the shared question authority is authorized.

Shared code changes still need explicit scoped ownership, public tests and merge review. The two consumers' disjoint fixture records must both survive composition; final catalog count is70 (baseline65 + one snack + one drink + three activity records). Real provider, real browser and user acceptance are not established by these controlled patches.
