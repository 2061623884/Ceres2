# Native Pi interim, recipe facts, and browser follow-up

Date: 2026-10-07 (Asia/Shanghai)\
Worktree: `Ceres2-optimization-20261007`\
Tester: dedicated tester. The test-only browser proxy, temporary worker copies, databases, raw SSE and rejected-candidate text are isolated under `work/ceres2-optimization/testing/tmp/` or `data/generated/`.

## Build and controlled tests

In `runtime/pi/`, `npm run typecheck && npm run build` exited `0` after the native interim and `recipe_facts` changes. In `backend/`, `../.venv/bin/python -m pytest tests/test_pi_interim_native.py -q` exited `0`: `6 passed in 13.31s`.

An initial test invocation from the worktree root (`.venv/bin/python -m pytest backend/tests/test_pi_interim_native.py -q`) exited `4` because pytest could not import the backend's `app` package. The same test file then passed from its configured `backend/` workdir with the command above.

## Current live Guide/SSE samples

The current approved provider was passed only to isolated subprocess environments. Reports record model ID `deepseek-flash`, host `api.deepseek.com`, and that no API-key value was recorded.

| Sample | Instrumentation | Observed result |
| --- | --- | --- |
| `recipe-facts-native-tools-production-v1` | No `sitecustomize`, preload, or test worker copy | Completed/accepted, 22 frames, 2 ready interim candidates, 1 published before completion, 1 `finish_response`. Canonical host message included both named dishes; 2-person baselines; tomato 300g/egg 3pc and rice 300g/egg 2pc; pantry amounts explicitly unknown; shared egg; and current 10pc / ¥12.80 and 6pc / ¥9.80 egg offers. No product cards are expected for this `recipe_facts` response; two current product-evidence rows were returned. Cart, confirmation, and purchase-ledger row counts were all zero. |
| `soda-native-tools-rejected-audit-capture-v2` | Test-only copied worker and fetch observer; no wire fields changed | Completed/accepted, 2 ready candidates, both approved and published before final, one `finish_response`. |
| `product-policy-rejected-audit-capture-v2` | Test-only copied worker and fetch observer; no wire fields changed | Completed/accepted, 2 ready candidates, one approved/published and one rejected. Two final messages were returned; the demo catalog's lack of yogurt remains a no-product negative, while the policy response was retained. |
| `recipe-facts-rejected-audit-capture-v1` | Test-only copied worker and fetch observer; no wire fields changed | Completed/accepted, 2 ready candidates, one approved/published and one rejected. |

The uninstrumented recipe sample's exact SSE, DB and source snapshot are under `tmp/pi-real-smoke/recipe-facts-native-tools-production-v1/`; its concise report is [pi-real-provider-recipe-facts-native-tools-production-v1-2026-10-07.json](pi-real-provider-recipe-facts-native-tools-production-v1-2026-10-07.json). The three instrumented diagnostics have separate versioned reports: [soda capture](pi-real-provider-soda-native-tools-rejected-audit-capture-v2-2026-10-07.json), [product/policy capture](pi-real-provider-product-policy-rejected-audit-capture-v2-2026-10-07.json), and [recipe capture](pi-real-provider-recipe-facts-rejected-audit-capture-v1-2026-10-07.json). They do not modify the production worker or fetch request fields.

The text-only rejected-candidate capture contains one candidate in each of the product/policy and recipe samples. After inspection, both read as lookup/process plans, with no asserted merchant fact or completed business action. The candidate strings remain only in these ignored files:

- Product/policy: `tmp/pi-real-smoke/product-policy-rejected-audit-capture-v2/rejected-audit-candidates.jsonl`.
- Recipe: `tmp/pi-real-smoke/recipe-facts-rejected-audit-capture-v1/rejected-audit-candidates.jsonl`.

This is evidence of conservative false-positive audit decisions on lookup narration. No audit rule or merchant/execution guard was loosened. The soda capture sample produced no rejected candidate, so no text file was created for it. A prior capture-v1 attempt is preserved as a test-instrumentation failure: the temporary worker did not receive the opt-in output path and the run ended with `PI_RUNTIME_ERROR`; the test-only child environment injection was corrected before the two v2 captures.

## Firefox display verification

