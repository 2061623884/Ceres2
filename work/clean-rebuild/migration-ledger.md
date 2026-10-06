# Clean rebuild migration ledger

## Foundation for P01/P02

Foundation is newly authored against retained HTTP clients. No archived Python package or database is imported at runtime. Source paths below refer to the immutable archive and are documentary only.

| Reference source | SHA-256 | Purpose |
|---|---|---|
| backend/app/core/identity.py | c511ec7403cd22bc0ae3a9b499735aec250cbc78ae2843af0800033dd1360f5c | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |
| backend/app/core/errors.py | 62faf3735c89bd5670db23171c8fc794e49750fbea0ea6df0b13b96eae76d55e | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |
| backend/app/core/database.py | ef0719a9b0788bd116e377a4dda6d7799442c029a597f543b34dd92fd92947a7 | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |
| backend/app/core/config.py | 9f81125d4bb8db78577c8eda3386d62bd0a92beb68bb9348c88026f19abf54de | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |
| backend/app/models/catalog.py | 881886fba0e93a31d0ede80d0883438e2effb9dff2b6cc7ee04a7f61e80319b6 | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |
| backend/app/models/store.py | 0ea1a01a94cd415a49b2bf3112ef849d6ad710a527aba00072045bd54cb10d40 | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |
| backend/app/schemas/catalog.py | fe7d67110254a9ba31823a29a23f527a2fb2a45b29ca9e75a6a5fb1c4eb86ee0 | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |
| backend/app/api/catalog.py | 6da11465ff99f323ced6d9ff06299ec57c1d568565480e5e0e61335599039cea | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |
| backend/app/api/bootstrap.py | e42b4950ee4d8dfd8897fdc516b10a84b735165d52cef201916e8c730413f43e | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |
| backend/app/services/catalog_service.py | 3fd7a73757fd08fb6c3fc7d592f51849c531b12f14e41c8520dde54f7f78fb0d | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |
| frontend/src/lib/saleGuide.ts | 1cf803ab57199a90d9d44b4658f2c1899b5916fc2ab5daeb5ccc6bd0922a6c95 | Identity/error/public catalog contracts; narrow model fields and projections, not bulk backend transfer |

Static data: only staged products.json and offers.json enter data/fixtures for the initial slices. The deterministic seed inserts absent rows and never resets mutable offers on repeat. Source input hashes and missing-image/partial recipe coverage are recorded in static-catalog/verification.json and README.md. Recipes, reviews, procurement, cart, checkout and human-ticket schema are not pre-created by foundation.

Database starts with a clean, recorded baseline; there is no conversion or load of archived SQLite files. Case/order models are registered from the Mercury owner and guide models from the Pi owner. Future schema changes need versioned migrations at their slice.

## Verified asset recovery

33 original JPEG objects were retrieved at source commit e24debf670db02a86cb79c40933b901827db8a55 and matched to archived LFS OIDs by the data worker. Exact provenance is in static-catalog/image-recovery.json. Local files live in data/images; data/fixtures/product-images.json maps only verified SKU assets. The remaining 32 products keep missing-image presentation. Runtime does not fetch source URLs. Python requirements.lock preserves the dedicated tester fresh-install resolution.

## TASK12 additive schema

After dedicated Tester observed the missing-column red on a synthetic P02 database, shared migration 0012_checkout_orders adds nullable store_id and version default 1 to canonical simulated_orders. It preserves unknown store identity and exact pre-existing snapshots. Cart/CheckoutPreview/CheckoutReceipt are registered from the TASK12 owner; no historical order data is imported.

## Explicit proxy dependency

The dedicated tester installed socksio 1.0.0 from the official registry because the current OpenAI/httpx transport consumes the supplied SOCKS proxy configuration. This explicit protocol dependency neither changes credentials nor bypasses trust validation. Manifest and resolved lock now include that already-tested installed version; previous source hashes are not represented as matching the amended manifest. Supplemental pip-check / lock / wire verification is tracked by the tester.
