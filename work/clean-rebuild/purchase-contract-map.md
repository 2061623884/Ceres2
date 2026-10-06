# Clean purchase contract handoff: TASK04–11

Read-only preparation, 2026-10-05 16:46 UTC. Only this document was written; no implementation, application/test/install command, task-state change or archive mutation. Current source is a moving TASK03 worktree, not its release. Recheck TASK03's released manifest before dispatch. No historical result is acceptance evidence.

## Release order and unique ownership

Approved tickets: 04←03; 05←04; 06←05; 07←06; 08←04; 09←03+02; 10←09; 11←07+09. Root must release each dependency, then assign one implementation owner. This document does not release blocked work.

TASK04 should own the small shared purchase DTO and confirmation transaction: backend plan/item/confirmation schemas, their projection in `frontend/src/lib/saleGuide.ts`, and edits to `api/guide.py`, `models/guide.py`, `pi_product_turn_service.py`, `pi_product_runtime.py`, `runtime/pi/src/worker.ts`, `App.tsx`, migrations/model registration. Later tickets extend this same contract; do not concurrently invent alternative `PlanResponse`, amount, or receipt shapes. TASK09 owns memory DTO/recall policy shared with Mercury, coordinating actual edits to Mercury's provider/tools with that module owner. Root retains registration/migration integration ownership or explicitly transfers it. No generic framework is needed.

## Existing clean entities and seams to reuse

- `GuideSession`: owner, current task, session version, entry context, store and delivery zone. `GuideEntry` provides canonical owner entry; `require_canonical_session` preserves legacy sessions read-only.
- `GuideTask`: owner/session, state version, step/status, `goal`, `conditions_json`, nullable `plan_json`. This already stores the current plan; a second entire task/plan framework is unnecessary.
- `GuideTurnReceipt`: run/request ID, digest, original admission anchor/input, status/result, execution ID/start time. `GuideRunEvent`: persisted SSE sequence. `GuideCommandReceipt`: lifecycle command replay. Reuse run lifecycle and immutable admission evidence, not another runner.
- `GuideMessage`: persisted user/assistant history but **no plan ID/version columns**. Persist a displayed-plan association in TASK04 (message-linked reference or equivalent precise task snapshot); generic chat text is not a confirmation reference.
- `CatalogProduct` and `CatalogService`: canonical SKU, ingredient IDs, package quantity/unit, brand, tags, metadata. `Offer`: store/SKU price in fen, integer available sale packages, sellable, offer version. `Store`: demo flag and delivery zone.
- `Cart` and `CartItem`: owner/store/version and unique cart/SKU integer quantity, current price. `CartService.fence` serializes owner writes. **`mutate` commits internally and `get_cart` may create/commit**: do not loop over these inside plan confirmation. Factor the smallest transaction-owned cart mutation/read seam and let confirmation own the commit. Preserve shelf POST/PATCH/DELETE behavior and checkout integration.
- One canonical SQLAlchemy database; migration entry is `backend/app/migrations/__init__.py`, registration `models/__init__.py`. Additive fields/tables only, with synthetic-old and repeat-upgrade tests; do not import archived runtime databases.

## TASK04: minimum vertical slice

### Proposed host contract, not yet implemented

1. Keep actual Pi `guide_request`, `search_products`, `product_details` SDK tools. Add the smallest explicit purchase-proposal tool and explicit-confirm intent path. Python resolves refs and computes facts; tool output cannot itself grant approval. Current worker/Python whitelist and final JSON validator only accept query/conversation/status, so **both** protocol ends and host final rendering need coordinated edits.
2. Direct-product proposal: one selected canonical SKU, positive integer sale-package count, current task conditions (budget fen, exclusions), store/zone, and existing owner/task/session anchor. Candidate selection creates a plan, not cart writes. Related new products remain suggestions until selected. An ambiguous product needs actual candidates and clarification.
3. Use `GuideTask.plan_json` for one versioned bundle snapshot. Required public fields below plus internal owner/task identity, offer/store/zone evidence, displayed revision and expiry policy. Persist factual proposal/history and `plan.ready`/terminal result together under current task/version fence. Return `plan_effect='replace'`, `available_actions` including `modify` and, only if eligible, `confirm`.
4. Implement retained button endpoint `POST /api/v1/guide/tasks/{task_id}/confirm`, `Idempotency-Key` header; body `{plan_id, plan_version, expected_state_version, expected_session_version, selected_items:[{sku_id,quantity}]}`. Text “就按这个加购” resolves the unique current **displayed** revision and enters exactly the same service. “好的/可以”, candidate selection, budget acceptance, old messages and model claims do not authorize cart mutation.
5. Small durable confirmation receipt: owner/key, request digest, task/plan/revision, result JSON and receipt/operation identity. Check same-key replay **before** stale-version rejection; same key different body conflicts. Also fence the revision against a second key or the other confirmation entry point. Store real per-plan/row added quantities, not a global inference from cart alone; project remaining quantities. A transaction-safe row-add operation uses the same facts/ledger without forcing a model turn.
6. One short transaction rechecks owner/canonical session/active task, session+state+plan versions, unique displayed revision, exact selected outstanding SKU/count set, budget/exclusions, current store/zone delivery evidence, offer price/version/sellability and stock including existing cart count. Claim permission against stop/run state **in the same transaction** as cart increments, plan ledger, task/version changes and receipt. Stop first means no write; commit first means factual receipt even if later delivery/transport fails. No compensating cart deletion.
7. Keep receipt recoverable after a lost response and SSE reconnect. Task/run finalization must not overwrite a successful confirmation with stopped/failed or publish old plan state. Existing TASK03 `stop_requested` and late-result fences need transactional integration, not only a pre-call boolean check.