The current built UI was opened in native Firefox 136.0 headless through geckodriver 0.37.1, with the isolated demo database and the approved live provider. No production worker edits, Node preload, or Python `sitecustomize` were used. The tester proxy forwards the public SSE event frames unchanged and holds downstream delivery after the first `message.interim` until the Firefox DOM is sampled; this creates a direct pre-terminal observation point without changing event payloads.

The passing sample [browser-interim-smoke-streaming-v10-dom-barrier-2026-10-07.json](browser-interim-smoke-streaming-v10-dom-barrier-2026-10-07.json) exited `0`. Firefox showed two assistant text bubbles, including the interim, while the progress indicator was visible. The interim was SSE sequence `3`; `turn.completed` was sequence `9`, with runtime completed, accepted answer status, one `finish_response`, and two ready interim-candidate opportunities. The first interim was recorded 1.89 seconds after the host run start; the report does not claim that value is browser display latency.

Earlier attempts remain in separate reports: v4/v5 exposed a test-harness readiness predicate that waited for an empty-input send button to enable; v6 timed out without a terminal event and was interrupted during cleanup; v7 exposed a missing backend import path in the tester-only stack wrapper; v8 had no terminal event in its bounded observation and did not produce a stack dump; v9 received valid pre-final interim SSE but the DOM sampling heuristic failed to capture a pre-terminal snapshot. The corrected v10 frame barrier passed. These attempts are not counted as zero-interim completed turns.

## Evidence limits

The current samples verify controlled behavior, a live recipe-facts host projection, and one real Firefox pre-terminal bubble. They do not provide a naturalness blind score or prove that all user requests generate an interim. Each candidate, audit verdict, failure, and published message remains counted per versioned sample; historical wire-A/B and earlier zero-interim reports remain unchanged.

## Current prompt v2 verification

The initial nine-case same-model audit is preserved at [interim-claim-semantic-audit-2026-10-07.json](interim-claim-semantic-audit-2026-10-07.json): 9/9 provider calls completed, with one miss where an affirmative recipe ingredient/amount result was accepted. The prompt was narrowed only for interim process messages; the ordinary `GENERAL_CLAIM_PROMPT` did not change. The rebuilt current prompt passed 13/13 exact-prompt streamed checks: captured policy and recipe lookup plans, a Chinese egg lookup plan, the factual price/stock/ingredient/policy claim negatives, positive purchase promise/already-added negatives, and four held recipe-result/lookup variants. This is a same-model prompt smoke, not blind or human scoring. Full details and source hashes are in [interim-claim-semantic-audit-v2-2026-10-07.json](interim-claim-semantic-audit-v2-2026-10-07.json).

On the rebuilt current prompt, [recipe-facts-visible-v6](browser-interim-smoke-recipe-facts-visible-v6-2026-10-07.json) passed the actual Firefox visibility gate. The live response had two candidate opportunities (`ready`, `absent`) and one published interim. Its SSE sequence was 3, before terminal sequence 17. While the proxy held the interim frame and progress remained visible, exactly one additional assistant bubble was visible in the scroll viewport (opacity 1, 28,285 px² intersection). The browser DOM has no rendered React message ID attribute, so the report proves the ordered event-ID to one-visible-bubble delta, not a direct DOM key lookup.

The fact-only recipe response made no `/result-introductions` API call. The settled view showed canonical recipe quantities and current simulated egg offers. The manual role fallback was used after the router returned unavailable; this is not automatic-routing evidence. Screenshots are preserved under `tmp/browser-interim/recipe-facts-visible-v6/`: `interim-1-before-terminal.png` and `browser-interim-terminal-settled.png`. The earlier v4 screenshot showing DOM content outside the visible scroll area remains preserved and is not counted as a browser visibility pass.

The focused current runtime suite passed 16/16: official DeepSeek transport assertions, 6 native interim tests, and 4 controlled interim tests. The final backend suite then passed 441/441; exact command, duration, source snapshot and log are in [backend-full-regression-current-prompt-v2-2026-10-07.json](backend-full-regression-current-prompt-v2-2026-10-07.json). Historical `440 passed/1 stale transport assertion`, `8/9 semantic`, candidate rejections/absent opportunities, and earlier timeouts remain recorded in their own reports and are not overwritten.
