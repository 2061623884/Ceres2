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

This is a diagnostic fix, not a demonstrated cure for the original live failure. The next manually launched run can identify more of the transport cause. No agent has read the root `.env`, inspected private state or initiated a new live request. Full TASK16/browser/user acceptance remains outstanding.
