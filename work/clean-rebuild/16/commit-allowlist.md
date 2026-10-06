# Final local commit allowlist proposal

Read-only audit at 2026-10-05 20:45 UTC, baseline `49ce511`. This document alone was written. No source/test/config edits, test/build execution, staging or commit were performed. Final backend pair is still running; this inventory is a proposed staging boundary, not test acceptance or a security-content certification.

## Decision and dependencies

Use exact individual paths below; never broad `git add .`, `git add work/`, `git add data/`, or `git add backend/`. Existing unchanged tracked files (including frontend locks/assets, design documents and provenance) already belong to checkout and need no restaging.

- Commit application Python, all backend tests, Pi source/config/lock, changed UI, catalog fixtures and all 33 original product images.
- DOM scripts depend on `work/clean-rebuild/02/test-support/package.json` AND its lock. Fresh checkout requires `npm ci --prefix work/clean-rebuild/02/test-support`, as well as production dependencies. Keep original compile/UI scripts; their generated `compiled/` trees are regenerated.
- `work/clean-rebuild/12/order-projection.json` is required by backend checkout test and order DOM harness. Backend test writes/replaces this synthetic artifact during execution, so wait for tests to finish before staging it.
- `final-dom.sh` depends on `work/ceres2-runtime-upgrade/01/test-runs/capture.py`. Both are included explicitly although their parent directory otherwise contains excluded raw runs.
- `work/clean-rebuild/06/import_recipes.py` is a historical reproducible migration utility requiring sibling `../staging/static-catalog/chinese-dishes-v1.json`. Normal runtime/tests use the checked-in recipes fixture and do not need that external source. Do not claim fresh checkout can rerun the historical import without its documented source.
- `.env.example` is listed only as the intentionally public template; no environment file contents were read. Root must verify that the author has kept it placeholder-only before staging. All real/local environment files remain excluded.

## Missing ignore protections

Current `.gitignore` misses `*.sqlite-*` (including WAL/SHM/journal sidecars); an untracked 947,632-byte `business.sqlite-wal` was observed under final-backend-01/pytest-tmp. It also misses work `compiled/`, `pytest-tmp/`, general `test-runs/`, `output.txt`, archive ZIPs and dashboard/live screenshots. Explicit allowlisting handles this commit safely without changing the frozen tree. After the final pair completes, root may add these narrow rules: `*.sqlite-*`, `**/compiled/`, and `work/**/pytest-tmp/`. These do not hide the retained capture/final harnesses or reviewed evidence. Avoid a blanket `test-runs/` rule for now because required scripts and selected evidence live there. Do not blanket-ignore all evidence without preserving intended artifacts.

Exclude work/agent-team (live status/dashboard/screenshot/process tooling), node_modules/.venv/caches, runtime dist/frontend dist, every compiled/ tree, databases and sidecars, output.txt/raw logs, frozen-source-content.zip and tracked*.diff. The source commit makes duplicate full-source ZIP/diffs unnecessary. Archive/reference remain outside this repository and must not be added or linked.

## Evidence finalization

Below, final evidence JSON files record commands, exit status and source hashes without raw output. Their presence alone is not proof of pass. They are being updated by Tester: stage only after the final run finishes and root checks source matching. At snapshot time `final-backend-01/evidence.json` and `final-backend-02/evidence.json` were not yet present; add those exact paths only after their successful completion and review. Keep final reviewed delivery/status files current. Raw historical evidence directories referenced in docs are local-only archives and deliberately omitted from this lean commit; documentation should distinguish these from committed summary evidence.

The exact paths below are text inventory, not an executed git command. Root may add this audit document itself after review. Sizes are filesystem bytes at snapshot time; changing test evidence may differ when staged.

## Core source, fixtures, changed status/docs

194 files; 4,076,879 bytes.

