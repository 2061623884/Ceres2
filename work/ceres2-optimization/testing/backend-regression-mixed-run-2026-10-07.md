# Backend mixed-snapshot regression attempt

Date: 2026-10-07 (Asia/Shanghai)\
Worktree: `Ceres2-optimization-20261007`\
Purpose: exercise the previously passing dish/policy regressions plus catalog, supply, product-query, comparison and constraint modules after the knowledge-service integration.

## Commands

| Command | Working directory | Exit |
| --- | --- | ---: |
| `../.venv/bin/pytest -q tests/test_dish_public.py tests/test_multidish_public.py tests/test_multidish_edges.py tests/test_multidish_compatibility.py tests/test_multidish_selection.py tests/test_next_shared_policy_public.py tests/test_runtime_pi_product_query.py tests/test_foundation_http.py tests/test_supply_public.py tests/test_supply_edges.py tests/test_final_review_constraints_public.py tests/test_final_review_compound_public.py tests/test_final_review_quantity_public.py tests/test_final_review_expression_diagnostics_public.py tests/test_comparison_public.py tests/test_comparison_safety.py tests/test_comparison_migration.py tests/test_guide_dish_suggestions.py tests/test_next_context_public.py tests/test_history_edges.py tests/test_aftersales_public.py tests/test_human_public.py` | `backend/` | 4; `ModuleNotFoundError: No module named 'app'` while loading `conftest.py` |
| `../.venv/bin/python -m pytest -q tests/test_dish_public.py tests/test_multidish_public.py tests/test_multidish_edges.py tests/test_multidish_compatibility.py tests/test_multidish_selection.py tests/test_next_shared_policy_public.py tests/test_runtime_pi_product_query.py tests/test_foundation_http.py tests/test_supply_public.py tests/test_supply_edges.py tests/test_final_review_constraints_public.py tests/test_final_review_compound_public.py tests/test_final_review_quantity_public.py tests/test_final_review_expression_diagnostics_public.py tests/test_comparison_public.py tests/test_comparison_safety.py tests/test_comparison_migration.py tests/test_guide_dish_suggestions.py tests/test_next_context_public.py tests/test_history_edges.py tests/test_aftersales_public.py tests/test_human_public.py` | `backend/` | 2; interrupted after 266.60s |

The console-script failure was an invocation issue; `python -m pytest` successfully loaded the application. The latter run ended with 106 passed and 9 failed before Ctrl-C. Source fixtures and Graph code changed while that run was in progress, so this is a mixed-snapshot diagnostic only and must not be used as final regression evidence. One knowledge-service child logged `BrokenPipeError` during shutdown after the interrupt.

## Failures observed before interruption

- Five cases in `test_runtime_pi_product_query.py` failed: two controlled server handlers indexed an empty `products` list and surfaced as `UND_ERR_SOCKET`; the five-round case completed without the expected product name; the “matched empty selection” case returned no-match; and the competing-revision case never reached its expected write checkpoint.
- `test_foundation_http.py::test_catalog_returns_real_seeded_products_and_current_offer` still expected 70 products while the current fixture contained 71.
- `test_final_review_constraints_public.py::test_explicit_raw_product_search_leaves_shelf_scope_but_keeps_dietary_constraint[True-False]` expected `pi-cola` evidence but got none.
- `test_comparison_public.py::test_task_filters_and_page_category_are_preserved_and_empty_retires_refs` expected one controlled product card but got none.
- `test_comparison_safety.py::test_protected_comparison_close_retires_old_snapshot[deadline]` observed `WORKER_EXIT` before completion.

Several controlled test products are not in the versioned BGE index; confirm the intended boundary for test and non-demo catalog rows before interpreting the empty results. Re-run this scope after the catalog/runtime implementation is stable. The complete live tool output contained fixtures and error details but no credentials; this report preserves the sanitized findings.
