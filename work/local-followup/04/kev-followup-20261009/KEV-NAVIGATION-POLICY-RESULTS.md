# Kev navigation, policy and browser pilot results

Date: 2026-10-09. This is additional evidence for ticket 01. It is not an accuracy sign-off or the formal 100-run baseline; 02 owns that baseline. Final 01 technical-gate status remains with the root task.

## Frozen services and sources

- Worktree HEAD/tree: `9e9be1da8ef7dd7ba630a2025e63835612e4795e` / `e28d6b06da5a174a6d739907dc4c5dfacaf7f6d8`.
- Isolated Ceres FastAPI service remains running in exec session `78420` at `127.0.0.1:8017`; the existing Kev service at `127.0.0.1:8009` was not restarted or changed. Health was HTTP 200 before the browser run, and both ports remained listening afterwards.
- Current approved primary model: `deepseek-flash`. Kev endpoint/model: local `127.0.0.1:8009`, `kev-latest`. No credential values are recorded here.
- `serve_baseline.py` SHA-256: `af65cd78c7045da48d186fdedf27e9306b1a41194e71b9e351a7d6a89f7dc3d8`.
- `kev_provider.py` SHA-256: `5059a7e61dda6590b57c17532fb96f6907db6b5c40ab213c728964bdba824566`; `navigation_service.py`: `0baa40f74f73a72f1f0ccc8eed5003acaba25ca0e71ff501458886a78892c0ce`.
- Momo query path sources: [`router.py`](../../../../backend/app/mercury/router.py), SHA-256 `8f7f52dcf16be76371f2508fbdba4078e8c39ab5f9a8a64bc953cffaafdab3c3`; [`graph.py`](../../../../backend/app/mercury/graph.py), `4712cbb8721d75deeb93c23194c53f890546b28cc1d990baad588a9ccfa30fc6`; [`provider.py`](../../../../backend/app/mercury/provider.py), `b80df9bfcf4196028e3ea3a1f939afaa882d33b9a9dd354be560a513801ed2f1`.
- Demo policies SHA-256: `7a370431a1a9c2df2b818218f3c54cb01946f93fa027aad44021dd1637f10502`; hybrid index: `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`; GraphRAG manifest: `3aad90d9d498e614ddd30799275881c5fc53b9f45c1dbba5fc62eb067cdb3787`.
- Browser used system Firefox `136.0`, GeckoDriver `0.37.1`, and the existing built UI (`index.html` SHA `903798b07e1f3ffc4b5518f1dd0cb784c0a6b8e7e716c31449cc63dd16cebda0`, JS `3c49e724bfad7a3439837887a262ca94e1837abe9081845259c07bd8493e24d4`, CSS `3f414980b295757eb960743c65265df6994846dbb88a1fb0c9b2b26acdf1f247`). A fresh headless Firefox profile used an HTTPS loopback authority at `localhost:8447`; a local exact-authority proxy served the built UI and forwarded browser API routes only to 8017. Browser attempts to reach 15 external authorities were blocked. This validates the browser harness boundary only; it does not isolate the API process from its approved provider network.

## Direct Kev protocol probes

The existing [9-call protocol pilot](./KEV-PROTOCOL-PILOT.md) remains a separate layer. Nine direct provider calls used the current production `kev_provider` contract: all 9 returned a valid schema under the existing 3-second timeout. The 8 prelabelled positive/negative probes matched their predeclared branch; the ambiguous probe returned `uncertain` and has no gold label. This is a small contract sample, not an independent quality estimate. The JSONL is local and ignored: [`kev-protocol-pilot.jsonl`](tmp/kev-protocol-pilot.jsonl), SHA-256 `9347bf6f52b5ced56ffaed0e990812efd1be6d1d4704092d4af42763611a8f53`.

## Public navigation API matrix

The frozen [navigation plan](./NAVIGATION-PILOT-PLAN.md) declared six unique cases and one exact same-body replay. The saved [`navigation-pilot.json`](tmp/navigation-pilot.json), SHA-256 `79eb375835386a9f837e49eee7ac018f34be1dbc8b54f9bb681d088758ef094b`, records 7 HTTP `/routes` posts and 6 distinct judgments. All HTTP results were 200; observations were 2 `yes`, 3 `no`, and 1 `uncertain`. One `yes` case was accepted and the other declined. The accepted case retained the exact original-message hash; the decline left the opening on Keke with no handoff.

For the same-body replay, the safe receipt matched and the global `kev-latest` requests counter stayed 530→530 during its before/after snapshot. The first route window had requests 529→530. These values are a consistency check, not per-owner telemetry: the model card exposes service-global successful-batch counters, and outside traffic cannot be excluded.

## Two policy-to-Guide public turns