### Existing UI/API fields that matter immediately

`PlanResponse`: `plan_id`, `plan_version`, `mode ('bundle'|'alternatives')`, `items`, `total_price_fen`, `expires_at`, `validation_status`; optional `targets:[{group_id,name}]`, `selected_total_fen`, `gaps`, `can_confirm`.

`PlanItem`: `sku_id`, `quantity`, `unit_price_fen`, `line_total_fen`; optional `name`, `image_path`, `role ('required'|'pantry'|'optional')`, `selected`, `added_quantity`, `remaining_quantity`, `spec_quantity`, `spec_unit`, `requirement:{quantity,unit,source?:{original_quantity,original_unit}}`, `contributions:[{group_id,quantity,requirement}]`.

`ConfirmResponse`: `operation_id`, `status`, `cart_version`, `items_added:[{sku_id,quantity}]`, `errors`, `task_id`, `state_version`, `session_version`, `confirmation_id`. Session DTO also accepts `confirmation_result`. Backend currently has no `/confirm` or `/plan-revisions` route despite retained clients.

`App.tsx` only retains a restored plan when `available_actions` contains **`modify`**; `confirm` alone is insufficient. Normal send re-fetches the authoritative session after terminal response, so updating only a turn response loses the plan. `confirmableItems` submits selected outstanding amounts; `remaining_quantity` is preferred, otherwise quantity minus added. Button handler currently generates a new key per attempt: revision-level duplicate protection remains necessary. Retained revision client sends `{request_id, expected_state_version, expected_session_version, base_plan_id, base_plan_version, coverage_intent:'partial_ok', items:[{sku_id,quantity,selected}]}`. Do not let that hard-coded historical `partial_ok` silently authorize TASK07 partial procurement; distinguish selection revision from explicit partial-purchase decision.

### Immediate highest-value public cases for Tester

- Two isolated owners; one SKU, explicit quantity 2, offer stock >=2. Query/select yields plan and unchanged cart; button and text produce identical real increment/receipt.
- “好的” and quoted/old confirmation do not write. Current plan absent, ambiguous or revised: no write. Related recommendation remains outside plan.
- Same-key same-body retry after success/lost response; same-key changed quantity; two different keys and simultaneous button/text against one revision: at most one increment.
- Stop before claim vs commit before stop, task replacement/amend while model runs, stale session/store/zone, other-owner task, price/stock mutation and budget/exclusion failure.
- Inject failure before commit: no cart/ledger/receipt partial state. Lose response after commit: public receipt/session/cart reads show success. Preserve shelf direct mutations and checkout stock/version behavior.
- Row explicit add followed by full confirm adds only remaining quantities; changing/removing a goal never silently removes cart facts.
- Empty/synthetic-old database, repeated migration, recovery/hold preserves cart/history/receipts. New technical evidence, two independent behavior runs, separate UI/provider and user acceptance.

## Exact static data and units: TASK05 onward

Active `data/fixtures` currently contains products/offers/product-images only. Approved reproducible static export is `../staging/static-catalog/`; provenance/coverage in `work/clean-rebuild/static-catalog/{README.md,verification.json}`. Import only chosen JSON into fresh runtime-owned data with provenance; never runtime-import staging/archive or execute old application code. Export has 65 demo products/offers, 102 ingredient identities, 105 dishes, six templates, one hotpot scenario. Recipe coverage is partial (35 recipe/scenario ingredient IDs lack products).

