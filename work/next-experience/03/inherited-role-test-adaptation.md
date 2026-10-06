# Inherited cross-role test adaptation

Scope: test-only updates for the public role-navigation contract. No production code, provider gate, business transaction, skip, or existing assertion changes.

## Recorded RED

Tester froze `ec221f9` and ran the inherited 345-case suite: 339 passed, 6 failed. Evidence: `work/next-experience/10/runs/frozen010203-full/record.json` and `output.log` in the integration workspace. This frozen source and evidence are not modified.

The six cases previously moved from a Keke request directly into Mercury free-text ingress without making the newly required explicit public role choice. The production gate correctly returned `409 ROLE_CHANGED`. The affected nodes are:

- `test_integrated_lifecycle.py::test_comparison_checkout_same_order_graph_receipt_survives_loss_and_restart`
- `test_integrated_lifecycle.py::test_human_acquisition_vs_inflight_confirmation_then_close[human-first]`
- `test_integrated_lifecycle.py::test_human_acquisition_vs_inflight_confirmation_then_close[commit-first]`
- `test_memory_background_cross_role.py::test_actual_role_same_key_keeps_domain_fence_and_truthful_origin[shopping-aftersales-False]`
- `test_memory_background_cross_role.py::test_actual_role_same_key_keeps_domain_fence_and_truthful_origin[communication-communication-True]`
- `test_memory_cross_role.py::test_same_user_keke_memory_is_need_to_know_in_actual_momo_query`

## Adaptation

`backend/tests/public_role_navigation.py` reads the current opening through GET, explicitly selects the destination with POST `/switches`, then verifies target role, unchanged opening identity/quota and no pending business handoff. The tests continue using their original actual Pi/LangGraph boundaries.

The integrated lifecycle helper now explicitly selects Momo after its existing order selection. The two memory modules select Momo before their existing queries; background cross-role memory explicitly returns to Keke before the original final memory-list assertion. No internal navigation/session mutation is used. All original human responsibility race, order/receipt restart, memory origin/domain/recall, provider wording and cart assertions remain intact.

Implementation was prepared in `next-03` after merging integration `b02ddc6`. Tester owns execution and final evidence; full-suite rerun is a separate result from these targeted updates.

## Targeted GREEN

Tester `work/next-experience/10/runs/inherited-role-switch-green/` passed all 7 cases across the 3 affected modules in 14.38 seconds, with unchanged captured source. This includes all 6 original failures and the additional existing explicit-memory preference case. The prior 345-case frozen RED record remains intact. This targeted result is not presented as a rerun of the entire inherited suite.
