# Bounded clarification and dish suggestions

Scope: final TASK03/16 Spec corrections. Root owns commits; no push. This work changed only the agreed Pi turn/runtime/worker files, the guide session projection (transferred by final integration owner), and two new public-behavior test files. Tester alone executed tests, runtime typecheck, and builds.

## Behavior

- A waiting result persists a canonical supported clarification slot and its host-authored question in the existing durable receipt. Session reload and idempotent replay expose the same question.
- Pi receives one bounded current question, with task/session/state equality checked by the host. No raw shopping transcript, previous user instruction, memory CRUD output, deleted memory text, or historical authorization is copied.
- The latest committed assistant-message receipt supplies that projection. A concurrent admitted run cannot hide it. Completed unrelated questions/progress preserve the current projection within the final transaction; related answers, explicit stop, protected termination, and changed task/version retire it.
- Dish suggestions use current queried recipe references and host-rendered numbered names, with no plan or cart write. Only five suggestions are retained as recipe IDs/names. A later ordinal selection is interpreted against these names and re-queries current recipe facts before preparing a plan.
- Recipe absence requires actual recipe-search evidence. Found recipes with no selected display refs are described as unselected, not absent.
- Newly prepared purchase/history plans persist `waiting_confirmation` run status. Existing plan/quote/supply data determines which user decision is needed; no new cart authority is granted.
- Existing receipt JSON and message sequence provide persistence, so no schema or migration is needed.

## Public verification

Tests use public HTTP/SSE with the actual Node Pi SDK and an isolated deterministic HTTP model boundary. They do not claim live provider/model or user acceptance.

- Initial RED: `red-clarification-context` (2 failed, 1 passed), `red-dish-suggestions` (1 failed, 1 passed).
- Initial GREEN: actual runtime typecheck/build; `green-context-suggestions` (5 passed).
- Independent Spec review found interruption/admission continuity and empty-recipe evidence gaps. RED: `red-context-continuity` (3 failed), `red-context-admission` (1 failed).
- Reviewed GREEN: `green-context-reviewed` (12 passed, stable source).
- Factual wording RED: `red-empty-dish-selection` (1 failed). Final `green-context-final`: 13 passed, exit 0, identical before/after captured source. Independent final Spec source review closed all findings at runtime SHA 21cf8470; broader full integration verification remains with Tester.

Evidence directories are under `work/ceres2-runtime-upgrade/16/test-runs/`.

## Frozen source SHA-256

- backend/app/services/pi_product_runtime.py: 21cf8470809d8ec3a23904612d0291b7fbc8dd6e98c63d618b745c571ce1d88c
- backend/app/services/pi_product_turn_service.py: 8530e14da8a692ef27e84383fed145c5ee31151d95027b822dd46496fd946e57
- runtime/pi/src/worker.ts: 83865f2fe95fd91f0e29065fc6fb56829fdf9e6aca92c2cd8008faaa1bfd65c3
- backend/app/api/guide.py: 8d330e1ef611379c508e6a482139e4ba94a043ca4be771e7cfbea2981e4b13fc (includes integration owner's earlier edits)
- backend/tests/test_guide_clarification_context.py: 360c76b4edb7dab4ff9219dd952721eee0da9714264de81a770e08beeaf3e415
- backend/tests/test_guide_dish_suggestions.py: 941b998788a932a29c103943e0d575e1c833a097a2c2b699439ae2280c3e418b
