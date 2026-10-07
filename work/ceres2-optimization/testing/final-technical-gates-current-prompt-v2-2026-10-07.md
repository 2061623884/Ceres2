# Final technical gates — current prompt v2

Date: 2026-10-07 (Asia/Shanghai)\
Worktree: `Ceres2-optimization-20261007`\
Evidence owner: dedicated tester. Provider credentials were loaded only into isolated subprocesses and are absent from reports. Browser screenshots, DBs, SSE, and runtime instrumentation remain under ignored `testing/tmp/` or `data/generated/` paths.

## Frozen verification snapshot

The final backend suite ran on HEAD `b118dbea3852026c6a04c790b1e27df67c3c9c18`, with source snapshot SHA-256 `4e87c6b746f70f3dd4ce3fa6066e143775e2df9274b5e584cd317b7193195525` over 66 modified/untracked files in backend, frontend, runtime, fixtures and evals. The prompt change that closes the recipe-result claim miss was included and the Pi runtime was rebuilt before verification. A later eval-metadata-only update to the failure-regression review file occurred after suite startup; it does not affect backend/runtime behavior or tests.

The run harness recorded only the aggregate source digest. Afterward, the original 66 path-to-SHA records and a source copy were reconstructed by reverting exactly the eval file's v2→v1 version string and removing its appended fifth case in a temporary copy. The reconstructed aggregate exactly matches the run record. The current source was not changed; see [the source manifest](backend-full-regression-source-manifest-current-prompt-v2-2026-10-07.json) and [the reconstruction script](freeze_backend_run_sources.py). The frozen copy is under ignored `testing/tmp/backend-full-regression-source-freeze-current-prompt-v2-2026-10-07/`.

The earlier full-suite run against the pre-fix test contract is preserved at [backend-full-regression-2026-10-07.json](backend-full-regression-2026-10-07.json) and its companion [backend-full-regression-2026-10-07.log](backend-full-regression-2026-10-07.log): 440 passed, 1 failed because `test_official_deepseek_thinking` still expected the removed `response_format=json_object` on main tool calls. The current test now asserts `tool_choice=auto`, actual tools, and no JSON mode while retaining thinking/token checks.

## Builds and test suites

`runtime/pi`: `npm run typecheck && npm run build` passed after the current interim-claim prompt update.

`frontend`: `npx tsc --noEmit && npm run build` passed. Vite emitted its existing `configLoader: native` notices about `__dirname` and the JSON import attribute.

Focused runtime verification passed: `tests/test_official_deepseek_thinking.py`, `tests/test_pi_interim_native.py`, and `../work/ceres2-optimization/testing/test_pi_interim_controlled.py` — 16 passed in 20.27 seconds.

The final complete backend suite passed: `../.venv/bin/python -m pytest tests -q` from `backend` — **441 passed in 819.24 seconds**, exit code 0. Exact log and command record: [backend-full-regression-current-prompt-v2-2026-10-07.json](backend-full-regression-current-prompt-v2-2026-10-07.json) and [backend-full-regression-current-prompt-v2-2026-10-07.log](backend-full-regression-current-prompt-v2-2026-10-07.log).

## Same-model interim claim audit

The first nine-case prompt-level sample completed all 9 provider calls but matched 8 expected verdicts: the model allowed a positive recipe ingredient/amount assertion. That failed evidence remains immutable in [interim-claim-semantic-audit-2026-10-07.json](interim-claim-semantic-audit-2026-10-07.json).

