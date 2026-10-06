# One-command real-model API integration batch

Preparation only until you personally run the command. This is **API integration through the actual FastAPI application lifecycle, real Pi SDK and real LangGraph**. It is not a browser test, browser workaround, or TASK16 acceptance.

## User command

From the Ceres2 project directory, personally run:

```bash
.venv/bin/python work/live-validation/run_live_batch.py
```

No key belongs in that command, terminal history, chat, screenshot or report. The child loads the existing root `.env` through the application's normal Settings loader. It never prints that file or the key. Existing shell environment still takes precedence, as in normal application startup. The command fails closed if the configured provider is not `https://discovery-api.intern-ai.org.cn/v1`, any of the three models is not exactly `qwen3.8-27b`, credentials are absent, demo mode is off or shopping writes are paused. It makes no fallback to another model/provider.

This launch is your manual start of the **whole bounded batch below**, including model requests and automatic background extraction/Dream scheduled by normal application startup. There are no intermediate prompts or manual clicks. It sends the configured provider credential to that provider, with synthetic shopping conversation, current demo catalog facts, generated synthetic order/refund facts, app system prompts and eligible synthetic memory sources. Normal provider usage charges may apply. No real purchase, payment, delivery or refund occurs. No operator token is sent.

Only run where that provider's outbound access is permitted. A denied provider/network route is a failure to report, not permission to bypass it. The batch opens no local HTTP listener, uses no port/proxy/browser and does not resolve prior browser restrictions.

## Scope and bounds

- Creates a new private run directory and a new isolated business DB/checkpoint pair each time; process overrides replace only the two DB paths. Existing `.env`, databases, checkpoints and services are never edited, reused or deleted.
- Seeds 65 static catalog products, 65 simulated Offers and one store. Verifies no prior owners/carts/orders/applications/memory.
- Runs at most five guide turns and one Mercury query, stopping immediately if a required stage fails. Each guide turn retains the application's existing 15-second/five-tool-round protection; Mercury retains its own 15-second/five-round budget. Ordinary explanation may invoke the app's additional same-model claim checker. These are application-level bounds, not an exact invoice/network-request count; SDK transport behavior is not replaced or instrumented.
- The worker has a 240-second total wall-clock cap. Normal background extraction/Dream is enabled throughout that window, including during shutdown; its calls use the application's 20-second timeout and zero SDK retries. Memory observation itself waits at most 35 seconds, then reports pending/missing work. The supervisor terminates only its own process group, including any surviving Pi child. Ctrl-C cancels that owned group. Cleanup does not delete any DB or evidence.
- No installation, build, dependency modification or service restart is performed. Uses this project's existing `.venv` and compiled Pi worker.

## Actual journey and automated consent

By launching this synthetic batch, you instruct it to:

1. Compare current drinks with real Pi; require at least two returned comparison candidates and no cart change.
2. Select the first actually returned candidate, quantity one, budget ¥100; require an actual model-created matching plan and no cart change. If that exact plan has a budget quote within the ¥100 scope, accept the displayed quote through the revision API, separately from cart confirmation.
3. Explicitly confirm that exact versioned single-item plan through the cart confirmation API; replay the same confirmation and verify exactly one cart effect.
4. Preview and explicitly confirm simulated checkout; replay and verify exactly one new simulated order.
5. Select that actual new order in Mercury. Ask the real model for an unshipped whole-order refund proposal, reason “买错了”. Require a real model-created proposal for the same order; never manufacture a proposal when the model fails. Verify no receipt before consent, explicitly confirm it, replay and verify one durable “requested” receipt, never “refunded”.
6. Ask an ordinary question, express one synthetic stable preference plus a one-off ¥30 budget, and stop one further guide request. Record actual results, verify cart/plan protection, then observe natural automatic memory jobs/records. A model deadline/tool-budget stop is protection, not success; a waiting clarification is not completion.

The sequence does not attempt operator handoff, full historical multi-dish repurchase, deliberate Dream threshold creation, memory correction/deletion/restart or browser close/reopen. Those gates remain untested. Natural Dream jobs, if any, are recorded only as observations; ten prompts are never treated as ten extracted records.

## Evidence to return

The terminal prints one directory ending in `/evidence`. Send that directory's files back:

- `manifest.json`: commit plus content hashes of current source, compiled Pi, dependency locks and static seed; model/provider identifiers; fresh paths; declared limits
- `events.jsonl`: exact allowlisted request/response/event fields, synthetic prompts, actual IDs, per-stage UTC/elapsed times, statuses and assertion results
- `initial-state.json`, `memory-state.json`, `final-state.json` when reached: named authoritative counts and eligible memory evidence, never generic database dumps
- `summary.json` when the worker finishes and `supervisor.json` in all launch outcomes

Only share `/evidence`, **never** its sibling `/private-state`, `.env`, full DB/checkpoint, headers/cookies, raw terminal traces or credentials. The positive field allowlist omits unknown fields and records an omission count. Known credential values and common credential patterns are redacted from retained strings; removed values are marked. Provider/app stdout and stderr are discarded, never copied into reports. No complete raw-provider-exchange claim is made. Poll-event receipt time is when this client observed it; Mercury TestClient SSE is buffered, so its true first-byte time is unavailable.

Exit 0: bounded API scenarios completed and a matching automatic-memory record was observed. Exit 2: core/API checks passed but matching automatic memory was not observed. Exit 1: blocked/failed required stage. Exit 124: overall timeout. Exit 130: cancelled. A successful exit still does not prove real browser operation, full TASK16 coverage, two independent live runs, or user acceptance.

If interrupted or failed, keep the failing evidence. Do not replace it with a successful run. A future rerun uses a fresh independent directory and is another user-launched live batch.

## Offline implementation checks (Tester only)

The inert harness tests never import application Settings, start the live worker, read `.env`, open a socket or contact a provider. Dedicated Tester uses a minimal environment and runs:

```bash
env -i PATH=/usr/bin:/bin HOME=/tmp .venv/bin/python work/live-validation/test_live_batch.py
```

This is synthetic harness validation, never real-model evidence. Agents must not execute the user command above, directly or indirectly.

Redirect note: the initial provider URL is pinned. Redirect handling remains that of the existing application SDKs/default fetch; this harness does not instrument each transport hop or claim redirects are disabled. No redirect/security workaround is added. Installed Python httpx strips Authorization across origins; the Pi OpenAI SDK uses default fetch.
