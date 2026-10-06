# TASK16 integrated delivery and manual verification

Final controlled integration verified 2026-10-05 20:58 UTC. **294/294 backend cases passed twice on the same frozen source; all 45 final DOM/build/typecheck/pip command records passed on that source. Independent Standards and Spec source reviews have zero remaining actionable findings.** Root confirmed this controlled technical result. TASK16 remains blocked/awaiting acceptance for actual qwen, real browser and user experience. No overall acceptance is claimed. Root owns commits; no push. Review corrections reuse existing state/transaction boundaries, with no new schema.

## Final evidence

- Full backend: `work/ceres2-runtime-upgrade/16/test-runs/final-backend-01/` and `final-backend-02/`; 294/294 twice, exit 0/0, 369.68s and 368.93s. Each run used a separate fresh pytest base directory.
- Exact applicability: `final-integrated-source-comparison.json` in the same test-runs directory verifies four matching before/after maps, matching frozen inventory/current **320 files**, zero current mismatches, and fingerprint `b711e091dd35bd646062946a76c1f57b4e514f6a243eb1a9efe917874b63b6ba`.
- The comparison file lists all **45** matched final command records, including freshly compiled current component DOM journeys, snapshot ordering, budget/quantity controls, frontend/Pi typecheck/build and pip check. These are controlled DOM checks, not a real browser.
- `inventory/dependency-data-audit.json`: Python installed freeze matches lock; frontend 49 and runtime 87 installed package resolutions match their locks; no archive/reference runtime links. Fixture/image hashes retained; standalone retrieval index is not applicable because current catalog lookup is SQL.
- `inventory/fresh-schema-seed.json`: fresh isolated schema has 28 tables and 9 migration markers; explicit static import yields 65 catalog products/65 Offers/one store, with zero old business users/orders/carts/applications. Repeated initialization/seed preserve counts and deliberately changed Offer price/version. Synthetic pre-upgrade, repeated-upgrade and safe fact-preserving rollback tests are also in both full backend runs.
- `inventory/configuration-clock-scope.json`: exact source configuration/data scope, temporary DB/checkpoint isolation and clock limits. `inventory/frozen-source-manifest.json` plus content ZIP preserves the tested tree including untracked source. Installed resolutions, versions, tracked diff and status are alongside them. No secrets were captured.
- `final-review-closure.md`: separately attributed final Standards/Spec source conclusions and exact reviewed hashes. Review is not test execution; Tester supplied the execution evidence above.



## New controlled integration fixture

`backend/tests/test_integrated_lifecycle.py` reuses the released actual-Pi HTTP fixture. Every invocation creates its own temporary business SQLite file, checkpoint and two synthetic owners. It constructs only the existing minimal beverage catalog plus a six-can package; no old DB, session, cart, order, index, key or checkpoint is imported. The selected package is one unit, 1,980 ml, 1,800 fen. Domain time is `2026-10-05T12:00:00Z` for checkout creation, human correspondence and aftersales eligibility; runtime admission, cancellation and monotonic limits deliberately use real time. ORM metadata timestamps and other existing suites are not claimed globally frozen.

The Pi provider is the local controlled HTTP fixture (`controlled-pi`); Mercury's model boundary is a controlled proposal response. Installed Pi SDK, Node worker, LangGraph, SqliteSaver, Python business services and real SQL transactions execute normally. This proves deterministic integration, not qwen compatibility, autonomous model quality or live timing.

Three cases cover:

1. Public comparison → displayed candidate selection → plan with empty cart → stopped in-flight Pi query preserving the plan → exact separate cart confirmation → checkout preview/confirmation/replay → canonical same-order selection → model-driven actual LangGraph proposal without receipt → explicit confirmation with postcommit response loss → durable receipt → repeat initialization → checkpoint loss → reconstructed application/router public read and replay. Original order snapshot and empty post-checkout cart survive; second owner cannot read case/order/receipt or confirm.
2. Public human acquisition wins while an actual confirmation request is paused at the approved submit interface. The resumed submit is denied, operator correspondence does not write an application, closing does not restore old consent, and a new proposal plus fresh explicit confirmation succeeds.
3. Actual submit commits first while its response is paused. Public human acquisition preserves the already committed factual receipt, operator reply/close does not submit again, and old-key replay returns that same receipt. Repeat initialization preserves closed ticket and application receipt.

The race injection is immediately before or after the **actual** `AfterSalesService.submit` UoW. It establishes the two linearized boundary orderings; it does not claim a scheduler stress test of every internal interleaving. Restart reconstructs application/router/graph access without lifespan; dedicated existing recovery tests separately exercise startup-managed workers and run interruption.

