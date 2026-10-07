# Native Pi tool and interim follow-up

Date: 2026-10-07 (Asia/Shanghai)\
Scope: the follow-up Pi seam uses required native tools without JSON mode, lets `finish_response` carry the final structured references, and sends non-final assistant text through the existing claim audit before publishing an interim. This report supplements and does not replace the earlier JSON-handshake and wire A/B evidence in [pi-real-provider-analysis-2026-10-07.md](pi-real-provider-analysis-2026-10-07.md).

## Build and controlled regression

From `runtime/pi/`:

- `npm run typecheck`: exit `0`.
- `npm run build`: exit `0`.

From `backend/`:

```sh
../.venv/bin/python -m pytest -q \
  tests/test_pi_interim_native.py tests/test_runtime_pi_product_query.py \
  tests/test_comparison_safety.py \
  ../work/ceres2-optimization/testing/test_pi_interim_controlled.py
```

Exit: `0`; result: `43 passed in 151.79s`. The new native-tool tests cover approved and rejected prose, completion without another generation request, unknown product references, and a mixed completion/tool iteration. The older controlled cases still cover approved/rejected interim, stop, and SSE reconnect. This establishes the protocol and host behavior under controlled model responses; it is not evidence that the live model emits interim prose.

## Live Guide/SSE samples

Three separate isolated SQLite stores and public Guide/SSE requests used the approved local Ceres2 provider configuration. The reports record only model ID/hostname, no key; role routing was unavailable in each case, so the tester explicitly selected Keke before the request.

| Sample | Terminal | Candidate opportunities | Candidate status | Published interim |
| --- | --- | ---: | --- | ---: |
| Soda lookup | `turn.completed` | 2 | absent: 2 | 0 |
| Product plus policy | `turn.completed` | 2 | absent: 2 | 0 |
| Recipe relations | `turn.completed` | 2 | absent: 2 | 0 |

Across all three runs, the 6 tool-bearing iterations had zero text characters and one or two native tool calls; none produced a ready, invalid-format, or published interim. Each request completed, and each run recorded three valid main-model usage events with nonnegative durations. Provider metadata was `deepseek-flash` on `api.deepseek.com`; secret values were not recorded. These samples do **not** meet the multi-message behavior goal. They show that the new seam avoids the prior JSON-mode and answer-reference failures for these cases, while the model still emits no optional prose in the observed tool iterations.

Per-run reports and source hashes:

- [soda native-tools sample](pi-real-provider-soda-native-tools-v1-2026-10-07.json)
- [product and policy native-tools sample](pi-real-provider-product-policy-native-tools-v1-2026-10-07.json)
- [recipe-relations native-tools sample](pi-real-provider-recipe-relations-native-tools-v1-2026-10-07.json)

All three share these hashes: `runtime/pi/src/worker.ts` `397cca13064d7f9f8f7d1344c7316496bdc27fb11bbb3e437ed5786de5d06906`; `runtime/pi/dist/worker.js` `2db081c6c93863c102767ed8866cec2ae83e09828679f4436d2113a7f2f7e713`; `backend/app/prompts/experience.json` `c82d3c67c4d3d310bbcc2e7fc864649144504aa2b48f52cd4aa4240138cdde80`.

The test runner with the three versioned aliases has SHA-256 `5abf331326a9a608a8a1725f5f1ed1bee6d3c34dba9a128627c555e4cfe4610f` at this report revision.

Raw SSE remains under ignored `testing/tmp/pi-real-smoke/<sample>/`; exported run captures remain under ignored `data/generated/evals/`. No browser multi-bubble check was repeated in this follow-up because the live runs emitted no interim bubble to render. The prior Firefox journey validates the shopping/order/after-sales flow, not multi-message rendering. Controlled SSE persistence and reconnect behavior are covered by the 43-test run above.

The previous real-provider failures remain documented in the linked earlier report. The new live results are a new versioned sample set, not replacements for those failures or a naturalness rating.
