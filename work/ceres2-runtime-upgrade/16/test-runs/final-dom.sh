#!/bin/bash
set -u
C=".venv/bin/python work/ceres2-runtime-upgrade/01/test-runs/capture.py"
export MERCURY_TEST_SUPPORT="$PWD/work/clean-rebuild/02/test-support"
$C 16/test-runs/final-guide-initial-compile node work/clean-rebuild/03/compile_ui.cjs
export MERCURY_COMPILED_DIR="$PWD/work/clean-rebuild/02/compiled"
$C 16/test-runs/final-compile-02 node work/clean-rebuild/02/compile_ui_races.cjs
$C 16/test-runs/final-dom-02 node "$MERCURY_COMPILED_DIR/ui_races.mjs"
export MERCURY_COMPILED_DIR="$PWD/work/clean-rebuild/13/compiled"
$C 16/test-runs/final-compile-13 node work/clean-rebuild/13/compile_ui_contact.cjs
$C 16/test-runs/final-dom-13 node "$MERCURY_COMPILED_DIR/ui_contact.mjs"
$C 16/test-runs/final-identity node work/clean-rebuild/13/identity_race.mjs
export MERCURY_COMPILED_DIR="$PWD/work/clean-rebuild/15/compiled"
$C 16/test-runs/final-compile-15 node work/clean-rebuild/15/compile_ui_human.cjs
$C 16/test-runs/final-dom-15 node "$MERCURY_COMPILED_DIR/ui_human.mjs"
$C 16/test-runs/final-compile-12 node work/clean-rebuild/12/compile_ui.cjs
$C 16/test-runs/final-dom-12 node work/clean-rebuild/12/ui_orders.mjs
$C 16/test-runs/final-compile-14 node work/clean-rebuild/14/compile_ui.cjs
$C 16/test-runs/final-dom-14 node work/clean-rebuild/14/ui_aftersales.mjs
$C 16/test-runs/final-operator-route node work/clean-rebuild/03/ui_operator_route.mjs
GUIDE_UI_CASE=late-init $C 16/test-runs/final-guide-late-init node work/clean-rebuild/03/ui_guide.mjs
GUIDE_UI_CASE=interrupted $C 16/test-runs/final-guide-interrupted node work/clean-rebuild/03/ui_guide.mjs
GUIDE_UI_CASE=task-abandoned $C 16/test-runs/final-guide-task-abandoned node work/clean-rebuild/03/ui_guide.mjs

$C 16/test-runs/final-compile-03 node work/clean-rebuild/03/compile_ui.cjs
$C 16/test-runs/final-guide-default node work/clean-rebuild/03/ui_guide.mjs
$C 16/test-runs/final-compile-shopping node work/clean-rebuild/04-purchase/compile_ui.cjs
$C 16/test-runs/final-04-purchase-ui_purchase node work/clean-rebuild/04-purchase/ui_purchase.mjs
$C 16/test-runs/final-04-purchase-ui_purchase_background_refresh node work/clean-rebuild/04-purchase/ui_purchase_background_refresh.mjs
$C 16/test-runs/final-04-purchase-ui_purchase_lost_response node work/clean-rebuild/04-purchase/ui_purchase_lost_response.mjs
$C 16/test-runs/final-05-ui_dish node work/clean-rebuild/05/ui_dish.mjs
$C 16/test-runs/final-06-ui_multidish node work/clean-rebuild/06/ui_multidish.mjs
$C 16/test-runs/final-06-ui_group_ledger node work/clean-rebuild/06/ui_group_ledger.mjs
$C 16/test-runs/final-07-ui_supply node work/clean-rebuild/07/ui_supply.mjs
$C 16/test-runs/final-07-ui_alternative node work/clean-rebuild/07/ui_alternative.mjs
$C 16/test-runs/final-08-comparison-ui_comparison node work/clean-rebuild/08-comparison/ui_comparison.mjs
$C 16/test-runs/final-11-ui_history node work/clean-rebuild/11/ui_history.mjs
$C 16/test-runs/final-comparison-order-error node work/clean-rebuild/08-comparison/ui_comparison_order.mjs error
$C 16/test-runs/final-comparison-order-success node work/clean-rebuild/08-comparison/ui_comparison_order.mjs success
$C 16/test-runs/final-comparison-order-reconnect node work/clean-rebuild/08-comparison/ui_comparison_order.mjs reconnect
$C 16/test-runs/final-ui_snapshot_ordering-default-1 node work/clean-rebuild/16/ui_snapshot_ordering.mjs
$C 16/test-runs/final-ui_snapshot_ordering-cards-1 node work/clean-rebuild/16/ui_snapshot_ordering.mjs cards
$C 16/test-runs/final-ui_plan_controls-default-1 node work/clean-rebuild/16/ui_plan_controls.mjs
$C 16/test-runs/final-ui_plan_controls-budget-1 node work/clean-rebuild/16/ui_plan_controls.mjs budget
$C 16/test-runs/final-ui_snapshot_ordering-default-2 node work/clean-rebuild/16/ui_snapshot_ordering.mjs
$C 16/test-runs/final-ui_snapshot_ordering-cards-2 node work/clean-rebuild/16/ui_snapshot_ordering.mjs cards
$C 16/test-runs/final-ui_plan_controls-default-2 node work/clean-rebuild/16/ui_plan_controls.mjs
$C 16/test-runs/final-ui_plan_controls-budget-2 node work/clean-rebuild/16/ui_plan_controls.mjs budget
$C 16/test-runs/final-frontend-typecheck frontend/node_modules/.bin/tsc -p frontend/tsconfig.json --noEmit
$C 16/test-runs/final-frontend-build npm --prefix frontend run build
