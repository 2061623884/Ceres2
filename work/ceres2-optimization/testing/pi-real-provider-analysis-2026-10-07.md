# Real-provider Guide/SSE interim analysis

Date: 2026-10-07 (Asia/Shanghai)\
Provider/model: configured DeepSeek Flash at `api.deepseek.com`. No API key, request body, response prose, owner ID or hidden reasoning is written to reports. Every live turn used an isolated worktree database and the public Guide/SSE entry point. The route endpoint returned unavailable because no KEV base URL is configured, so each actual guide request followed an explicit Keke role choice. Memory extraction/dream background models were disabled for these tester runs; the Pi turn itself used the approved live provider.

## Planned three-request sample set

These three first attempts are the requested versioned sample set for the updated experience prompt. The two errored turns remain failures in the denominator; their candidate events are not available in the ordinary terminal SSE error payload. Later diagnostic replays are reported separately and do not replace them.

| Sample | Terminal result | Candidate denominator available from ordinary SSE | Observed interim |
| --- | --- | ---: | --- |
| `soda-revised` | `PI_ANSWER_INVALID` after three `understanding` phases | 0; error ended before runtime events were returned | 0 published; diagnostic retry found 1 `absent` candidate before `guide_request` |
| `product-policy` | `PI_UNKNOWN_REFERENCE` | 0; error ended before runtime events were returned | 0 published; diagnostic retry returned no candidate event and no tool-execution event |
| `recipe-relations` | `turn.completed` | 2 | 2 `absent`; text lengths 0 and 25 whitespace characters; 0 published |

The completed recipe turn had 3 main-model calls, valid usage/host/timing fields, 12 SSE frames and 71 final `answer.delta` characters. The host-reported event times are separate top-level event columns; browser display time remains unobserved. These samples do not establish multi-message behavior. The observed candidate denominator is 2/2 absent in the only successful primary sample; the two failed turns have unavailable candidate denominators.

Reports and raw captures:

- [soda-revised](pi-real-provider-soda-revised-2026-10-07.json), [product-policy](pi-real-provider-product-policy-2026-10-07.json), [recipe-relations](pi-real-provider-recipe-relations-2026-10-07.json).
- Raw SSE and export captures stay under ignored `testing/tmp/pi-real-smoke/` and `data/generated/evals/` paths. Exported labels are null before annotation.

## Safe runtime-event reproductions

A test-only Python startup wrapper re-ran the two failed prompts and saved a filtered view of `PiProductRuntime.events` on success/error. It left the model calls, host code, tools, errors and event flow unchanged. Only event types, candidate status/character count/tool-call count, tool names, usage fields, and allowlisted transport diagnostics were retained.

- The soda retry again returned `PI_ANSWER_INVALID`. It had one candidate event: status `absent`, 0 text characters, 1 native tool call (`guide_request`). Two main model-usage events were observed before the later host error.
- The product/policy retry again returned `PI_UNKNOWN_REFERENCE`. It had one model-usage event, but no candidate event and no tool-execution-start event.

See [soda diagnostic retry](pi-real-provider-soda-revised-diagnostic-2026-10-07.json) and [product/policy diagnostic retry](pi-real-provider-product-policy-diagnostic-2026-10-07.json). These are separate real calls, retained alongside the planned sample failures.

## Wire-level A/B: `response_format=json_object`

One same-request diagnostic pair used the actual public Guide/SSE host and the same DeepSeek model, prompt, runtime and tools. A test-only instrumented copy of the built Node worker recorded only assistant message shape (`stop_reason`, text length, text-block count, native tool-call count, and allowlisted JSON keys). A Node preload observed main request bodies and, in the B arm, deleted only the top-level `response_format` field. It did not log URLs, headers, bodies or credentials. The production worker and request logic were unchanged.

| Arm | Wire observation | Main assistant shape and outcome |
| --- | --- | --- |
| A, field retained | One main tool-bearing JSON request observed; `response_format` present; no body mutation | Final assistant text was a JSON object with keys `content` and `tool_calls`, but native tool-call count was 0; host ended with `PI_UNKNOWN_REFERENCE`; no interim candidate was published |
| B, field removed | Three main tool-bearing requests observed; `response_format` removed from all 3; all other request fields retained | First tool iteration: plain text, 65 characters, 1 native tool call, `invalid_format`; second: empty text, 1 native tool call, `absent`; final: plain text, 141 characters, 0 native tool calls; host ended with `PI_ANSWER_INVALID`; no interim published |

The single wire-instrumented pair does not show a successful strict `{ "interim_message": ... }` payload alongside a usable tool call. Removing JSON mode changed the observed output shape in this pair but did not produce a valid interim message or successful final answer. It is a diagnostic experiment, not production verification or a quality pass. No parser fallback was introduced.

See the [A arm report](pi-real-provider-recipe-relations-ab-baseline-wire-v2-2026-10-07.json) and [B arm report](pi-real-provider-recipe-relations-ab-no-json-mode-wire-v2-2026-10-07.json). The B report confirms only the intended top-level field was removed and that no request content was recorded.

## Additional instrumented repeats and harness notes

Additional repeats of the same recipe relation request showed model-output variability. One completed repeat had one absent candidate alongside two native tool calls and a final structured answer with keys `answer_kind` and `status` ([report](pi-real-provider-recipe-relations-ab-baseline-instrumented-2026-10-07.json)). Other unmodified repeats ended in `PI_ANSWER_INVALID` with a final plain-text block of 664 characters ([report](pi-real-provider-recipe-relations-ab-baseline-2026-10-07.json)) or `PI_UNKNOWN_REFERENCE` with JSON text keys `content` and `tool_calls`, but no native tool call ([report](pi-real-provider-recipe-relations-ab-baseline-fetch-2026-10-07.json)). These repeats are diagnostic evidence, not an additional unbiased product-evaluation set.

Two tester-only setup failures are retained separately and excluded from the model-call denominator: a port mismatch ended before the Guide route ([report](pi-real-provider-soda-revised-port-mismatch-2026-10-07.json)); a diagnostic wrapper initially omitted `subprocess.PIPE`, so the request failed before starting the Node worker ([report](pi-real-provider-recipe-relations-ab-baseline-v2-2026-10-07.json)).

## Earlier prompt snapshot

The pre-revision sample remains in [pi-real-provider-smoke-2026-10-07.json](pi-real-provider-smoke-2026-10-07.json): one completed public Guide/SSE turn, 0 published interim messages, valid three-call usage/timing. That report predates `interim_candidate` instrumentation; its earlier opportunity count was hard-coded and cannot be combined with the observed candidate-event denominators above.
