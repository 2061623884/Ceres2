# Clean static catalog export

Source: archived Ceres2 repository, `data/fixtures/` only. The original `data/sale_guide.db` does not exist. Database sidecars, runtime databases, sessions, carts, checkpoints, orders, credentials, vendored applications, retrieval indexes and historical runtime outputs are excluded. Archived source files were read only; input SHA-256 hashes and verification results are in `verification.json`.

## Payload and schema

- `products.json`: 65 fixture-declared demo products. Identity is `sku_id`; `ingredient_ids` references `ingredient-catalog.json`. Original names, brands, categories, product types, tags, quantity specifications and static metadata are retained. `spec_quantity` + `spec_unit` (`g`, `ml`, `pc`) describe the source-declared sale-package quantity; do not multiply again by metadata pack count. Existing nested metadata/provenance is descriptive source material, not verified real-world facts or allergen guarantees. Missing fields remain missing.
- `offers.json`: one demo store, its fixture delivery quote, and 65 offers keyed by `(store_id, sku_id)`. 56 have explicit fixture prices and stock. Nine reproduce the archived seed's explicit default-offer policy: eight SKU price overrides, one deterministic fallback (`demo:clear-soup-base-200g`, 1748 fen). Default stock is 20. Every offer records its source. `sellable=true`, `is_demo=true` and initial `offer_version=1` reproduce initial fixture semantics, not live inventory. `price_fen` is simulated CNY minor units. No source timestamps, runtime IDs or mutable state are carried over.
- `ingredient-catalog.json`: 102 canonical ingredients, Chinese names, aliases and source mapping tags. Tags do not imply the absent imported product database is available.
- `chinese-dishes-v1.json`: 105 existing structured dishes. `base_people` is the recipe baseline; required/optional items retain exact `quantity_g`, `quantity_ml` or `quantity_pc`. Scale by requested people / baseline. `pantry_items` contain identities but no amounts: amount is unknown, not zero and not an invented serving conversion.
- `purchase-templates.json`: six existing purchase templates with the same quantity semantics.
- `shopping-scenarios.json`: one existing hotpot scenario with explicit component rules, source-declared per-person amounts and package counts. Preserve these as scenario data rather than interpreting them as recipe quantities.
- `assets-manifest.json`: image provenance and unavailable asset references. All 33 referenced archive JPEG paths contain Git LFS pointer text; no actual image bytes or local LFS objects are present. The other 32 products have no image path. No pointer text is copied as an image. Exported `image_path` is null for missing LFS assets; `image_status=unavailable_lfs_object`. Original pointer OID, expected size, path and checksum are retained. Use the application's ordinary missing-image presentation. Existing nested image metadata remains historical provenance, not evidence of a usable photo.

## Important limits

All data is demo material from the user's existing repository. No third-party recipe corpus was fetched or imported, and no new reuse/license rights are asserted. Existing OFF image URLs and official product provenance URLs, where present in static metadata, are retained for traceability only; they were not fetched. Image availability and depicted-product correctness are unverified. Display factual allergy claims only from separately verified evidence: missing or `unknown` metadata cannot mean allergen-free.

Thirty-five recipe/scenario ingredient IDs lack a corresponding product in this fixture-only catalog; the exact list is in `verification.json`. Catalog queries can run from this data, but recipe coverage is partial. Unavailable ingredients must remain unavailable until authorized evidence supplies actual catalog products and offers. All 65 available products have source-declared package quantities. No mass-per-piece conversion is supplied: egg counts must remain piece counts.

## Reproduce and validate

Run `python export_static.py /absolute/path/to/read-only-archive` in staging. It uses only Python's standard library; it does not import or run archived application code. Outputs are sorted-key JSON with stable source order. Source SHA-256 hashes are checked before/after export. Semantic checks cover unique IDs, offer-to-product/store relations, ingredient references, positive existing quantities and recipe baselines, and byte checks for copied assets where present. This is data verification, not an application or integration test.

Integrate payload JSON into the fresh application's chosen static-data directory only after the integration owner approves the destination. Keep this export script and source notes outside runtime dependencies.
