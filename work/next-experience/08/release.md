# TASK08 controlled implementation handoff

Implementation candidate: `3cdb3816680c59714c366ad8ce173c4b9a58eebc`, including the released TASK04, TASK05 and TASK09 integration source. This note does not set the canonical TASK status or claim user acceptance.

## Delivered

- The existing homepage card enters Keke through a typed activity request rather than sending an invented recipe request. Its existing design is retained; its subtitle explicitly describes demo finished products.
- One fixed, host-owned `light-meal` task scope bounds finished salad, fruit-platter and juice supply. Current budget, quantity, dietary restrictions and exclusions survive entry; prior category/type/query/dish/history selection fields do not leak into the new goal.
- The existing message-backed product question, Pi selection references, comparison projection, purchase plan and separate versioned confirmation remain authoritative. Users can select different products/quantities; there is no fixed bundle or ingredient decomposition.
- Read-only exploration is reused for activity raw search and comparison, including model calls that omit semantic routing. Product details recheck current eligibility, recipe tools reject expansion while scoped, and final purchase facts recheck activity membership alongside price, stock, dietary and drink-filter requirements.
- Arbitrary task-condition writes cannot clear the host-owned scope. Existing explicit `new_goal` or `abandon` transitions remain available and invalidate prior choices while preserving the cart/history.
- Entry task creation, question publication and replay receipt commit together through the existing lifecycle authority. No new workflow table or business-write authority was added.
- The App keeps newer navigation authoritative if an activity response arrives late. Busy/error/retry display is retained without automatic text routing.

## Public contract

`POST /api/v1/guide/sessions/{session_id}/activities/light-meal`

Body: `request_id`, nullable `expected_task_id`, `expected_state_version`, `expected_session_version`. Response: the existing complete guide projection, including current conditions, messages and question history. Owner/canonical-session checks, anchor validation and existing command receipts apply. Reusing a request with different content is rejected.

`activity_id` is reserved to the host entry, not a model/client-controlled filter. Product eligibility requires matching `metadata.activity_ids` and `finished_product: true`. See [fixture manifest](fixture-manifest.md) for the three explicitly simulated AC records. The composed catalogue has 70 records; the ordinary drink-type fixture gains a sixth label, 果汁, because of approved supply expansion, not model improvement.

Shared ownership: TASK03 authored the App hookup/navigation fence, TASK05 authored the narrow Python Pi activity callback adapter, the integrator registered the API router, and TASK01/root approved shared question/lifecycle/purchase/comparison hunks. TASK04 drink filters and all source records were preserved during composition.

## Final frozen controlled evidence

Designated Tester verified unchanged source at candidate `3cdb381`:

- `work/next-experience/10/runs/next08-composed05-public`: 82/82 scoped public tests pass, 68.60s. Includes activity, snack/drink, lifecycle, comparison, purchase, foundation and composed TASK05/TASK09 checks.
- `work/next-experience/10/checks/next08-composed05-runtime`: runtime typecheck and build pass.
- `work/next-experience/10/checks/next08-composed05-ui`: frontend strict typecheck/build and four controlled actual-App DOM journeys pass: activity entry/selection/explicit confirmation, interrupted activity navigation, drink filters and snack choices.

The 16 activity cases cover bounded typed entry/replay, actual Pi raw-search scope, comparison hard dietary constraints, host-owned scope and explicit exit, two different finished-product compositions with one Kev decision each, separate idempotent cart confirmation, price/stock/membership changes, budget/quantity/exclusion/unknown dietary restrictions, recipe rejection and repeat-seed/stale-supply behavior.

Earlier RED/GREEN evidence remains separate: `next08-red-01` → `next08-green-01`; corrected raw-search projection RED `next08-red-02-corrected` → `next08-green-02`; comparison hard-constraint RED `next08-red-03` → `next08-comparison-green-scope-red`; host-scope protection → `next08-green-04`; App entry and late-navigation RED → corresponding DOM GREEN captures. The first raw-search RED used the wrong projection field and is not defect proof. Initial broad failures were corrected test fixture/contracts, not relaxed commerce protection: the synthetic pi-store cart was replaced by normal public demo-cart initialization, the recipe assertion follows the existing SSE `error` event, and exact fixture counts/labels reflect approved AC additions.

## Remaining gates

These are controlled HTTP/SSE/actual-Pi-with-loopback-provider and actual-App DOM results. They are not live Kev/main-model quality results, real-browser layout/click evidence, natural-language review, full-suite regression or user acceptance. No real credentials, `.env`, live provider calls, remote push or old runtime state were used. TASK06 may later change the shared expression stage; its composed candidate needs fresh affected verification rather than inheriting this source's result.