Initial 3/3 pre-stop-extension evidence: `work/ceres2-runtime-upgrade/16/test-runs/integrated-lifecycle-first/`. This is provisional, not the final paired source. The new journeys initially passed, so no artificial RED or production fix is claimed.

## Final-review corrections verified

- Budget negotiation: final Spec review found over-budget preparation raised a generic error before showing an actual counteroffer. Public `red-budget-quote` reproduced it. Preparations and revisions now retain current budget and project exact `budget_quote {budget_fen,total_fen}`, with confirmation disabled. Explicit version-bound `accept_quote` verifies current quote/Offer/delivery and updates only the task budget and plan revision; cart confirmation remains a separate action. Price/stock changes reject the old quote. Supply selection remains independent, and later expansion still obeys the accepted budget. The 3 quote cases and affected purchase/dish/supply regression passed 60/60 in `green-budget-regression` (exploratory because other approved files changed concurrently). Both backend review axes reported no remaining quote finding. The App quote control and row quantity control have controlled DOM GREEN; exact UI evidence and snapshot ordering closure are in `APP-SNAPSHOT-HANDOFF.md`. The final 294-case pair and matched UI checks now cover this correction. Four old preparation tests were changed to assert factual quote, unchanged budget and no cart write rather than generic refusal; confirmation safeguards were not removed.
- Responsive UI snapshot ordering now rejects older same-session authoritative snapshots, including task replacement and candidate evidence. Its two delayed-response DOM RED→GREEN cases, quote/quantity controls, typecheck/build and Standards closure are recorded in `APP-SNAPSHOT-HANDOFF.md`. Bounded clarification/dish-candidate context and truthful waiting_confirmation are complete with public RED→GREEN and final 13/13 stable focused verification, documented in `CLARIFICATION-DISH-HANDOFF.md`. Source-only Spec and Standards reviews closed; the final full frozen pair now covers these corrections.
- Fresh DOM execution exposed stale historical harnesses: TASK03 omitted current `ComparisonCards.tsx` compile input; TASK12 called current order component without `onContactOrder` and expected obsolete local selection text. The harnesses now compile the actual dependency and assert the exact canonical order callback. Tester rechecks passed; no production behavior was changed for these harness repairs.

## Existing released coverage retained in the final suite

- `test_history_public.py::test_history_rebuilds_current_multidish_supply_then_requires_new_confirmation` already supplies the entire second required journey: historical two-dish plan → current people/price/zero egg stock → supply preview → explicit partial-choice → fresh confirmation/replay → unchanged source plan. TASK16 does not duplicate it. `test_history_edges.py` retains mixed-spec provenance/current supply, user isolation, reminder refusal and protected memory/default cases.
- `test_memory_background_public.py` already connects completed Pi shopping replies with durable background extraction, public memory reads, ten-record Dream threshold/24-hour cooldown, explicit deletion and application restart. `test_memory_background_recovery.py`, `test_memory_background_dream.py` and deletion/review regressions retain leases, correction, expiry and no-resurrection behavior. Their controlled models are distinct from live qwen.
- `test_guide_disconnect.py` uses actual local HTTP/SSE disconnect and replay; guide lifecycle/recovery tests cover public run state and interruption. The new journey interleaves a real explicit stop. None of these is real-browser page-close evidence.
- Existing purchase/checkout/aftersales UoW suites retain precommit rollback, postcommit response loss, conflict/replay and concurrent mutation checks. Existing migration suites retain fresh and synthetic pre-upgrade schema/fact checks; TASK16 adds repeated initialization after actual integrated writes. No new state means no TASK16 migration is needed.
- All applicable controlled DOM harnesses must be recompiled from final source before execution. A JSDOM pass proves component/client behavior only; layouts, actual browser interaction and browser SSE remain separate.

The dated `verification-map.md` remains preparation history. Use the final Tester evidence and root release record for the actual final scope, command/exit codes, source manifests, full pair counts, schema/seed/dependency checks and reviewer closures. Do not combine successful runs from different source versions into one pair.

## Still unverified / externally blocked

- Actual `qwen3.8-27b` on all four model paths: Pi, Mercury, extraction and Dream. Secure provider configuration is not available. Never use pasted chat keys, copied old `.env` contents, another model, or the controlled fixture as a substitute.
- Actual browser: the previously permitted localhost path returned `ERR_BLOCKED_BY_CLIENT`; shell Chromium returned `EPERM`. No bypass or new browser pass is claimed. Need a permitted working browser path.
- User's own experience and acceptance remain pending separately. Simulated prices, inventory, checkout, refunds and fulfillment are never real transactions.
- No project-owned controlled integration blocker remains in the reviewed/tested scope. This does not establish live model quality, real browser behavior, every possible production interleaving or user acceptance.

## Reproduce controlled verification (Tester only during collaboration)

