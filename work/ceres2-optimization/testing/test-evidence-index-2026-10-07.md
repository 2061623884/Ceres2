# Ceres2 optimization test evidence

Date: 2026-10-07 (Asia/Shanghai)\
Worktree: `Ceres2-optimization-20261007`\
Evidence owner: dedicated tester. Generated databases, indexes, browser captures and raw provider SSE remain under ignored `testing/tmp/` or `data/generated/` paths.

## Current validation state

The final backend suite on the rebuilt current prompt passed **441/441** in 819.24s. Its exact command, source snapshot and log are in [backend-full-regression-current-prompt-v2-2026-10-07.json](backend-full-regression-current-prompt-v2-2026-10-07.json) and the companion `.log`. A prior 440/1 run failed only on a stale expectation for `response_format=json_object` after production moved to `tool_choice=auto`; that evidence remains in [backend-full-regression-2026-10-07.json](backend-full-regression-2026-10-07.json). Earlier `431 passed, 3 failed` and focused `45/45` reports remain historical snapshots in [backend-regression-current-2026-10-07.md](backend-regression-current-2026-10-07.md), not the current gate.

Focused current checks passed for quality and fulfillment quantity clarification (2 tests), repeat seeding of the two chip SKUs without resetting Offers (1 test), fixture import repeatability, malformed Unicode Base64 returning 422, and the explicit evaluation annotation join contract. The same backend report contains their exact commands/results. The evaluation contract report clearly labels its reviewer as synthetic and technical-only.

## Retrieval and knowledge

- [preflight-2026-10-07.md](preflight-2026-10-07.md) records the independent Python/GraphRAG/BGE environment and dependency setup.
- [retrieval-dev-run-v4-literal-or-dense-2026-10-07.json](retrieval-dev-run-v4-literal-or-dense-2026-10-07.json), [relevance-hits-smoke-v4-literal-or-dense-2026-10-07.json](relevance-hits-smoke-v4-literal-or-dense-2026-10-07.json), and [hybrid-query-smoke-v4-literal-or-dense-2026-10-07.json](hybrid-query-smoke-v4-literal-or-dense-2026-10-07.json) capture 18 development queries, BM25/dense/RRF evidence, relevance hits, negative controls, and the four egg dishes returned for the literal query `蛋`. This tuned development set is not an independent acceptance set.
- [graph-schema-smoke-2026-10-07.json](graph-schema-smoke-2026-10-07.json), [graph-build-smoke-v3-2026-10-07.json](graph-build-smoke-v3-2026-10-07.json), [graph-artifact-audit-v3-2026-10-07.json](graph-artifact-audit-v3-2026-10-07.json), and [graph-global-overview-v3-smoke-2026-10-07.json](graph-global-overview-v3-smoke-2026-10-07.json) record the completed GraphRAG index, schema/artifact checks, and canonical local/global query projections. Graph build files and Lance/Parquet artifacts are kept in ignored `testing/tmp/`.
- In the global overview sample, the model's original selector identified 2/4 egg recipes. The host projection retained all 4/4 canonical egg-recipe facts from the 11 retrieved community reports; this is a host-scope result, not evidence that model selection improved. See [graph-global-overview-v3-smoke-2026-10-07.json](graph-global-overview-v3-smoke-2026-10-07.json).
- [pi-graph-tool-payload-smoke-2026-10-07.json](pi-graph-tool-payload-smoke-2026-10-07.json) confirms the Pi tool receives canonical facts/relations rather than a free-form GraphRAG answer or report text.

## Catalog, orders, after-sales, and browser

- [catalog-hybrid-http-smoke-2026-10-07.json](catalog-hybrid-http-smoke-2026-10-07.json) records live HTTP product retrieval against the isolated demo catalog with current Offer facts and hard constraints.
- [demo-quality-photos-state-smoke-2026-10-07.json](demo-quality-photos-state-smoke-2026-10-07.json) records the focused order-state, photo, and quality proposal/confirmation flow.
- [browser-demo-journey-2026-10-07.json](browser-demo-journey-2026-10-07.json) records the real Firefox/geckodriver journey: product search and detail, add to cart, simulated checkout, order status progression, entry to after-sales, quality quantity/photo proposal and confirmation, then operator ticket/photo access. The backend and DB were isolated in this worktree and used demo mode.