The [predeclared policy plan](./POLICY-PREFETCH-PILOT-PLAN.md) selected public cases `dev-24` and `dev-36` from the 40-case development set, each with a fresh owner and one Guide request. The source dataset is `ceres2-local-followup-dev-2026-10-08-v2`, SHA-256 `032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d`. Both completed HTTP/SSE requests returned `business_facts`, met their declared machine checks, and left the plan null. Both entry judgments were `no`; both policy judgments were `yes`; each made one successful prefetch from `Ceres 模拟服务规则` version `2026-10-07-demo-v1`, index revision `fb981e66e2cd272a9a32a6da9db49512dd7a55142e3ccf59afbdc43ee1bb2c01`. Each recorded zero policy-tool lookups and zero policy-reuse events; therefore the trace proves a successful prefetch followed by a final answer, but does not contain a distinct reuse event.

| Case | Policy judgment | Prefetch lookup | Guide stream client time | Final answer |
| --- | ---: | ---: | ---: | --- |
| `dev-24` | yes, 242.667 ms | success, `prefetch`, 4,362.305 ms | 7,388.045 ms | accepted, one message, 519 characters |
| `dev-36` | yes, 233.319 ms | success, `prefetch`, 56.848 ms | 2,733.437 ms | accepted, one message, 547 characters |

Both client stream timings were below the configured 15-second Guide budget. They start at the Guide stream request and exclude bootstrap/session creation, so they are not full page-entry timings. Existing lexical cue checks matched their expectations, but they are not human semantic ratings or blind quality scores.

The existing raw safe projection [`policy-guide-pilot.json`](tmp/policy-guide-pilot.json), SHA-256 `891f87cc5c399c61d472cc7e13229c94d6fcb93ec1709033d8750a10df63e18c`, initially showed empty usage maps because its extractor used the wrong field names. A read-only projection from the same isolated database, with no provider calls, joined `provider_call_start`/`provider_call_end` by call id and corrected that shape. The helper is [`reconcile_policy_usage.py`](tmp/reconcile_policy_usage.py), SHA-256 `b3d30761a9b8bc1fa6295435e67031e03f31e55dbab8174a05a253318023af7a`; its output is [`policy-guide-usage-reconciled.json`](tmp/policy-guide-usage-reconciled.json), SHA-256 `94e7e9aa68c30b8f75cfa38aaae6e0ab810ebc07ce6e3b097a8ab74875a38f50`.

| Case | Model/host | Calls | Input | Output | Cache read | Cache write | Total tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `dev-24` | `deepseek-flash` / `api.deepseek.com` | 2 | 11,780 | 131 | 10,368 | unknown | 11,911 |
| `dev-36` | `deepseek-flash` / `api.deepseek.com` | 2 | 11,812 | 133 | 10,368 | unknown | 11,945 |
| Total for these four primary Pi calls only | same | 4 | 23,592 | 264 | 20,736 | unknown | 23,856 |

These token figures apply only to the four instrumented primary Pi calls in the two Guide cases. They do not cover Kev, Momo's Mercury query, or memory jobs, so total usage/cost for the whole 01 work is unknown. `cacheWrite` was absent in every provider event; no cost was inferred.

## Real Firefox route prompt and accepted handoff

This is distinct from the earlier manual role-button pilot. The manual pilot clicked “墨墨 · 订单售后” directly; it made no `/routes` call and is not route acceptance evidence. Its successful local result is [`browser-role-pilot.json`](tmp/browser-role-pilot/browser-role-pilot.json), SHA-256 `4e0cdaa368a9ac6c690ed9a6ae0d12a56abe0ab3077c83c35302d9aa4e03fa71`.

The authorized one-off [browser route plan](./BROWSER-ROUTE-PILOT-PLAN.md) was executed once from the visible UI in the fresh Firefox profile. Its exact synthetic input was not copied into another eval set; its SHA-256 was `afefc919769712a15f1ad2a1ce52b2ae59eaf91da9b9c69c385f6331a05a55b4`. The order number was only text; `selected_object` stayed null.

