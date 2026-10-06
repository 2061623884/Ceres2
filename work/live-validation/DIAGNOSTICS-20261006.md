# First manual run: Pi diagnostic gap

The original sanitized evidence from the first manually launched run is retained locally and unchanged.

Observed:
- Exact provider/model configuration, new isolated paths, seed and empty-cart gates passed.
- At 2.338 seconds overall, required Pi comparison ended `failed` with `PI_PROVIDER_ERROR` and generic `ProviderError`.
- The recorded application 502 is not an observed upstream HTTP status. Purchase, checkout and Mercury were not reached.

Confirmed source-level observability gap:
- The SDK converts original provider errors into assistant `errorMessage`.
- The worker previously reconstructed `ProviderError` and guessed selected status/code tokens from that string.
- Python exposed only a short correlation message, while the rest existed in suppressed log/cause output.

Fix scope:
- Transparent same-request fetch observation retains only actual Response status or finite error class/structured cause code. No body/header/URL copying, no additional requests, no retry/proxy changes.
- Reset observation at each model invocation and each fetch, avoiding stale earlier response status.
- Python positively validates the diagnostic and places it inside the existing nested error object, which the public SSE journal and durable receipt preserve.
- The batch allowlist preserves these fields separately from application HTTP status.

Verification seam: existing real-Pi/public-SSE synthetic provider fixture. A dedicated Tester first reproduced missing public diagnostic as a failing assertion; it owns compiled-worker build, typechecking and all synthetic execution. Additional controlled cases cover HTTP 401, closed connection and HTTP 200 carrying misleading “401” prose. Actual failure evidence is not overwritten or relabeled.

This is a diagnostic fix, not a demonstrated cure for the original live failure. At the time this note was first written, no agent had read the root `.env`, inspected private state or initiated a follow-up live request. A later user-authorized run is recorded below. Full TASK16/browser/user acceptance remains outstanding.

## User-authorized live follow-up — 2026-10-06 03:42 UTC

The local install/build smoke completed at source revision `3283e28cae09e856d53e1b56c43696fdb1426131` using Python 3.11.15, Node 22.19.0 and npm 10.9.3. Backend lock installation plus `pip check`, Pi runtime build and frontend build passed. Python 3.12.14 was unavailable through the installed uv Python source; 3.11.15 satisfies the backend's declared `>=3.11` requirement.

At the user's explicit request, the dedicated Tester ran one bounded live API batch. Config, isolated database/checkpoint paths, seed and live health gates passed. The required comparison did not naturally complete: the public result was `protected`, with `runtime_status=deadline`, `answer_status=failed`, and 4 completed tool rounds before the 15-second runtime deadline; a fifth model turn had started. No upstream HTTP status or transport cause was observed. The run exited 1 before the purchase, checkout, Mercury, extraction or memory stages. Do not count it as a pass or infer a provider/network cause.

Sanitized local evidence: [evidence](tmp/live-20261006T034233Z-d66f017a40aa/evidence). It is under ignored `tmp/`; keep its sibling `private-state` local and uninspected. No automatic rerun was performed. This first follow-up did not change the then-approved 15-second protection.

## User-requested 30-second run — 2026-10-06 04:40 UTC

The user explicitly changed the guide exploration protection from 15 to 30 seconds and requested one more bounded live API batch. The runtime entry deadline, Python Pi adapter limit, Node worker timer and public deadline text were updated; the five-tool-round cap remains. Mercury keeps its separate 15-second/five-round budget. On the updated, uncommitted working tree at revision `3283e28cae09e856d53e1b56c43696fdb1426131`, Pi typecheck/build passed. The admission lock test now waits 31 seconds, and its test-only SQLite busy timeout is 40 seconds. After this fixture correction, the full affected backend module passed: **23 tests, 87.70 seconds, exit 0**.

The single requested live batch passed configuration, isolation, seed and live health gates. It failed during `pi_comparison` after about 9.87 seconds with public application error `422 PI_UNKNOWN_REFERENCE` (`retryable=false`). This is not a 30-second deadline. No `runtime_status`, tool-round count, upstream HTTP status or transport cause was recorded. Purchase, checkout, Mercury, extraction and memory stages were not reached. The run exited 1; no live retry was performed.

Sanitized evidence: [evidence](tmp/live-20261006T044045Z-ade5f6652231/evidence). Do not inspect or upload its sibling `private-state`.

## User-authorized DeepSeek API batch — 2026-10-06 06:22 UTC

Further bounded runs after the 30-second change exposed independent prompt and harness issues; each evidence folder is retained and none of the failures is relabeled as a pass:

- `055416Z-f79c2fb38b68`: comparison ended with `PI_UNKNOWN_REFERENCE` while validating model product refs.
- `060428Z-13968b118835`: `PI_ROUTE_INVALID`; the app rejected a route registration after product lookup.
- `060800Z-e54300dc1117`: comparison passed, but the test's selection message added a new 100-yuan budget, changing task conditions and correctly invalidating the prior candidate. The one-shot harness was corrected to keep this as a pure selection turn.
- `061121Z-a64bb75e8c7d`: `PI_ANSWER_INVALID` for malformed final JSON. The Pi worker now requests JSON Output only when the endpoint hostname is the official `api.deepseek.com`; Python still strictly validates references. The official guide shows this mode with `deepseek-flash`: [DeepSeek JSON Output](https://api-docs.deepseek.com/guides/json_mode/).
- `061504Z-4444251939ab`: comparison, selection, cart and checkout passed; the one-shot harness assumed POST session creation returned `selection_version`. The API returns that field from GET, so the harness was corrected without changing the original runner or product API.
- `061748Z-d55b66f5ac5a`: the app correctly denied a whole-order refund proposal that incorrectly included an `item_id`. The Mercury prompt/tool description now states that whole-order refunds omit/null `item_id`; item IDs are only for user-selected item returns.

After those fixes, the single batch at `062210Z-0575eb5f534d` passed: `api_batch_passed`, **41/41 checks**, 34.02 seconds, exit 0, using `deepseek-flash` at `api.deepseek.com`. It covered Pi comparison, selected-item plan, simulated cart confirmation/replay, checkout/order replay, and Mercury refund proposal/confirmation/replay. Memory extraction was observed. Dream was skipped because its threshold was not reached. The independent Mercury public/aftersales regression modules passed **31/31**; Pi typecheck/build passed. The test used a fresh isolated demo database; canonical active guide runs were 0 before/after, the adjacent `private-state` was not opened, and only sanitized evidence was checked. The original `run_live_batch.py` was not modified.

Sanitized successful evidence: [evidence](tmp/live-20261006T062210Z-0575eb5f534d/evidence). This is a bounded API batch, not a browser test or full TASK16 acceptance. Browser, historical repurchase, supply revision, operator, stale consent, browser recovery, memory correction/deletion/restart, and independent second run remain untested.
