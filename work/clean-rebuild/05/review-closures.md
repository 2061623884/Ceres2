# TASK05 review closures

- Spec: unselected pantry stock/sellability could block the actual selected purchase. Public ninth test first failed with CHECKOUT_UNAVAILABLE after salt became unsellable/stock 0/version 2. The fix checks supply/stock and changed-offer confirmation evidence for selected rows only. It retains truthful sellable/available_qty for unselected candidates and shows an unavailable label. Selecting the unavailable item still invokes normal authoritative validation. This does not authorize partial required-ingredient supply or TASK07 optimization. Evidence: `work/ceres2-runtime-upgrade/05/test-runs/red-unselected-pantry-supply`; subsequent Tester green recorded separately.
- Standards: duplicate recipe lookup/validation between PurchaseService and DishService removed. The sole caller validates/loads one recipe, passes that exact recipe to deterministic requirements; no new abstraction or optional path.

No test command was run by the implementer. Root retains release and commit authority.
