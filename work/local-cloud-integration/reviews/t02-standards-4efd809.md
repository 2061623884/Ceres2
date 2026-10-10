# T02 canonical shopping: independent Standards review

## Fixed scope and sources

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/Ceres2_T02`, clean at inspection.
- Baseline: `ccf272b752f096ce0d80f7d0a4f29b19c05b0a77`.
- Frozen HEAD: `4efd8094e566de7d1589821d4cd7b16dde90debc`.
- Exact diff: `git diff ccf272b752f096ce0d80f7d0a4f29b19c05b0a77...4efd8094e566de7d1589821d4cd7b16dde90debc`.
- Commit list: `git log ccf272b752f096ce0d80f7d0a4f29b19c05b0a77..4efd8094e566de7d1589821d4cd7b16dde90debc --format='%H %s'`.
- Full diff and 12-commit list saved alongside this report as `t02-standards-4efd809.diff` and `t02-standards-4efd809-commits.txt`.
- Standards: AGENTS, domain/issue-tracker instructions, GLOSSARY, ADRs 0001/0002. Contract: T02 TASK and integration spec. All twelve smell heuristics considered; repository overrides and tooling exclusions applied.
- Merger confirmed T02 owns products/offers/knowledge-provenance after the static-source handoff; Offers/seed were already T02-owned. Guide API projection plumbing and constructor seams overlap the explicitly coordinated T03 integration.
- Shrimp source independently read from frozen Git object `6734c7fe79e670df2dae12b065dcc49c0b10a307:data/fixtures/offers.json`; its complete row matches the migrated row, including 1590 fen, stock 25 and demo provenance. No runtime database or old index was read.

## Findings (under 400 words)

Hard documented violations: none established.

Judgment finding, possible Mysterious Name (P3, nonblocking): `backend/app/services/product_constraints.py:45–64`, `def drink_filter_mismatch(product, conditions)`, now enforces category, pack count, product type, packaging and brand for every category before `if product['category_id'] != 'beverage': return False`. Its name still suggests a beverage-only predicate even though final snack/cart confirmation now depends on it. A focused rename such as `product_filter_mismatch`, updating its actual callers, would make this important shared boundary discoverable. This is a heuristic naming improvement, not a hard rule or correctness blocker; the docstring already describes the broader behavior.

No other smell warranted a finding. Alias matching preserves original user conditions. Case selling-unit and sugar-free acceptance require explicit sourced facts; two new minimal fixtures clearly identify synthetic provenance and leave original water/tea negative cases unchanged. Versioned product/provenance changes invalidate old retrieval manifests. The migrated shrimp Offer matches its frozen source.

Catalog recall sends the full approved/category-eligible ID space to retrieval instead of imposing a top-20 prefilter. Unknown returned IDs are excluded, current approval/category and Offers are re-read with `populate_existing`, and price/stock come from SQL rather than embedding documents. Shared constraints now reach final confirmation, including snack attributes and pack-count mode. Repeated seed retains mutable Offers; public regressions exercise that boundary, explicit add-to-cart, quantity/budget filtering and candidate 21.

Deadline/stop parameters have current integration callers rather than speculative uses. Standalone HTTP/answer projections establish or preserve bounded budgets. Pi-side forwarding belongs to coordinated T03 integration, so this T02-only pin is not complete end-to-end budget acceptance.

The parent reports 66 controlled tests GREEN at this pin. This reviewer executed no tests, installations, builds, services or real APIs. The controlled product double is explicitly not real BGE/index validation. Same-version T02/T03 integration verification and final whole-branch review remain separate.

Summary: zero hard violations; one nonblocking P3 naming judgment; no blocking Standards finding.
