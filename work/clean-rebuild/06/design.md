# TASK06 public contract and evidence boundary

First seam: actual Pi `propose_dish` → authoritative plan/session HTTP projection. Explicit `operation: append` adds a stable group without replacing existing groups. Subsequent update resolves an exact group ID (or the sole unambiguous matching recipe); all other groups survive. No proposal or revision changes the cart.

`conditions_json.dish_groups` retains stable IDs, dish IDs, explicit/default people and ingredient SKU/selection choices. `plan.groups` projects sources; each merged row carries `contributions` with its original group/ingredient/selected SKU/amount/unit. Known compatible requirements are summed before piece rounding and sale-package ceil. Different selected SKUs stay separate. Unknown pantry amounts remain null, not inferred quantities; their package choices are not silently treated as compatible recipe demand.

The existing SKU ledger and confirmation transaction remain authoritative. There will be no second cart mutation path. Revisions use TASK04 version/display/idempotency gates and preserve already added quantities. Shared budget and exclusions apply to the full selected plan. Group-attributed purchase evidence must reference the original exact selected groups and real row purchase, never claim the same shared package was separately bought for every group.

Existing task/plan/receipt JSON supports this extension without new tables. Synthetic/repeated upgrade and hold checks must prove facts survive; no active DB or archived runtime dependency. Static recipe additions select exact staged objects and record hashes. TASK07 supply optimization/partial adaptation is out of scope.

All test/build/typecheck/server commands are Tester-owned. First RED is `backend/tests/test_multidish_public.py::test_explicit_append_keeps_groups_and_merges_before_package_rounding`. Controlled fixtures exercise actual Pi SDK behavior but do not establish live qwen3.8-27b or real-browser/user acceptance.
