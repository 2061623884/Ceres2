# TASK01 minimal choice contract

Base: 6a4489650b81715aa0beea49eefcf015e91290fd; owner: implement_next_snack_flow.

Public seam: existing guide HTTP/SSE, session restoration and cart query. The first vertical test uses the actual Pi worker with a controlled loopback provider and asserts one supply-derived category question without a plan/cart effect. Only the designated Tester executes verification.

Reuse existing GuideMessage for durable question history, existing task/session anchors for validity, existing command receipts for action replay, Catalog/Offer for current facts, Comparison for cards, and PurchaseService for plans/confirmation. No generic pending state table or workflow engine.

Question projection: question_id (original assistant message ID), session_id, task_id, state_version, session_version, kind (category/products), question, options (option_id, label, value), selected_option_ids, status (active/answered/stale). Internally the same message stores exploration arguments and a current-supply fingerprint. Labels are display only. Active question and history are derived from these messages, not a second authority. Unrelated reads do not change anchors. Relevant task/condition/supply changes make old choices stale.

Structured answer: POST /api/v1/guide/sessions/{session_id}/questions/{question_id}/answers with request_id, option_ids, quantities keyed by option_id, expected_task_id, expected_state_version, expected_session_version. Category choice returns grounded product options. Product choices and quantities prepare a multi-item plan. Explicit existing confirmation remains a separate operation. Every action validates owner, current question, membership, operation kind, displayed anchors and fresh facts. No model/Kev call on valid structured paths.

Free text uses the ordinary text turn and actual Pi. Current question/options enter bounded context so the model can interpret an answer or a changed constraint; it cannot convert a label or an ambiguous answer into transaction authority. explore_products obtains real constrained supply and returns an opaque exploration_ref; the final exploration answer references only that host result.

App ownership is TASK03. TASK01 provides a typed question component and API helper; TASK03 wires projection/history and refresh. Runtime shared file ownership is TASK01 for initial frontier; TASK02 and TASK03 supply narrow adapters rather than concurrent edits.

Evidence remains pending: controlled RED/GREEN, public safety/regression journeys, real provider, real UI, and user acceptance are distinct gates. Existing simulated catalog facts never prove real retail inventory or fulfilment.

## Implemented continuation and safety fields

The same message-backed question contract also supports kind quantity when a selected product lacks a sale-package count. known_quantities preserves explicitly known per-option counts; answered_quantities records the submitted choice. select_question_products is a Pi read/prepare tool binding current question_id and option_id values. Its final selection_ref either publishes the one necessary quantity question or prepares the existing PurchaseService multi-item plan. It never confirms cart writes.

Dietary fields on current task conditions are excluded_allergens and dietary_requirements. They require source-backed metadata.attribute_evidence; unknown evidence does not satisfy a hard condition. PurchaseService.facts repeats this check during final confirmation, so a changed allergen statement cannot bypass the filter. Ingredient association IDs are never treated as a complete ingredient/allergen statement.

The App adapter is authored by TASK03 and integrated through its exact patch. QuestionChoices renders original IDs, disabled answered/stale history, unknown factual attributes, checked products and user-entered quantities. answerGuideQuestion sends IDs and anchors directly. App's existing snapshot ordering and displayed-plan confirmation guards remain authoritative.

## Verification limits

Controlled public API/SSE, actual Pi SDK with loopback provider, actual App DOM interactions with controlled HTTP, and build/typecheck are separate evidence. This is not a live-provider result, actual browser/layout acceptance, natural-language quality claim or user acceptance. No real .env, credentials or provider network was used. The strict controlled Kev transport exercises the production request/parser contract, not live Kev accuracy.
