# Drink fixtures: next-drink-v1

Source: existing tracked Ceres2 catalog/Offers at fea02b7, with provenance retained. Owner: TASK04. No archive/reference runtime imports, old databases, credentials or private holdout. Prices, inventories and product combinations are demo data, not live retail or fulfillment claims.

## Bounded changes

All13 existing beverage records receive a type and Chinese label justified by their existing product name/family: cola/可乐, water/饮用水, tea/茶饮, sparkling_water/苏打水, juice_drink/果汁饮料. Existing original-flavor cola names receive flavor=原味, and the existing peach juice name receives flavor=桃味. Zero-sugar names are not treated as flavor or health evidence. Unknown packaging, flavor and complete dietary/allergen evidence remain unknown.

Exactly one new explicitly simulated record supplies the otherwise missing same-type flavor contrast:
- DR:cola-lemon-330ml-can: 演示柠檬味可乐330毫升罐装, 演示品牌, cola/可乐, 柠檬味,330ml, one can per sale package;450fen and8 initial simulated units. Empty attribute_evidence; no nutrition, benefit or delivery claims.

Existing cola brands,330ml/500ml/6-can packages and current Offers already supply brand and sale-package differences. No full-category expansion is needed.

The seed inserts missing rows and refreshes only versioned released beverage type/flavor metadata. Existing Offer price, stock, sellability and version are never reset. Repeated import is tested after changing all three price/stock/version facts. Data additions are recorded separately from code and do not establish model-quality improvement.

## Scenario mapping

- DR-cross-type: shipped seed to real eligible type choices.
- DR-same-type: concrete type directly to product cards, factual brand/flavor/package/spec options.
- PKG-price: separate known sale packages and prices; multi-select totals use actual Offer values.
- SUP-unknown: missing brand/flavor does not create a filter; missing allergen evidence fails a hard safety condition.
- SUP-insufficient: isolated controlled budget/quantity or changed stock excludes supply and invalidates stale choices.
- No match: text adds an unavailable flavor, retains budget/quantity/spec, then explicit ordinary-filter clearing restores eligible options.

DR-prefixed isolated test fixtures in backend/tests/test_next_drinks_public.py provide controlled boundary variation and preserve repeated mutable stock. They are not real retailer claims. No AC-prefixed activity records are owned here.