From project root create a **new**, previously unused absolute run directory for each execution. Set `DATABASE_URL=sqlite:///<absolute-run>/business.sqlite3`, `MERCURY_CHECKPOINT_PATH=<absolute-run>/checkpoints.sqlite3`, `PYTHONPATH=<project-root>/backend` and `PYTHONDONTWRITEBYTECODE=1` before imports or test collection. Do not display the whole environment. The fixture overrides only its own temporary resources and local controlled provider.

- Targeted bridge: `.venv/bin/python -m pytest backend/tests/test_integrated_lifecycle.py -q`
- Required same-final-source pair: `.venv/bin/python -m pytest backend/tests -q`, twice with independent fresh isolation and matching before/after consumed-source manifests.
- Pi: `cd runtime/pi && npm run typecheck && npm run build`
- Frontend: `cd frontend && npx tsc --noEmit && npm run build`
- Fresh compiled DOM: use each owning `work/clean-rebuild` compile script and matching UI script listed in the final Tester inventory. Do not run cached old bundles or label this browser E2E.

Use only this project's locked `.venv` and node_modules, never sibling archive/reference dependencies. Follow README for clean installation by the Tester if rebuilding is required. Seed is explicit and idempotent; actual old databases are forbidden. The checked-in catalog SQL lookup has no separate vector-index build to claim.

## Manual live experience when the gates are available

1. Choose a fresh absolute business DB/checkpoint directory. Set both paths before seed or backend startup. Do not reuse archived data. Install project-locked dependencies and build Pi as in README. Run the explicit catalog seed; it creates only missing static catalog/Offer/store facts, not prior users or orders.
2. Securely configure `LLM_MODE=live`, the correct OpenAI-compatible endpoint and provider credential; set `LLM_MODEL`, `MEMORY_EXTRACTION_MODEL` and `MEMORY_DREAM_MODEL` to `qwen3.8-27b`. Set a distinct `HUMAN_OPERATOR_TOKEN` only if exercising the operator page. A model key must never be used as an operator credential. Do not paste secrets into chat or evidence logs.
3. In `backend/`, start `../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8012`. Separately in `frontend/`, run `npm run dev` (current configured port 8443, API/media proxy to 8012). Check `/health` then bootstrap via the normal page. Coordinate occupied ports rather than killing unknown processes.
4. In a permitted actual browser, browse normally, then open 可可. Ask to compare current drinks, inspect real candidate attributes/unknown fields, choose one and inspect its prepared quantity/price. If over budget, inspect the actual quote; explicitly accept it only if desired, then verify the budget changed while the cart stayed unchanged. Confirm cart addition separately; check exact cart contents. Simulate checkout, then open that exact order through the independent 墨墨 entry.
5. Ask for an eligible unshipped whole-order refund. Review order, quantity, amount, reason and policy; before confirming, verify no application receipt. Confirm, then refresh/reopen and verify one simulated requested receipt, never approved/refunded wording.
6. Prepare a multi-dish plan, then start a new task and intentionally choose the historical source. Change people/budget/exclusions. For deterministic shortage exercise use only the controlled isolated fixture/test; there is no unapproved ordinary-user stock mutation screen. Observe current-supply preview, choose available items, then separately confirm. Old history and old approval must not become current authorization.
7. On a fresh eligible order, request human support with a pending proposal. Open `/operator/human-cases` with the separate operator credential; reply/ask and close. User sees progress. Agent writes are held during responsibility; the old proposal remains invalid after close. Prepare and explicitly confirm a new proposal. Deterministic in-flight orderings belong to the controlled test above, not a manual timing claim.
8. During guide exploration press stop, then verify the shopping task/plan/cart remain. Separately close/reopen the actual page while work runs; check durable result recovery and absence of duplicate writes. Record actual browser behavior rather than inferring it from HTTP tests.
9. Ask to remember, list, correct and delete a shopping fact. Observe extraction only after a committed reply and check that deleted facts do not reappear after restart. Ten-record/24-hour/30-day clock boundaries are deterministic controlled tests unless actually exercised live; do not claim them from a brief manual session.

Record source/build hashes, fixture/Offer versions, secure model identity (no key), prompts, UTC timing, final outcome and exact business receipt for each live case. Distinguish natural completion, waiting, stopped, failed and 5-round/15-second protective termination; protection is not task success. User acceptance is a separate recorded decision.

## Safe hold / rollback

`SHOPPING_WRITES_PAUSED=true` holds only cart/checkout mutations, not all writers. After new orders/applications/receipts/tickets exist, stop the application and background writers, retain the upgraded DB and checkpoint, and inspect business facts through SQLite URI `mode=ro`. Never restore an older backup over committed facts, drop receipt/ticket tables, silently release human holds or re-enable legacy unconfirmed writes.
