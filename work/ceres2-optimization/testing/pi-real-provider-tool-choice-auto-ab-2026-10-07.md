# Native tool choice A/B for interim messages

Date: 2026-10-07 (Asia/Shanghai)\
This is a test-only wire experiment against the then-current production build, whose main requests used `tool_choice=required`. A Node preload changed only the top-level `tool_choice` from `required` to `auto` on requests with a `tools` array. It did not edit production source, prompt, JSON mode, headers, URL, or any other request field. The resulting observations are a basis for the parent session's production change, not production verification.

The wire log for every case recorded exactly 3 tool requests, 3 `required` values changed to `auto`, zero requests containing `response_format`, and no captured bodies, headers, or credentials. Preload and source hashes are in each individual report.

## Results

| Case | Tool-bearing opportunities | Nonempty text + native tools | Audit outcomes | Published interim | Final |
| --- | ---: | ---: | --- | ---: | --- |
| Soda lookup | 2 | 2 | rejected: 2 | 0 | `finish_response`; `turn.completed`, accepted |
| Product + policy | 2 | 2 | approved: 1, rejected: 1 | 1 | `finish_response`; `turn.completed`, accepted |
| Recipe relations | 2 | 1 | rejected: 1; one opportunity absent | 0 | `finish_response`; `turn.completed`, accepted |

Overall, 5 of 6 tool-bearing opportunities had plain text alongside one or more native tools. The host ran the existing audit for those 5 candidates: four were rejected and one was approved and published. All three requests executed `finish_response` once and completed with `answer_status=accepted`; no unknown-reference error was observed. The final snapshots contained zero product cards for the soda and product-policy cases; the recipe case contained two dish candidates. The result verifies completion and the accepted interim path, but does not establish that every shopping/policy task returned the intended business results.

In the product-policy case, the one approved interim was sent as SSE sequence 3 at host `recorded_at_ms=1791370048723.9673` and `elapsed_ms=2180.558349609375`. The final `turn.completed` was sequence 25 at host `recorded_at_ms=1791370056471.9026` and `elapsed_ms=9928.49365234375`. The interim therefore preceded the final event in the actual public stream. Browser display time was not measured; this is SSE sequence and host-event timing only.

The candidate denominator includes only model iterations with a native tool call before the final `finish_response` iteration. Final-tool prose is deliberately not eligible for interim publication. The live stream did not produce multiple published bubbles: one of six candidates was audited and shown. No naturalness score is claimed. The four audit rejections remain unresolved pending review of only the rejected audit inputs, which are captured separately under ignored `testing/tmp/` when the diagnostic rerun is performed.

Per-case records retain event and source evidence:

- [Soda A/B record](pi-real-provider-soda-native-tools-auto-v1-2026-10-07.json)
- [Product/policy A/B record](pi-real-provider-product-policy-native-tools-auto-v1-2026-10-07.json)
- [Recipe A/B record](pi-real-provider-recipe-relations-native-tools-auto-v1-2026-10-07.json)

Raw SSE remains under ignored `testing/tmp/pi-real-smoke/<sample>/`; no text candidate is included in the checked-in report. The preload source hash for all three runs is `10332d19363f31b3054188810fea8b243db70bd26b8b82d6d3e5f9e96e0c7015`.