```text
.env.example
AGENTS.md
PROJECT.md
README.md
backend/app/__init__.py
backend/app/api/__init__.py
backend/app/api/bootstrap.py
backend/app/api/cart.py
backend/app/api/catalog.py
backend/app/api/guide.py
backend/app/api/orders.py
backend/app/core/__init__.py
backend/app/core/business_mode.py
backend/app/core/config.py
backend/app/core/database.py
backend/app/core/errors.py
backend/app/core/identity.py
backend/app/human/__init__.py
backend/app/human/models.py
backend/app/human/router.py
backend/app/human/service.py
backend/app/main.py
backend/app/mercury/__init__.py
backend/app/mercury/aftersales.py
backend/app/mercury/aftersales_graph.py
backend/app/mercury/aftersales_models.py
backend/app/mercury/graph.py
backend/app/mercury/models.py
backend/app/mercury/orders.py
backend/app/mercury/policy.py
backend/app/mercury/provider.py
backend/app/mercury/router.py
backend/app/mercury/store.py
backend/app/mercury/tools.py
backend/app/migrations/__init__.py
backend/app/models/__init__.py
backend/app/models/cart.py
backend/app/models/catalog.py
backend/app/models/checkout.py
backend/app/models/comparison.py
backend/app/models/guide.py
backend/app/models/identity.py
backend/app/models/memory.py
backend/app/models/purchase.py
backend/app/models/store.py
backend/app/schemas/__init__.py
backend/app/schemas/history.py
backend/app/schemas/memory.py
backend/app/services/__init__.py
backend/app/services/cart_service.py
backend/app/services/catalog_service.py
backend/app/services/checkout_service.py
backend/app/services/comparison_service.py
backend/app/services/dish_service.py
backend/app/services/guide_lifecycle_service.py
backend/app/services/guide_run_service.py
backend/app/services/history_service.py
backend/app/services/memory_background.py
backend/app/services/memory_model.py
backend/app/services/memory_service.py
backend/app/services/pi_product_runtime.py
backend/app/services/pi_product_turn_service.py
backend/app/services/purchase_service.py
backend/app/services/seed_service.py
backend/app/services/supply_service.py
backend/pyproject.toml
backend/requirements.lock
backend/tests/test_aftersales_migration.py
backend/tests/test_aftersales_proposal_migration.py
backend/tests/test_aftersales_public.py
backend/tests/test_budget_quote_public.py
backend/tests/test_checkout_migration.py
backend/tests/test_checkout_public.py
backend/tests/test_comparison_migration.py
backend/tests/test_comparison_public.py
backend/tests/test_comparison_safety.py
backend/tests/test_dish_public.py
backend/tests/test_foundation_http.py
backend/tests/test_guide_clarification_context.py
backend/tests/test_guide_disconnect.py
backend/tests/test_guide_dish_suggestions.py
backend/tests/test_guide_lifecycle.py
backend/tests/test_guide_migration.py
backend/tests/test_guide_recovery.py
backend/tests/test_guide_semantics.py
backend/tests/test_history_edges.py
backend/tests/test_history_public.py
backend/tests/test_human_public.py
backend/tests/test_integrated_lifecycle.py
backend/tests/test_memory_atomic.py
backend/tests/test_memory_background_cross_role.py
backend/tests/test_memory_background_dream.py
backend/tests/test_memory_background_mercury.py
backend/tests/test_memory_background_models.py
backend/tests/test_memory_background_public.py
backend/tests/test_memory_background_recovery.py
backend/tests/test_memory_background_review.py
backend/tests/test_memory_cross_role.py
backend/tests/test_memory_deletion_fence.py
backend/tests/test_memory_lookup.py
backend/tests/test_memory_mercury.py
backend/tests/test_memory_migration.py
backend/tests/test_memory_mutation_flag.py
backend/tests/test_memory_public.py
backend/tests/test_memory_review_regressions.py
backend/tests/test_memory_wire.py
backend/tests/test_mercury_provider.py
backend/tests/test_mercury_public.py
backend/tests/test_mercury_wire.py
backend/tests/test_multidish_compatibility.py
backend/tests/test_multidish_edges.py
backend/tests/test_multidish_public.py
backend/tests/test_multidish_removed_target.py
backend/tests/test_multidish_selection.py
backend/tests/test_order_case_journey.py
backend/tests/test_purchase_confirmations.py
backend/tests/test_purchase_migration.py
backend/tests/test_purchase_public.py
backend/tests/test_purchase_safety.py
backend/tests/test_runtime_pi_product_query.py
backend/tests/test_supply_edges.py
backend/tests/test_supply_public.py
data/fixtures/offers.json
data/fixtures/product-images.json
data/fixtures/products.json
data/fixtures/recipes.json
data/images/00004069.jpg
data/images/00004612.jpg
data/images/00012683.jpg
data/images/0008112100281.jpg
data/images/0011152094564.jpg
data/images/00159944.jpg
data/images/demo-baking-powder-100g.jpg
data/images/demo-bell-pepper-300g.jpg
data/images/demo-butter-200g.jpg
data/images/demo-cake-flour-250g.jpg
data/images/demo-chicken-breast-500g.jpg
data/images/demo-cooking-oil-500ml.jpg
data/images/demo-cream-cheese-200g.jpg
data/images/demo-eggs-10pack.jpg
data/images/demo-eggs-fresh-6pack.jpg
data/images/demo-flour-all-purpose-500g.jpg
data/images/demo-green-tea-500ml.jpg
data/images/demo-milk-1l.jpg
data/images/demo-noodles-500g.jpg
data/images/demo-peanut-200g.jpg
data/images/demo-pork-500g.jpg
data/images/demo-potato-2d.png
data/images/demo-rice-2kg.jpg
data/images/demo-salt-500g.jpg
data/images/demo-scallion-200g.jpg
data/images/demo-soy-milk-1l.jpg
data/images/demo-soy-sauce-500ml.jpg
data/images/demo-sparkling-water-500ml.jpg
data/images/demo-sugar-white-500g.jpg
data/images/demo-tofu-firm-400g.jpg
data/images/demo-tomato-fresh-500g.jpg
data/images/demo-vanilla-extract-30ml.jpg
data/images/demo-yeast-dry-7g.jpg
frontend/src/AfterSalesPanel.tsx
frontend/src/App.tsx
frontend/src/ComparisonCards.tsx
frontend/src/HumanCasePanel.tsx
frontend/src/HumanOperatorPage.tsx
frontend/src/MercuryChat.tsx
frontend/src/SimulatedOrders.tsx
frontend/src/index.css
frontend/src/lib/aftersales.ts
frontend/src/lib/humanCases.ts
frontend/src/lib/mercury.ts
frontend/src/lib/orders.ts
frontend/src/lib/saleGuide.ts
runtime/pi/package-lock.json
runtime/pi/package.json
runtime/pi/src/worker.ts
runtime/pi/tsconfig.json
tasks/ceres2-runtime-upgrade-01-pi-product-query.md
tasks/ceres2-runtime-upgrade-02-langgraph-aftersales-query.md
tasks/ceres2-runtime-upgrade-03-persistent-responsive-runs.md
tasks/ceres2-runtime-upgrade-04-explicit-cart-confirmation.md
tasks/ceres2-runtime-upgrade-05-single-dish-servings.md
tasks/ceres2-runtime-upgrade-06-multi-dish-demand.md
tasks/ceres2-runtime-upgrade-07-supply-partial-purchase.md
tasks/ceres2-runtime-upgrade-08-category-comparison.md
tasks/ceres2-runtime-upgrade-09-explicit-role-memory.md
tasks/ceres2-runtime-upgrade-10-recoverable-memory-dream.md
tasks/ceres2-runtime-upgrade-11-historical-repurchase.md
tasks/ceres2-runtime-upgrade-12-persistent-simulated-orders.md
tasks/ceres2-runtime-upgrade-13-canonical-order-aftersales.md
tasks/ceres2-runtime-upgrade-14-confirmed-aftersales-receipts.md
tasks/ceres2-runtime-upgrade-15-async-human-cases.md
tasks/ceres2-runtime-upgrade-16-integrated-verification.md
tasks/ceres2-upgrade.md
work/clean-rebuild/README.md
```

