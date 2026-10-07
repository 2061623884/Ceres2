# T02 independent Spec review

Frozen HEAD: `4efd8094e566de7d1589821d4cd7b16dde90debc`; baseline: `ccf272b752f096ce0d80f7d0a4f29b19c05b0a77`. Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/Ceres2_T02`, clean at inspection. Commands: `git diff ccf272b752f096ce0d80f7d0a4f29b19c05b0a77...4efd8094e566de7d1589821d4cd7b16dde90debc` and `git log --format=fuller ccf272b752f096ce0d80f7d0a4f29b19c05b0a77..4efd8094e566de7d1589821d4cd7b16dde90debc`; outputs saved alongside.

## Result

No new missing, incorrect, or out-of-scope behavior findings in this T02 product/fixture delta.

- Spec “canonical 条件在检索候选空间/最终验证保持”: `CatalogService.search_products` supplies approved/category-scoped allowed IDs and requests their full count before downstream filters. It excludes unknown hits, rechecks current category/approval, and reloads Offer using populate_existing; index price/stock cannot become authoritative. Shared constraints cover canonical category, pack mode, type, packaging, brand, safety and existing drink-specific attributes. `PurchaseService.facts/confirm` rechecks these at confirmation alongside current supply, total selected amount, displayed plan, owner/state and quantity fences.
- T02 “current Offer 重读” and “不重置可变 Offer”: comparison/exploration apply requested quantity to stock and aggregate price eligibility; confirmation rereads after expiring cached state and rejects changed price/version/stock. Existing seed only inserts absent Offers. Regression source preserves modified price, stock, sellability and version across reseed.
- T02 synthetic-data contract: exactly two clearly labeled demo positives are added. Case matching requires selling_unit=case plus source, never pack count alone; sugar-free matching requires explicit sourced attribute evidence. Original water/tea negatives remain unchanged. Alias matching does not rewrite canonical user conditions. Incoming shrimp receives the documented simulated Offer; fixture/provenance versions change with source content.
- Typed questions remain based on filtered facts and current scoped option IDs; selection prepares a plan, and separate explicit confirmation is required for cart mutation. Public regression source covers positive/negative fixtures, the 21st eligible candidate, category/approval/Offer changes, and final constraint changes.

## Phase limits

Deadline/cancellation interfaces and standalone projection budgets are present. Pi caller wiring is owned by T03; the standalone T02 pin is not certification of the integrated original-deadline chain. T02+T03 same-pin verification remains required. No tests, installs, services, APIs, or product edits were performed. The reported 66-test GREEN and captured-source/commit equivalence remain Tester evidence. Controlled recall is not real BGE/index validation or final whole-branch acceptance.
