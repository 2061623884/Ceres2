# TASK02 policy baseline and fixture provenance

Owner: implement_next_policy_help. Baseline: 6a448965 (implementation source inherited from 64ca7b6). No old database, order, session or credential is imported.

## Authority and source

The existing static policy IDs P-REF-01, P-RET-01 and P-RET-02 remain the shared policy source. The 2026-10-06 source version denotes this versioned simulation policy presentation, not an external merchant legal policy or newly effective law. Source label: Ceres 模拟售后规则. All rules apply only to this simulated business.

- P-REF-01: unshipped whole-order simulated refund; shipped/delivered orders do not qualify for refund-only. Concrete order status and previous applications remain checked by MercuryOrderService and AfterSalesService.
- P-RET-01: delivered within seven days and returnable product; whole order-item line only. The authoritative return_eligibility function still handles missing delivery time, expired window and product returnability.
- P-RET-02: explicitly nonreturnable products cannot be returned; unknown returnability does not establish eligibility.
- Existing P-DEL-01 is retained untouched; this ticket does not add delivery capability or delivery acceptance cases.

General-policy answers are produced from the same policy_summary helper in both roles. They disclose source ID/version and distinguish unverified concrete eligibility from submitted applications. Free model prose cannot replace the facts or claim approval/payment.

## Repeatable fixtures and evidence layers

Public test file: backend/tests/test_next_shared_policy_public.py. It reuses existing isolated HTTP/SSE fixtures. Fixtures create a new database per test and only synthetic model responses; actual Pi SDK uses a loopback HTTP model fixture. They do not read old business state or call a real provider.

- First vertical slice: Mercury unselected case asks return policy; public SSE must complete, show source/conditions, ignore fabricated model refund text, and public aftersales query remains empty. Tester RED next02-red-01 and GREEN next02-green-01.
- Second vertical slice: Keke asks same policy with no task/order; public SSE must show equivalent rules, no task/cart/order creation. Tester RED next02-red-02; GREEN pending shared adapter.

Controlled tests are technical evidence only. Real model sampling, actual browser-page interactions, natural-language review and user acceptance remain unverified. Current TASK status is owned by the integration task entry.

Inherited human fallback: Mercury's existing policy_indeterminate signal still opens an asynchronous human support ticket for unmatched policy, through record_query_outcome. This is existing authorized support behavior, not a new policy database or refund application. Claims of no writes mean no cart/order/refund-application mutation; chat history, read receipts, background extraction and an applicable support ticket can still be persisted. UI continues to expose the existing human-support panel and protects Agent writes while human responsibility is active.

## Technical checkpoint, 2026-10-06

Tester confirmed next02-green-02: both roles pass (2/2), with Pi build/typecheck successful. Third vertical RED next02-red-03 exposed incomplete unknown-condition disclosure; P-RET-01 now explicitly states the already-authoritative expired-window, nonreturnable, unknown delivery-time and unknown returnability conditions. next02-green-03 passes 3/3.

Frozen candidate regression: next02-regression-01 passes 49/49 (new six policy tests, Mercury public, aftersales public and human public); next02-regression-02 passes 12/12 across provider/wire, role/background memory and guide semantics. One known inherited deadline test was intentionally deselected and is not counted as passed; its correction is separately owned in TASK01. Total: 61 unique current-scope passing cases. Evidence records and raw logs are maintained by Tester under work/next-experience/10/runs/ on integration.

The composed TASK01/02/03 candidate still requires a fresh integration run. Browser-page, live-model and user acceptance evidence remains pending. Shared Pi adapter/worker patch was authored by TASK01 owner and applied unchanged here. The main prompt mandates the policy tool; real-model adherence, including rejection of merchant-policy claims through the ordinary-general-answer validator, must be checked in the frozen Prompt/real-model phase. No live credentials or providers were accessed.

## Existing UI path and controlled DOM proof

No new frontend adapter is required for orderless policy. MercuryChat initSession creates/reads a case and selects an order only when an explicit targetOrderId is supplied. Its send/input/button guards check text, session availability and busy state, not selectedOrder. Keke App's send guard likewise does not require a shopping task or order.

Tester checks/next02-dom-01 compiles actual current components and API adapters and executes ui_policy.mjs: App→Keke with no task/order and MercuryChat with empty order selection both accept input, send their real client request, and render sourced policy/conditions. No order-selection, proposal, confirmation, checkout or human-request write is emitted; existing human support entry is visible. This is controlled DOM/client evidence, not browser layout, integrated live-provider behavior or user acceptance.

Tester also reports 7/7 on composed integration policy cases plus the corrected inherited deadline test. Full later TASK01/03 composition still requires its own verification.
