# TASK08 bounded finished-product fixture, next-activity-v1

These three new AC-namespaced records are explicitly simulated demo supply, not verified merchant products, inventory, nutrition, discounts, dates, or health effects. They use the existing repeatable `seed_catalog` import and mutable Offer protection. No session, cart, order, or old runtime state is imported.

| SKU | Sale package | Simulated price | Initial simulated stock |
|---|---|---:|---:|
| demo:AC-salad-250g-box | 250g, one box | 1990 fen | 12 |
| demo:AC-fruit-platter-300g-box | 300g, one box | 1590 fen | 8 |
| demo:AC-juice-300ml-bottle | 300ml, one bottle | 990 fen | 16 |

Source: newly authored TASK08 demo fixture records in `data/fixtures/products.json` and `offers.json`. Each is `source: demo`, `finished_product: true`, and explicitly belongs to `activity_ids: [light-meal]`. Ingredient association IDs are empty: finished SKUs are never ingredient procurement plans. Attribute evidence is absent, so nutrition and dietary suitability remain unknown. Prices refer to the complete sale package.

The collection reuses the existing homepage card. It creates no promotion platform, timed program, rewards, shipping service, recipe catalogue, or health claim. A current hard dietary requirement still requires authoritative evidence and can therefore return no matches.

The public entry returns the ordinary guide snapshot and question contract; selecting items only prepares the existing plan. Cart confirmation remains separate and is rechecked by the existing purchase authority. Controlled verification and actual-browser/user acceptance are recorded separately.