## Build and runtime checks

The frontend passed `npx tsc --noEmit` and `npm run build`; Pi runtime passed `npm run typecheck` and `npm run build`. Their results are summarized in [backend-regression-current-2026-10-07.md](backend-regression-current-2026-10-07.md). Vite emitted its existing `__dirname`/JSON import-attribute warnings.

## Real provider and evaluation evidence

[pi-real-provider-analysis-2026-10-07.md](pi-real-provider-analysis-2026-10-07.md) consolidates the pre-revision live sample, three planned revised-prompt public Guide/SSE samples, safe runtime-event diagnostic replays, and a single wire-instrumented A/B of `response_format=json_object`. Across the three planned revised-prompt attempts, one completed with two candidate events that were both absent, and two returned errors before ordinary SSE exposed candidate events. The A/B removed only the top-level JSON mode field from tool-bearing requests; it did not yield a publishable interim message or successful final answer. No naturalness rating is claimed, and browser display time remains unobserved. The individual reports retain source hashes; raw SSE/captures remain ignored.

[pi-real-provider-native-tools-followup-2026-10-07.md](pi-real-provider-native-tools-followup-2026-10-07.md) adds the latest native-tool/`finish_response` seam evidence: runtime typecheck/build passed and 43 focused controlled tests passed. Three fresh public Guide/SSE cases all completed, with 6/6 tool-bearing iterations producing zero text and 0 published interim messages. This remains a failed product-behavior target, despite the controlled protocol checks passing. The earlier failure reports remain intact. No browser multi-bubble check was repeated because there were no live interim bubbles to display; the previous browser journey does not verify that behavior.

[pi-real-provider-tool-choice-auto-ab-2026-10-07.md](pi-real-provider-tool-choice-auto-ab-2026-10-07.md) records a later single-field wire A/B: on the same prompt/build, changing only `tool_choice=required` to `auto` yielded 5 nonempty text-plus-tool iterations out of 6 and one audited, published pre-final interim. All three cases still used `finish_response` and completed; four other candidates were audited and rejected. This test-only override is evidence for a production change, not production verification; the uninstrumented retest remains pending.

[annotation-contract-smoke-current-2026-10-07.json](annotation-contract-smoke-current-2026-10-07.json) validates the label-join tool using a clearly marked synthetic reviewer label, not human scoring. It preserves the current separate event timestamp fields and leaves an unannotated fixture row null. The original export remains unannotated.

Older zero-interim, rejected-candidate, and timeout runs remain in their individual versioned reports and are not counted as passing completed interim turns. The latest current-prompt browser pass and its limits are documented below; no blind naturalness score is claimed.

## Latest native interim, recipe-facts, and browser evidence

[pi-interim-browser-and-audit-followup-2026-10-07.md](pi-interim-browser-and-audit-followup-2026-10-07.md) preserves historical six-case/native-browser evidence and appends current prompt v2 gates: 16 focused tests, 13/13 same-model semantic smoke cases after the recipe-result claim miss, and the current Firefox visibility pass. The current browser report records a visible pre-terminal interim, one visible bubble per observed unique event ID, and no automatic result-introduction API call for the fact-only recipe response. Earlier browser harness failures, candidate errors/rejections, and real no-terminal attempts remain preserved separately.

Current instrumented samples observed two ready candidates each for soda, product/policy and recipe facts. Publication counts were respectively 2/2, 1/2 and 1/2; two rejected candidates were retained as candidate text only under ignored `testing/tmp/` paths and inspected as lookup plans. The yogurt product query remains a legitimate no-match against the 71-SKU catalog, and the sample returned general return-policy rules without confirming eligibility for that absent SKU. The live recipe-facts sample returned source-derived quantities and fresh egg Offer evidence without changing cart state.

The current-prompt evidence is summarized in [final-technical-gates-current-prompt-v2-2026-10-07.md](final-technical-gates-current-prompt-v2-2026-10-07.md). It records the Firefox manual role fallback (router status unavailable), current interim candidate denominator, visible pre-terminal and settled screenshots, model/provider scope, and the distinction between same-model semantic smoke and blind review. The sample proves this one interaction path; it does not claim naturalness or a generalized interim-generation rate.