- `chinese-dishes-v1.json`: `{version,dishes:[{dish_id,name,aliases,base_people,required_items,optional_items,pantry_items}]}`. Required/optional amounts use one exact field `quantity_g`, `quantity_ml`, or `quantity_pc`, plus `ingredient_id`.
- `purchase-templates.json`: `{version,templates:[{template_id,scenario,base_people,required_items,optional_items,pantry_items}]}`.
- `ingredient-catalog.json`: `{version,description,ingredients:[{ingredient_id,name_zh,kind,aliases,ner_terms,...}]}`. Optional OFF tags/categories are source mapping metadata, not available external catalog or verified allergy facts.
- Pantry is an array of **ingredient IDs without amounts**. Default unselected; not selected does not mean already at home. Unknown amount remains null, not 0, 30 ml or 50 g. Archived `_pantry_needed` invents 30/50 quantities: **do not inherit it**. User may explicitly choose a sale package without claiming recipe requirement coverage.
- SKU `spec_quantity` + `spec_unit` (`g`,`ml`,`pc` in export) describes the **whole sale package**. Do not multiply again by metadata `pack_count`. Cart/plan `quantity`, Offer `available_qty`, and shortage package counts are integers of sale packages; required quantities/leftovers are g/ml/pc. Price and totals are integer CNY fen.
- Scale requirement = original amount × requested people / `base_people`. Preserve baseline and source (`default` baseline vs explicit user people). Round a fractional egg requirement to whole eggs only for coverage, then divide by package amount and ceil sale packages. No egg mass conversion exists; no mass↔volume↔piece conversion is licensed.
- Concrete recipe: `dish-fanqie-chao-dan` baseline 2, tomato 300 g and egg 3 pc, pantry oil/salt/sugar. `dish-dan-chao-fan` baseline 2, rice 300 g and egg 2 pc, pantry oil/salt/scallion.
- Concrete SKU: `demo:tomato-fresh-500g` 500 g; `demo:eggs-fresh-6pack` 6 pc; `demo:eggs-10pack` 10 pc; `demo:salt-500g` 500 g. At 3 people tomato/egg requirement =450 g/4.5 pc, needed whole eggs=5, one 6-pack covers it. Report source amount and package remainder honestly.
- Offers payload additionally has `store` and `delivery:{zone_id:'zone-default',reachable:true,eta_minutes:45}`. Clean Store persists zone but CatalogService currently returns `delivery_eta_minutes:null`; there is no full delivery quote model/service. TASK04 must explicitly use a minimal fixture-backed delivery contract rather than inventing live ETA/reachability or importing old service dependencies.

## Later slice additions, bounded by ticket

### 05 single dish

Add a minimal recipe loader/model only as required by chosen static source, host proposal target + people/source + selected SKU overrides, and deterministic ingredient demand/package calculation. Extend current plan rather than replacing it. Keep requirement/source, package and added/remaining fields. Existing UI calculates demand and coverage from contributions or row requirement only when unit matches package; it displays original quantity/unit when provided. Revisions must retain chosen specification, update amounts/budget and invalidate prior confirmation. No global optimization/multi-dish implementation here.

Public fixture: tomato-and-egg for baseline/3/5 people; 6/10-pack eggs, explicit selected SKU retained after people change; pantry unchecked then checked; user quantity revision; exclusion/budget; modify before/after row purchase; incompatible/unknown unit stays unknown. All confirmations use 04.

### 06 multi-dish

Add stable target/group IDs and per-target requirements/contributions to the same plan. Merge only compatible ingredient demand, **before** package rounding; preserve target-specific source/selection and explicit SKU choices. Do not merge incompatible form/specification or unknown dimensional amounts just because text/SKU appears similar. Update/remove a group without losing others. Added ledger survives revision; source quantities are not inferred from cart.

Public fixture: two compatible 300 g requirements with a 500 g package require ceil(600/500)=2, versus a 200 g+200 g pair requiring 1 rather than independently 2. Tomato-and-egg plus egg fried rice share 5 eggs at baseline and fit one 6-pack. Group removal/headcount change, incompatible SKU choices, shared budget, existing row add and reconfirm must all preserve exact cart counts.

### 07 supply / partial procurement

Extend requirement-addressed gaps with factual `kind`, missing/unknown attribute, required amount+unit, requested/available/shortfall **packs**, group/requirement IDs. Keep full plan vs supply preview vs explicitly chosen partial plan distinct. Explicit partial selection changes the plan; it is a separate decision from final cart confirmation. Evaluate compatible packs for one ingredient using entire demand, total price and remainder, preserving selected specs. No global meal optimizer; old 5% near-price threshold and 99-stock cap are historical implementation details, not approved clean requirements.

Public fixture: chosen spec out of stock with compatible alternative; insufficient single SKU but multiple packs can cover; ingredient wholly missing; null quantity/availability distinct from unavailable; query failure distinct from no stock. Preview doesn't write or silently select partial; partial selection still doesn't add until independently confirmed; price/stock changes demand refreshed display/confirmation.

### 08 category comparison