## Harnesses and bounded handoff/provenance docs

111 files; 633,757 bytes.

```text
work/ceres2-runtime-upgrade/01/test-runs/capture.py
work/ceres2-runtime-upgrade/12/implementation.md
work/ceres2-runtime-upgrade/12/release-source-manifest.json
work/ceres2-runtime-upgrade/12/task13-handoff.md
work/ceres2-runtime-upgrade/16/test-runs/final-dom.sh
work/clean-rebuild/01/CONSUMED-FOUNDATION.json
work/clean-rebuild/01/CONTRACT.md
work/clean-rebuild/01/HANDOFF-P03.md
work/clean-rebuild/01/MIGRATION.md
work/clean-rebuild/01/RELEASE.json
work/clean-rebuild/02/compile_ui_races.cjs
work/clean-rebuild/02/design.md
work/clean-rebuild/02/handoff.md
work/clean-rebuild/02/provenance.json
work/clean-rebuild/02/release-source-manifest.json
work/clean-rebuild/02/test-support/package-lock.json
work/clean-rebuild/02/test-support/package.json
work/clean-rebuild/02/ui_races.tsx
work/clean-rebuild/03/CONSUMED-FOUNDATION.json
work/clean-rebuild/03/HANDOFF-P04.md
work/clean-rebuild/03/INITIAL-SOURCE.sha256
work/clean-rebuild/03/README.md
work/clean-rebuild/03/RELEASE.json
work/clean-rebuild/03/compile_ui.cjs
work/clean-rebuild/03/ui_guide.mjs
work/clean-rebuild/03/ui_operator_route.mjs
work/clean-rebuild/04-purchase/FINAL-CANDIDATE.json
work/clean-rebuild/04-purchase/HANDOFF-P05-P08.md
work/clean-rebuild/04-purchase/POST-PAIR-DELTA.json
work/clean-rebuild/04-purchase/README.md
work/clean-rebuild/04-purchase/RELEASE.json
work/clean-rebuild/04-purchase/REVIEW-SOURCE.json
work/clean-rebuild/04-purchase/compile_ui.cjs
work/clean-rebuild/04-purchase/review-closures.md
work/clean-rebuild/04-purchase/ui_purchase.mjs
work/clean-rebuild/04-purchase/ui_purchase_background_refresh.mjs
work/clean-rebuild/04-purchase/ui_purchase_lost_response.mjs
work/clean-rebuild/05/FINAL-CANDIDATE.json
work/clean-rebuild/05/HANDOFF.md
work/clean-rebuild/05/RELEASE.json
work/clean-rebuild/05/recipe-provenance.json
work/clean-rebuild/05/review-closures.md
work/clean-rebuild/05/ui_dish.mjs
work/clean-rebuild/06/FINAL-CANDIDATE.json
work/clean-rebuild/06/HANDOFF.md
work/clean-rebuild/06/RELEASE.json
work/clean-rebuild/06/design.md
work/clean-rebuild/06/import_recipes.py
work/clean-rebuild/06/progress.md
work/clean-rebuild/06/recipe-provenance.json
work/clean-rebuild/06/review-source-manifest.json
work/clean-rebuild/06/ui_group_ledger.mjs
work/clean-rebuild/06/ui_multidish.mjs
work/clean-rebuild/07/HANDOFF.md
work/clean-rebuild/07/progress.md
work/clean-rebuild/07/ui_alternative.mjs
work/clean-rebuild/07/ui_supply.mjs
work/clean-rebuild/08-comparison/HANDOFF.md
work/clean-rebuild/08-comparison/INTEGRATION.md
work/clean-rebuild/08-comparison/RELEASE.json
work/clean-rebuild/08-comparison/REVIEW-FIXES.md
work/clean-rebuild/08-comparison/REVIEW.md
work/clean-rebuild/08-comparison/ui_comparison.mjs
work/clean-rebuild/08-comparison/ui_comparison_order.mjs
work/clean-rebuild/09/HANDOFF-P10.md
work/clean-rebuild/09/README.md
work/clean-rebuild/09/release-source-manifest.json
work/clean-rebuild/10/HANDOFF-P16.md
work/clean-rebuild/10/README.md
work/clean-rebuild/10/release-source-manifest.json
work/clean-rebuild/11/HANDOFF-P16.md
work/clean-rebuild/11/HANDOFF.md
work/clean-rebuild/11/RELEASE.json
work/clean-rebuild/11/progress.md
work/clean-rebuild/11/ui_history.mjs
work/clean-rebuild/12/compile_ui.cjs
work/clean-rebuild/12/order-projection.json
work/clean-rebuild/12/ui_orders.mjs
work/clean-rebuild/13/compile_ui_contact.cjs
work/clean-rebuild/13/design.md
work/clean-rebuild/13/handoff.md
work/clean-rebuild/13/identity_race.mjs
work/clean-rebuild/13/release-source-manifest.json
work/clean-rebuild/13/review-source-manifest.json
work/clean-rebuild/13/ui_contact.tsx
work/clean-rebuild/14/compile_ui.cjs
work/clean-rebuild/14/concurrent-intent-review-source-manifest.json
work/clean-rebuild/14/handoff.md
work/clean-rebuild/14/release-source-manifest.json
work/clean-rebuild/14/replacement-review-source-manifest.json
work/clean-rebuild/14/review-source-manifest.json
work/clean-rebuild/14/ui_aftersales.mjs
work/clean-rebuild/15/compile_ui_human.cjs
work/clean-rebuild/15/handoff.md
work/clean-rebuild/15/release-source-manifest.json
work/clean-rebuild/15/ui_human.tsx
work/clean-rebuild/16/APP-SNAPSHOT-HANDOFF.md
work/clean-rebuild/16/CLARIFICATION-DISH-HANDOFF.md
work/clean-rebuild/16/DELIVERY.md
work/clean-rebuild/16/ui_plan_controls.mjs
work/clean-rebuild/16/ui_snapshot_ordering.mjs
work/clean-rebuild/16/verification-map.md
work/clean-rebuild/baseline-files.json
work/clean-rebuild/migration-ledger.md
work/clean-rebuild/provenance.json
work/clean-rebuild/purchase-contract-map.md
work/clean-rebuild/shared-release-manifest.json
work/clean-rebuild/static-catalog/README.md
work/clean-rebuild/static-catalog/assets-manifest.json
work/clean-rebuild/static-catalog/image-recovery.json
work/clean-rebuild/static-catalog/verification.json
```

