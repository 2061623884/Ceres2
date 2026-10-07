# Current backend regression pass

Date: 2026-10-07 (Asia/Shanghai)\
Worktree: `Ceres2-optimization-20261007`

## Command and result

Working directory: `backend/`\
Exit: `1`\
Result: `175 passed, 2 failed in 324.82s`

```sh
PYTHONPATH=tests:. ../.venv/bin/python -m pytest -q \
  tests/test_dish_public.py tests/test_multidish_public.py tests/test_multidish_edges.py \
  tests/test_multidish_compatibility.py tests/test_multidish_selection.py \
  tests/test_next_shared_policy_public.py tests/test_runtime_pi_product_query.py \
  tests/test_foundation_http.py tests/test_supply_public.py tests/test_supply_edges.py \
  tests/test_final_review_constraints_public.py tests/test_final_review_compound_public.py \
  tests/test_final_review_quantity_public.py tests/test_final_review_expression_diagnostics_public.py \
  tests/test_comparison_public.py tests/test_comparison_safety.py tests/test_comparison_migration.py \
  tests/test_guide_dish_suggestions.py tests/test_next_context_public.py tests/test_history_edges.py \
  tests/test_aftersales_public.py tests/test_human_public.py tests/test_order_case_journey.py
```

Both failures are dish-result expectation mismatches after the demo recipe set expanded:

- `tests/test_guide_dish_suggestions.py::test_suggestions_then_first_choice_requeries_recipe_and_waits_for_confirmation` expected `番茄炒蛋` and `蛋炒饭`; the controlled request returned `番茄炒蛋` and `尖椒炒蛋`.
- `tests/test_next_context_public.py::test_factual_recipe_question_keeps_read_only_dish_facts_without_purchase_task` expected only `dish-fanqie-chao-dan`; the result also contained `dish-dan-chao-fan` and `dish-jiajiao-chaodan`.

No assertions or product code were changed in response. The remaining 175 cases passed, including runtime product-query, catalog/supply/comparison constraints, shared policy, after-sales, human support, and checkout/order-case journey.

## Focused retest after recipe identity and tokenizer fixes

After the dish identity constraint and Chinese unigram/bigram literal relevance revision were in the worktree, the six previously affected/adjacent modules were rerun:

```sh
PYTHONPATH=tests:. ../.venv/bin/python -m pytest -q \
  tests/test_guide_dish_suggestions.py tests/test_next_context_public.py tests/test_dish_public.py \
  tests/test_multidish_public.py tests/test_multidish_compatibility.py tests/test_multidish_selection.py
```

Exit: `0`; result: `31 passed in 55.45s`. This focused run confirms the exact-name factual question and egg-rice suggestion regression are fixed in that source snapshot. It is a separate run from the earlier 175-pass/2-failure run; do not add the counts.

## Full-suite run before the final three failure fixes

Working directory: `backend/`\
Command: `PYTHONPATH=tests:. ../.venv/bin/python -m pytest -q`\
Exit: `1`; result: `431 passed, 3 failed in 813.99s`.

The three failures were:

- `tests/test_guide_lifecycle.py::test_message_pagination_and_completed_stop_return_actual_receipt`: the terminal SSE payload has `recorded_at_ms` and `elapsed_ms`, while the `/turns/stop` cached result omits those two fields.
- `tests/test_guide_recovery.py::test_restart_marks_dead_process_only_and_preserves_committed_result`: the recovery fixture creates a running receipt with `started_at=None`; `append_event` then raises `TypeError` when calculating elapsed time.
- `tests/test_integrated_lifecycle.py::test_human_acquisition_vs_inflight_confirmation_then_close[human-first]`: after repeated `init_db`, the re-read human ticket includes the committed application but the earlier `closed.json()` response had an empty `applications` list.

This run predates the parent session's fixes for the three reported failures. The 431 passing cases include the fulfillment/quality, catalog, policy, order, navigation, runtime and memory paths covered by that source snapshot. The full suite has not been rerun after the fixes.

## Focused retest after the three failure fixes

After the parent session updated Guide event timing/migration, recovery handling and human-ticket projections, the failed modules and directly affected stream/interim/migration tests were rerun:

```sh
PYTHONPATH=tests:. ../.venv/bin/python -m pytest -q \
  tests/test_guide_lifecycle.py tests/test_guide_recovery.py tests/test_integrated_lifecycle.py \
  tests/test_guide_migration.py tests/test_next_result_stream_public.py \
  ../work/ceres2-optimization/testing/test_pi_interim_controlled.py
```

Exit: `0`; result: `45 passed in 160.78s`. This run includes the three formerly failing test cases, nullable legacy timing/migration coverage, next-result stream coverage, and the controlled interim positive, negative, stop, and reconnect cases.

## Targeted closeout checks