- One Keke submit generated one `POST /routes`: HTTP 200, Kev judgment `yes` in 329.102 ms, `status=switch`, target `momo`, `show_prompt=true`. The visible prompt appeared 451.482 ms after Enter. The prompt screenshot is local/ignored: [`01-route-prompt.png`](tmp/browser-route-pilot/01-route-prompt.png), SHA-256 `17af43a90fc15332d0b4f1be7dae767888ef2e6fa01490ad781855846681046c`.
- The page sent one `prompt-displayed` acknowledgement and one visible acceptance click. `POST /switches` returned HTTP 200, role `momo`, handoff present, selected object null, and the original-message hash matched the submitted text.
- Momo automatically issued one public `POST /turns/stream` with the same message hash and routing request. It returned HTTP 200 with `accepted`, one `answer.delta`, and `turn.completed`; there was no SSE error. The Momo panel became visible 261.397 ms after the acceptance click; full stream duration was not separately timed. The UI visibly reached Momo's order-selection prompt. No order was selected and no cart, refund, return, quality, fulfillment, or after-sales confirmation was clicked. The final screenshot is local/ignored: [`02-momo-after-handoff.png`](tmp/browser-route-pilot/02-momo-after-handoff.png), SHA-256 `7cf20adbd291e581845b6891e5289c78995c08fc706a0322d14b410aa8f83b90`.
- Browser proxy evidence contained 62 allowed requests, all to `localhost:8447`, and blocked 15 external authority attempts. There were no business write requests; `GET /cart` was a read. The accepted route path did not select or query a specific order. The UI loaded its standard simulated-order list for the picker; no item was selected and no business result was requested.
- The final page is consistent with the order-selection wait in the current Mercury query flow. That flow invokes `QueryChatClient` before the host emits the no-order prompt; the SSE had no error and completed. The Mercury query does not expose provider call/token usage in its public response, so its exact usage and call telemetry are unknown. The isolated DB aggregate at the end had `cart_items=0`, `simulated_orders=0`, `purchase_ledger=0`, and zero after-sales proposals/applications/receipts/human tickets.

The raw harness file [`browser-route-pilot.json`](tmp/browser-route-pilot/browser-route-pilot.json), SHA-256 `d2924cafc18bde24fe12c0d26e2ab5dd6c11a8c855c155920d2dd1b216a93219`, records the safe route/switch/SSE fields and transport rows. Its offline corrected summary is [`browser-route-pilot-derived.json`](tmp/browser-route-pilot/browser-route-pilot-derived.json), SHA-256 `ab4d3b2edb6ba7b8478d7583d9d24853a831401e919039bfdc3ece9623345a00`; summarizer SHA-256 `6685694f3aa452d6e1d6910aa7cba461fa3cf9e38e028ce315303f5a41e668a7`.

The browser command exited 1 only after the full UI journey, at `collect_safe_transport_evidence`, because the harness's counter-delta formatter indexed `before["models"]` after it had already selected a per-model row. This is retained as a harness failure, not hidden or attributed to product behavior. Both model-card snapshots had already been saved; a separate offline summary calculated `count` 568→569 and `requests` 569→570 for both card names. Per the Kev source contract, `count` is completed model batches and `requests` counts batched encodings; neither is a complete HTTP request log or per-owner counter. The delta is global and may include unrelated traffic. No route or model request was repeated to repair the report.

## Isolated state and limits

After both policy turns and the browser route handoff, the isolated database aggregate showed two `extract/completed` memory jobs and zero Dream jobs. Memory job rows have no provider usage fields; no tokens were inferred. This is an aggregate for this isolated DB, not a per-request attribution. The two Guide primary Pi token records above do not include Mercury or Memory.

The API response and UI handoff establish the public route/acceptance flow and that the original request reached Momo. They do not establish semantic correctness of the route classifier, refund eligibility, order validity, or after-sales completion. The synthetic order text did not select or look up an order. This sample is separate from both the six-case navigation API matrix and the formal 100.

## Harness failures retained

- The earlier manual role-button browser harness first missed a visible navigation control with its text selector; the initial JSON summary was overwritten before it could be preserved, so its exact exit status is unavailable. The failure screenshot remains under `tmp/browser-role-pilot/failed-open_keke_through_visible_navigation.png`.
- Manual harness attempt 2 reached the visible Momo state, then exited 1 in summary generation with `KeyError('path')` while classifying CONNECT rows. Its safe summary and screenshot were preserved as `browser-role-attempt-02-summary-error.json` and `browser-role-attempt-02-momo-visible.png`; the corrected third manual run succeeded, but was direct role selection only.
- The route browser attempt described above exited 1 after completing the handoff because of its `KeyError('models')` counter formatter. The offline derived summary preserved the journey evidence; there was no second route/browser/provider attempt.
- The first offline policy-usage reconciliation helper looked for nonexistent camel-case suffix fields and therefore produced null model/usage values. Its field projection was corrected offline using the actual event schema; the provider was not called again. A read-only aggregate query also initially asked for a nonexistent `mercury_cases.status` column; the actual field is `query_status`, and the corrected aggregate showed one `awaiting_order` and two `ready` cases. That failed read-only query made no database writes.

The WebDriver session, local UI server, and exact proxy all stopped cleanly; GeckoDriver exited 0. The API remains running for the next tester in session `78420`; Kev remains on its existing `8009` service. Raw run JSON, screenshots, browser logs, certificate, database, index, and model files are ignored local artifacts and are not suitable for Git staging.