## Final metadata evidence (provisional until Tester completes)

51 files; 3,321,243 bytes.

```text
work/ceres2-runtime-upgrade/16/test-runs/final-04-purchase-ui_purchase/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-04-purchase-ui_purchase_background_refresh/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-04-purchase-ui_purchase_lost_response/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-05-ui_dish/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-06-ui_group_ledger/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-06-ui_multidish/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-07-ui_alternative/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-07-ui_supply/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-08-comparison-ui_comparison/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-11-ui_history/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-comparison-order-error/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-comparison-order-reconnect/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-comparison-order-success/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-compile-02/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-compile-03/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-compile-12/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-compile-13/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-compile-14/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-compile-15/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-compile-shopping/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-dom-02/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-dom-12/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-dom-13/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-dom-14/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-dom-15/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-frontend-build/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-frontend-typecheck/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-guide-default/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-guide-initial-compile/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-guide-interrupted/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-guide-late-init/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-guide-task-abandoned/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-identity/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-operator-route/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-pip-check/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-runtime-build/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-runtime-typecheck/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-ui_plan_controls-budget-1/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-ui_plan_controls-budget-2/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-ui_plan_controls-default-1/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-ui_plan_controls-default-2/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-ui_snapshot_ordering-cards-1/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-ui_snapshot_ordering-cards-2/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-ui_snapshot_ordering-default-1/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/final-ui_snapshot_ordering-default-2/evidence.json
work/ceres2-runtime-upgrade/16/test-runs/inventory/configuration-clock-scope.json
work/ceres2-runtime-upgrade/16/test-runs/inventory/dependency-data-audit.json
work/ceres2-runtime-upgrade/16/test-runs/inventory/fresh-schema-seed.json
work/ceres2-runtime-upgrade/16/test-runs/inventory/frontend-installed.json
work/ceres2-runtime-upgrade/16/test-runs/inventory/frozen-source-manifest.json
work/ceres2-runtime-upgrade/16/test-runs/inventory/runtime-installed.json
```

Total proposed paths: 356 files; 8,031,879 bytes, excluding this document and pending backend-pair evidence.
