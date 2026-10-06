# TASK04 factual drink filters

Owner: TASK04 (bounded delegation approved by TASK01); base fea02b7. No new endpoint, request DTO, task store, transaction authority or confirmation path.

The existing products question optionally includes filter_options. Each has an opaque option_id, display label, attribute (brand, flavor, packaging or spec), and value. spec is {quantity:number, unit:string}; ordinary text values are strings. Null is offered only to explicitly clear an active ordinary filter. Unknown attributes never become choices. Values come from products already satisfying current offer, quantity, budget, type, exclusions and dietary conditions. Category questions remain types; product count does not manufacture a category question.

The existing question answer endpoint accepts one displayed filter option ID with no quantities. Product/filter mixtures and multiple filters are rejected. The original question remains answered history with its selected ID; a new question has a fresh identity and task version. Existing owner/session/task/version/current-supply/replay checks are unchanged. Conditions are amended one field at a time; a filter never selects a product, prepares a purchase, or grants cart permission. Product multi-selection and the separate existing cart confirmation remain unchanged.

Beverage-only drink_filter_mismatch applies type, brand, flavor, packaging and typed specification conditions in exploration and again in PurchaseService.facts before confirmation. Unknown or changed facts cannot satisfy a selected filter. This does not reinterpret inherited dish conditions for other categories. Safety evidence is still checked independently; clearing an ordinary filter cannot clear dietary/allergen constraints.

The actual QuestionChoices component renders filter controls only for kind=products. The App adapter and answerGuideQuestion remain unchanged. Cards expose known brand, flavor, packaging, sale-package price/count and simulated inventory; missing facts stay unknown. Quantity continuations cannot display copied filters as controls.

Runtime prompt ownership transferred to TASK05. That owner authored exactly two approved insertions into this TASK04 candidate: drinks alongside snack exploration, and flavor/spec amendments with typed spec. The new prompt candidate was rebuilt and revalidated separately; no other runtime behavior or timeout changed. Preserve30-second guide/15-second aftersales limits.
