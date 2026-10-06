# TASK11 historical reminder and repurchase handoff

Implementation candidate, 2026-10-05 19:59 UTC. Root owns independent review, technical release and commits. Dedicated Tester owns every verification command. No push, archive/reference runtime import, active database or credential use.

## Behavior and public contracts

- GET `/guide/sessions/{session_id}/history` returns only the authenticated owner's inactive task plan snapshots. Historical tasks remain immutable source records; their old prices and ledger are displayed only as history.
- POST `/guide/sessions/{session_id}/history/repurchase` binds the current task/session/state anchor and an explicit source task. A fresh task and plan are prepared using current store, zone, people, budget, exclusions and offer facts. Multi-dish source targets/spec choices are recreated; old plan IDs, ledger, approval and partial-purchase choice are not copied.
- Existing `GuideCommandReceipt` records deduplicate source selection. Same-key replay precedes stale-anchor rejection; different content conflicts. Source provenance is protected task JSON and plan projection. Preparation/revision reannotates source and current differences.
- New-goal admission may offer one relevant unfinished source, after reading actual owner/store cart. Source-once markers use existing command receipts. Full demand is checked against the greater of historical purchased ledger and current cart, rather than double-counting old purchases. Missing-ingredient/unknown-source gaps stay unresolved. Ignore/decline and any later admitted user turn stop that reminder; there is no task restoration or cart write.
- POST `/guide/sessions/{session_id}/history/reminder` accepts explicit ignore/decline for the current task. Owner/canonical-session checks are retained.
- Actual Pi SDK `history_command` lists sources, then stages explicit source selection. Ambiguous “上次” lists/clarifies; a model cannot choose a source without its ID or unique historical goal in current user text. Final response references only the latest host history result.
- Pi interprets ordinary prose effective shopping memories into typed people/budget/exclusions defaults with exact memory ID/revision refs. Python rerecalls under final transaction, checks live refs and whitelists fields; current explicit task conditions override defaults. Uninterpretable applicable preferences require clarification. Reference/communication memory remains background, never offer/cart/approval facts.
- Applied memory defaults retain separate protected provenance, so deletion/expiry is not converted into a permanent explicit task constraint on later repurchase. An explicit amend clears the relevant inferred-default marker.
- Dish and direct-product supply shortages produce current supply previews. Existing explicit alternative/partial selection is separate from fresh cart confirmation. Confirmation still uses TASK04 owner/display/version/offer/stock/receipt authority.

## Retained App

History button reads source list; an explicit source button sends the selected source through the ordinary Pi turn. Optional unfinished-source reminder can be declined. Plan sheet shows historical source, current differences and effective memory background. Supply preview disables confirmation; the user first chooses current available goods, then confirms independently. Existing pages, groups, row purchase, cart and plan controls are retained.

## Data and test seams

No schema/migration/model-registration change. Existing immutable task/plan JSON, protected current conditions and durable command receipts cover the required source/reminder state. Empty and synthetic-old schema, repeated upgrade and receipt-safe hold remain covered by existing migration tests; TASK11 explicitly repeats upgrade across historical selection/confirmation replay. No old database import.

Fixture uses the isolated real-Pi HTTP `pi_client` with two owners plus current `dish_seed`; `make_history` prepares reusable owner history through public operations. Changed price/stock is isolated fixture setup, not a business bypass. Tests assert source immutability and actual cart counts through HTTP.

New files: `backend/tests/test_history_public.py`, `backend/tests/test_history_edges.py`, `work/clean-rebuild/11/ui_history.mjs`. See `work/ceres2-runtime-upgrade/11/test-runs/` for dedicated Tester RED/GREEN artifacts. The DOM script exercises actual retained App under an isolated HTTP transport fixture; it does not establish a real browser session.

## Verification at this handoff

First source/current-supply journey GREEN 1/1; reminder/lifecycle GREEN 12/12; actual Pi history/prose-memory GREEN 3/3; provenance edge correction GREEN 4/4; App DOM, frontend build/typecheck and runtime build/typecheck passed. Two reminder edges, direct-product shortage and deleted-default memory each have public RED evidence and fixes queued for complete regression. No final pair or independent review claimed yet.

Live qwen3.8-27b provider configuration, real browser and user acceptance remain separately incomplete. Controlled fixtures prove deterministic integration, not live model quality or provider compatibility.

## Review corrections, 20:08 UTC

Historical partial plans retain unresolved known-SKU gaps even when their unavailable row was deselected by partial choice; reminder coverage now checks whole requirement against current cart/ledger, without reviving removed target groups. Explicitly abandoned tasks are excluded from automatic reminder, but stay available for intentional source selection.

Recreated dish groups retain protected and public `source_group_id`, and private `people_origin`. Current explicit per-target people map to the corresponding source target; ambiguous multiple unmatched targets clarify. Remembered people remain inferred. A newer explicit task-wide people amendment synchronizes existing group people/provenance, while later specific group revisions can differ. Displayed changes use exact target identity and state target removals, preventing false headcount changes after reordering/removal.

Added public regressions bring TASK11 to 18 cases. Source/current people and deletion/single-dish regression passed 25/25; global override passed 2/2. Final complete regression, both review closures and paired frozen verification are still required. `red-history-group-people` is labeled RED in its directory name but actually contains post-fix GREEN; do not count it as RED.

## Final controlled release, 20:26 UTC

This supersedes earlier pending-validation statements. Mixed-spec source continuity was reproduced with a corrected quantitative public RED and fixed: historical selected pack allocation shares are preference/source data only; current requirement, sale-pack count, price, stock and empty new ledger are recomputed. The first mixed-spec RED had reversed expected pack allocation and is not the valid quantitative RED; `red-history-mixed-specs-02` is valid. Focused mixed+affected regression passed 60/60. Both independent review axes, including the final narrow delta, are closed at `history_service.py 0c72a819` and `purchase_service.py 67179203`.

Dedicated Tester verified final independent pair 182/182 twice, exits 0/0. Four snapshots and current 314 captured files are identical, fingerprint `0f1be6b11ad91dc1cdd881aace1154101fbe6ed29a2787d0357e4ea202e57d53`. History DOM pair, eight affected UI flows and compile/typecheck/build passed on that same map. See `RELEASE.json` and `work/ceres2-runtime-upgrade/11/test-runs/final-history-source-comparison.json`.

Root released controlled technical scope at 20:26 UTC. Overall task remains 待验收. Live qwen3.8-27b provider, real browser and user acceptance remain unverified. Shared guide/runtime/worker/App/saleGuide/purchase ownership transfers to the new TASK16 integration owner; TASK11 has no further application/test edits, commits or pushes pending. See `HANDOFF-P16.md`.