The prompt was narrowed for interim messages only; the ordinary `GENERAL_CLAIM_PROMPT` stayed unchanged. On the rebuilt prompt, all 13 of 13 same-model streamed checks completed with valid schemas and matched expected verdicts. The cases cover captured lookup plans, a Chinese egg lookup plan, price/stock/ingredient/policy claims, purchase promise/already-added claims, and four held recipe variants (unfamiliar quantity, ingredient-only fact, shared-ingredient fact, and a lookup plan mentioning the same recipe/amount targets without asserting results). The direct check used the exact compiled `INTERIM_CLAIM_PROMPT`, `deepseek-flash` via `api.deepseek.com`, disabled thinking, 256-token cap, and no JSON-mode override. It is a small same-model semantic smoke, not a blind or human score. Report: [interim-claim-semantic-audit-v2-2026-10-07.json](interim-claim-semantic-audit-v2-2026-10-07.json).

## Live product and recipe samples

Two fresh public Guide/SSE runs completed with `deepseek-flash` at `api.deepseek.com`. They used the production Pi worker/provider with a tester-only Python `sitecustomize` safe-event projection; reports explicitly mark that observation wrapper and do not retain credentials.

- [Product/policy sample](pi-real-provider-product-policy-current-v4-2026-10-07.json): 4 interim opportunities, 1 candidate ready/published and 3 absent. The 71-SKU catalog has no yogurt match, so the product side correctly remains a no-match; two final policy messages retain the general rules without claiming this absent SKU has refund eligibility.
- [Recipe-facts sample](pi-real-provider-recipe-relations-current-v4-2026-10-07.json): 2 opportunities, 1 ready/published and 1 absent. The final single business-facts message reported tomato 300 g and egg 3 pc for tomato-and-egg stir-fry; rice 300 g and egg 2 pc for egg fried rice; shared egg; and current simulated 10-count/¥12.80 and 6-count/¥9.80 offers. It made no cart change or purchase. The source prompt was subsequently narrowed for the discovered recipe-result auditor miss; current-prompt browser coverage below uses the rebuilt version.

## Firefox interim and fact-only result check

Native Firefox 136 with geckodriver 0.37.1 passed on the current prompt in [recipe-facts-visible-v6](browser-interim-smoke-recipe-facts-visible-v6-2026-10-07.json). The request was a fact-only recipe lookup. SSE delivered one interim at sequence 3 before `turn.completed` at sequence 17. While the proxy held the complete interim frame, the assistant text bubble was visibly inside the chat viewport (opacity 1, 28,285 px² visible intersection, full bubble visible), with progress still shown. The unique interim `message_id` mapped to exactly one additional visible text bubble; the DOM does not expose the React message key directly, so the evidence is the ordered SSE-ID-to-one-bubble-count delta rather than a DOM ID attribute.

After completion settled, the canonical recipe facts were visible and no `/result-introductions` API call occurred for the fact-only response. The browser still required the visible manual Keke role fallback after router status `unavailable`; this is not counted as automatic role-routing success. No current sample exceeded 30 seconds or required a thread dump.

Screenshots are ignored artifacts: [pre-terminal interim](tmp/browser-interim/recipe-facts-visible-v6/interim-1-before-terminal.png) and [settled final answer](tmp/browser-interim/recipe-facts-visible-v6/browser-interim-terminal-settled.png). An earlier v4 screenshot showed DOM bubbles that were outside the visible scroll area; that report was preserved and is not counted as a visual pass. The v6 geometry/screenshot check closes that observation gap.

## Limits

The semantic sample is not a blind evaluation and does not establish generalization. The live product-policy case is a valid yogurt no-match, not positive yogurt coverage. Automatic router availability remains unverified because these Firefox sessions used the manual role fallback. No human naturalness rating is claimed; candidate opportunity counts and earlier absent/rejected/error/timeout samples remain in their individual reports and the preceding failure-analysis record.

## Final repository hygiene

`git diff --check && git diff --cached --check` exited `0`. A read-only Git eligibility audit found no tracked or eligible DB/SQLite, Lance/Parquet, model-weight, local-configuration or credential-named files. All four sampled generated artifacts (two Firefox screenshots, an isolated SQLite DB and an exported capture) were ignored by Git; no generated artifacts were eligible for staging. Nothing was staged or committed by the tester.
