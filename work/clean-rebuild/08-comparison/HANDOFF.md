# TASK08 category comparison handoff

## Implementation and authority

The comparison model/service belongs to TASK08. Shared guide API, turn coordinator, actual Pi worker/runtime, App and saleGuide are uniquely integrated by TASK05. Foundation registers the additive ComparisonDisplay model and 0008_category_comparison marker. No legacy database, runtime implementation or credentials were imported.

ComparisonService reads the canonical catalog and current store Offers. Page category plus current task brand, packaging, pack-count, budget and exclusions are applied before limiting display to five candidates. The whole sale package is spec_quantity/spec_unit; metadata pack_count never multiplies it again. Missing brand, packaging, pack count and per-item volume remain null. Non-volume/unknown package amounts have no per-litre quote. Monetary source is integer fen; yuan/litre = fen * 10 / package ml.

The actual Pi compare_products tool returns run-local factual refs. Final comparison creates no plan/cart. Host publication mints a bounded current displayed snapshot with owner/session/task/session-version/state-version/page/store/zone and persisted message association. Explicit displayed-candidate selection in a later actual Pi turn resolves that snapshot back to current canonical SKU facts and enters existing PurchaseService.prepare. Selection still does not add to cart; TASK04 explicit confirmation remains required.

Persisted candidate provenance survives repeated propose calls. The final host transaction re-resolves the candidate before plan preparation, so a concurrent replacement invalidates an old in-flight selection. Provider failures and protected deadline/tool-budget closes retire the prior displayed set only if that exact set remains current; a late failure cannot erase newer comparison cards. App completion/reconnect merges use current authoritative refs, and late UI errors remove only the failed request’s captured refs.

The retained glass-style chat cards show factual brand, packaging, package count, whole-package specification and per-litre quote with explicit unknown values. Chips preserve category, budget and exclusions. The App sends only refs actually rendered, separately from admission state refresh; stale cards are pruned, and empty/error clears old cards and selection refs. No separate comparison-management page exists.

## Evidence status

Public seams: actual Pi SDK against a controlled HTTP provider, public HTTP/SSE and session/cart reads. Additive migration cases use isolated fresh/synthetic-old databases only. UI evidence uses actual retained React App under jsdom, not a real browser.

Initial public REDs and incremental GREENs are in ../../ceres2-runtime-upgrade/08/test-runs/. Initial paired 16-case baseline plus DOM/type/build checks passed. Spec then found completion-order, reconnect and protected-close gaps; their separate REDs are recorded and TASK06 applied the shared corrections before its own changes. Corrected paired baseline passed 19/19 twice, typecheck/build passed, and both independent successor reviews closed; see REVIEW.md and RELEASE.json. Root released the controlled technical scope at 18:33 UTC. Formal task status remains in tasks/ceres2-runtime-upgrade-08-category-comparison.md; the release is limited to the exact controlled technical source fingerprint in RELEASE.json.

Actual qwen3.8-27b provider sampling is blocked by missing secure provider configuration. Real browser validation is blocked by the environment. User acceptance and TASK16 integration acceptance remain separate and incomplete. No local commit/push is made by this implementation worker; root owns commits and release.