Use current CatalogProduct metadata and offer facts; no extra comparison management page. Retained `ProductComparisonCard` fields are `ref,sku_id,name,brand,image_path,packaging('can'|'bottle'),pack_count,item_volume_ml,total_volume_ml,price_fen,price_per_litre_yuan`. Existing strict types must permit explicit unknowns where source metadata is missing. Product volume comes from `spec_quantity` (whole package); metadata has `item_quantity,item_unit,pack_count,packaging,family_id,sugar_type` on detailed cola rows. Unit price yuan/litre = price_fen ×10 / total_volume_ml; never compare unknown/non-volume units as though equal.

Examples include `demo:cn-coke-original-330ml-can` (330 ml, one can) and `demo:cn-coke-original-500ml-bottle`; generic `demo:cola-330ml` lacks packaging metadata. Current Pi product refs are **run-local random refs**; add bounded persisted displayed candidate evidence for a subsequent user selection, scoped to owner/task/version/context, not a global ref registry. Empty results clear old cards/refs. Preserve page/category conditions. Public cases: real multipacks, unknown metadata, empty/error, selected current candidate routes to 04, comparison alone creates neither plan nor cart.

### 09 explicit memory and role boundary

Add one SQL ShoppingMemory authority: ID/owner/category (`user|feedback|project|reference`), content, explicit/automatic source, source evidence, revision, timestamps/expiry and deletion fence needed by subsequent 10. Commands save/list/update/delete with verified owner/ref; deterministic result rendered into chat. Existing archived MemoryService caller-owned transaction and separate list/recall are useful concepts, but its physical deletes/no revision and blanket user/feedback recall are insufficient for approved role/fence requirements.

Full valid-memory list is not the bounded model context. Recall max 5 records/2,000 characters, current task constraints > explicit memory > automatic memory; role-specific relevant background only. Reference records retain source, never supply order facts or approval. Integrate actual Mercury entry/provider, not a standalone memory endpoint demonstration. Public fixtures cover all categories, two owners, role need-to-know, current overrides, expiry/deletion immediate, cross-task effect and truthful CRUD receipts.

### 10 recoverable extraction / Dream

Small durable background job/source uniqueness, status/lease and per-owner Dream serialization, coupled to a committed eligible reply. Independent configured model; main reply doesn't wait. Automatic TTL 30 days; Dream at >=10 valid automatic memories and >=24h since successful Dream. Recheck source/revision/deletion fence before commit; unchanged content does not renew TTL, explicit edits win. Do not copy archived trace-event-as-job algorithm: a started event currently suppresses retry forever and `_save(renew_existing=True)` renews identical extracted content.

Public cases: response visible while model blocked, restart/expired lease, duplicate source, failed model never says saved, late extraction after explicit edit/delete, Dream loser, fixed clock at count/time boundaries, unchanged TTL, actual qwen3.8-27b timing separately from controlled provider fixtures. No shopping monitor/notification.

### 11 history / repurchase

Reuse owner-scoped task/history snapshots as immutable sources; add only historical source reference and one-time reminder decision/seen state needed for journey. Current task replacement retains older rows already. Reminder checks actual cart and relevance before once-only offer; ignored/declined means stop. Ambiguous “上次” asks source choice. Selected history makes a fresh task/plan under current people/budget/exclusions/valid memory and current catalog/supply. Do not inherit old prices, stock, ledger, confirmation or mutate source snapshot.

Public cases: two owners, two ambiguous histories, current cart already covers old remainder, ignore/reject, changed price/stock/people and multi-dish source, partial procurement branch, fresh independent confirmation with retry, old snapshot unchanged.

## Source pointers and no-copy warnings

Authoritative: `tasks/ceres2-runtime-upgrade-{04..11}-*.md`, `docs/plans/ceres2-proactive-upgrade-spec.md` §§4–5 and accepted public/transaction test seams, root `AGENTS.md`.

Read-only archived **own** conceptual references at `../archive/ceres2-before-clean-20261005/backend/app/services/`: `confirmation_service.py` (replay-before-version and exact outstanding snapshot), `plan_item_service.py` (row ledger), `plan_revision_service.py` (revision), `plan_contract.py` (requirement vs package dimensions/gaps), `template_plan_service.py` (serving math), `shopping_plan_service.py` (contributions/merge), `memory_service.py`, `automatic_memory_service.py`. These pull old conversation/trace/operation/catalog/delivery/agent systems; don't bulk-copy that dependency graph, old fallback defaults, or sys.path/PYTHONPATH imports.

Archived tests offer assertion examples only: `test_confirm_service.py`, `test_concurrent_confirm.py`, `test_revision_confirmation.py`, `test_pantry_plan.py`, `test_v2_servings.py`, `test_v2_supply_adaptation.py`, `test_v2_cola_comparison.py`, `test_v2_explicit_memory.py`, `test_v2_automatic_memory.py`. Tester should express new red/green journeys through public HTTP/SSE/UI and the approved confirmation unit-of-work failure seam, without old collection errors/skips or inherited pass claims.