- `PYTHONPATH=tests:. ../.venv/bin/python -m pytest -q tests/test_aftersales_public.py -k problem_quantity_clarification`: exit `0`, `2 passed`; covers both quality and fulfillment missing-quantity clarification, proposal, confirm and human handoff.
- `PYTHONPATH=tests:. ../.venv/bin/python -m pytest -q tests/test_foundation_http.py::test_repeat_seed_corrects_chips_procurement_without_resetting_offer`: exit `0`, `1 passed`.
- `../.venv/bin/python ../work/ceres2-optimization/testing/data_import_smoke.py`: exit `0`; repeat import retained 1 store, 71 products and 71 offers, and preserved modified price/stock.
- `../.venv/bin/python ../work/ceres2-optimization/testing/unicode_photo_422_smoke.py`: exit `0`; invalid Unicode text in `data_base64` returned HTTP 422 `PHOTO_INVALID`.
- `../.venv/bin/python ../work/ceres2-optimization/testing/annotation_contract_smoke.py`: exit `0`; explicit synthetic label joined only to its run, the unannotated fixture row remained null, source/events/usage and separate event timestamps were preserved, and unknown, duplicate and invalid annotations were rejected. This is a tool-contract check, not a human or product review.

## Separate current build checks

| Check | Result |
| --- | --- |
| `runtime/pi`: `npm run typecheck` after the final worker telemetry addition | exit 0 |
| `runtime/pi`: `npm run build` after the final worker telemetry addition | exit 0 |
| `frontend`: final `npx tsc --noEmit` | exit 0 |
| `frontend`: final `npm run build` | exit 0; Vite reports config-loader warnings for `__dirname` and JSON import attributes |

Focused current HTTP evidence is in `catalog-hybrid-http-smoke-2026-10-07.json` and `demo-quality-photos-state-smoke-2026-10-07.json`. The failed/incomplete real-model GraphRAG global query sample remains in `graph-query-smoke-v3-canonical-2026-10-07.json` and `graph-query-v3-canonical-content-audit-2026-10-07.json`.

## Native Pi interim seam follow-up

After the native-tool/`finish_response` seam was added, `runtime/pi` typecheck and build both exited `0`. The new native interim/completion tests plus runtime product-query, comparison safety, and the older controlled interim stop/reconnect cases passed `43/43` in `151.79s`; exact command and scope are in [pi-real-provider-native-tools-followup-2026-10-07.md](pi-real-provider-native-tools-followup-2026-10-07.md).

Three fresh live public Guide/SSE samples all completed successfully, but produced zero interim messages: all six observed tool-bearing iterations had absent candidates with `text_characters=0`. These are versioned observations, not a behavior pass. The full backend suite was not rerun for this worker seam change; the earlier `431 passed, 3 failed` and separate `45 passed` post-fix evidence above remain distinct snapshots.

## Latest `recipe_facts` and native interim verification

After the current `recipe_facts` and native interim contract updates, `runtime/pi` typecheck/build both exited `0`; from `backend/`, `../.venv/bin/python -m pytest tests/test_pi_interim_native.py -q` exited `0` with `6 passed in 13.31s`.

The uninstrumented public Guide/SSE recipe-facts sample completed and was accepted with 2 ready interim opportunities, one published interim, and one `finish_response`. The Python-rendered message included both recipes' source quantities, shared egg, current 10pc/6pc egg Offers, and unknown pantry amounts. Isolated cart, confirmation and purchase-ledger counts stayed zero. A separate test-only diagnostic capture and native Firefox pre-terminal DOM observation are documented in [pi-interim-browser-and-audit-followup-2026-10-07.md](pi-interim-browser-and-audit-followup-2026-10-07.md).

The Firefox sample passed the UI/SSE pre-terminal check. This is one real user turn and does not provide a naturalness score or a generalized interim rate. The full backend suite was not rerun after the Pi contract addition; its prior full-suite and focused-post-fix evidence remain distinct snapshots.

## Final full-suite snapshot after current recipe-result interim prompt

This later full suite supersedes the earlier “not rerun” state above while preserving those historical results. It ran after rebuilding the current Pi prompt and updating the official DeepSeek transport assertion for the production `tool_choice=auto` / no-JSON-mode contract.

Command from `backend/`: `../.venv/bin/python -m pytest tests -q`\
Exit: `0`; result: **441 passed in 819.24s**.

The complete command log and runner snapshot are [backend-full-regression-current-prompt-v2-2026-10-07.log](backend-full-regression-current-prompt-v2-2026-10-07.log) and [backend-full-regression-current-prompt-v2-2026-10-07.json](backend-full-regression-current-prompt-v2-2026-10-07.json). The report records HEAD `b118dbea3852026c6a04c790b1e27df67c3c9c18`, a 66-file source snapshot hash, and exit code 0.

The preceding 440-pass/1-failure run remains preserved as a separate source/test snapshot. Its only failure was the stale assertion that main tool-bearing requests include `response_format=json_object`; the current transport test asserts `tool_choice=auto` and absence of JSON mode instead. Current verification details and the later semantic/browser evidence are consolidated in [final-technical-gates-current-prompt-v2-2026-10-07.md](final-technical-gates-current-prompt-v2-2026-10-07.md).
