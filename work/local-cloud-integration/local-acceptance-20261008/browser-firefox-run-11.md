# Firefox controlled browser acceptance — run 11

Run 11 is the first complete real-browser journey in this local worktree: the fixture and browser exited with status 0, and the launcher reports both process groups stopped. It exercises the checked-out Ceres UI, FastAPI, Pi worker, and LangGraph against scripted loopback models and controlled retrieval. It does not measure live-provider behavior, BGE/GraphRAG relevance, memory background work, or production merchant data.

## Frozen source and tools

- Worktree `HEAD`: `170fac0bc75fcc855897b073337ba218abeb5b7d`; tree `295499ee22cc30485d38eba82e96330a39d7d573`.
- Firefox WebDriver journey SHA-256: `1970fedfa38374c2e8dacfd1fc042aa264676818bd5b2e78e46277157a0ed6a7`.
- `frontend/src/QuestionChoices.tsx`: `1ffc28a2fe00c9bd73af43f7709e12b35afe9b1a3112e124492ab25578cff315`.
- `frontend/src/App.tsx`: `65ee70dadef0535eb7ec232382c2448bdf5292353e334d7eea83cfaa4ba33fef`.
- `runtime/pi/dist/worker.js`: `b3de5c2655878e88fbc9f5d8614aa33dba27e179413e4b8f3076ccf6dd1c7e97`.
- `backend/app/services/product_question_service.py`: `b6a83c2e75b390c5d437f5ddf0c0b34fdc79e6d19932649a3c1c2cef3c9ccac3`.
- Firefox 136.0; geckodriver 0.37.1; Selenium 4.50.0; Pi subprocess Node v22.19.0.
- Frontend dist file-hash aggregate: `a7b507fdbd25e7720b5383bebbb84c8ba048844ecc56931e1a015abb1693c819`.

The fixture uses a fresh SQLite/checkpoint directory and synthetic fixture rows. The UI, Pi SDK, and LangGraph are real. The provider and retrieval responses are scripted; the fixture explicitly disables the memory background worker. No `.env`, previous database/index/session, or holdout set was opened.

## Browser network boundary

The fresh Firefox profile used a local proxy. Its only allowed browser authority was `ceres-fixture-4fd6cde5c2edc90900505c91.localhost:58057`. The proxy logged 257 requests: 238 allowed to that exact authority and 19 denied external requests. HTTPS `CONNECT` was allowed only for that exact authority, where the proxy terminated TLS locally and forwarded to the fixture's loopback server. It blocked the browser's `example.com` HTTP and HTTPS probes and Firefox service/CDN requests. The fixture CSP also limits application connections to self. These records show no external browser forwarding.

The same random `.localhost` hostname and port were measured over HTTP and HTTPS. Firefox reported `isSecureContext=false` and `crypto.randomUUID` undefined over HTTP; over HTTPS with the fixture-generated certificate accepted in the fresh test profile, it reported `isSecureContext=true` and `crypto.randomUUID` available. This verifies the adapter's local HTTPS journey; it does not prove the documented default `http://localhost:8443` startup path.

The Pi child-process guard audit contains 44 rows: 11 actual Node v22.19.0 Pi/result-expression processes loaded the guard, and 33 provider fetches went only to the fixture loopback provider at `127.0.0.1:36813`. Browser proxy isolation and Node/Python child-process guards are separate evidence.

## Completed browser actions

The run completed the following in one fixture:

- Opened a product detail, added the item, used simulated checkout, and viewed the immutable order snapshot after demo delivery progression.
- Submitted a quality case with one affected sales package and an uploaded photo, then verified that evidence in the corresponding human ticket.
- Exercised same-order contact, a rejected yes decision followed by the pure “墨墨 · 订单售后” button without replay, an accepted role handoff, and no/uncertain/provider-error/timeout decisions preserving the original Coco request.
- Exercised mixed shopping and policy results with an explicit role boundary and no replay on the role action.
- Observed two different interim bubbles for the same run; the text repeated from the prior mixed turn was separately attributed by message/request IDs. Refresh restored the same stable history IDs.
- For the slow turn, verified that the newly added interim bubble was visibly inside the viewport while this request's receipt and event stream were both `running`, with no terminal event. Stop then persisted a `stopped` receipt and `turn.stopped` event; a later history read showed no additional message.
- Used the visible category button, product checkbox, quantity field, and “生成采购清单” button. The captured answer carried quantity `1`; the visible plan and public session projection contained one plan item at quantity `1`, while the cart stayed empty.

The interim-before-stop screenshot measured a visible area of 10,916 CSS px², opacity 1, and nonzero height. The settled two-bubble view also recorded visible geometry for both interim messages. Screenshots are retained under `tmp/browser-run-11/`:

- [Product detail](tmp/browser-run-11/01-product-detail.png)
- [Order snapshot](tmp/browser-run-11/02-order-snapshot.png)
- [Ticket evidence](tmp/browser-run-11/03-ticket-evidence.png)
- [Mixed result](tmp/browser-run-11/04-mixed-result.png)
- [Interims visible after completion](tmp/browser-run-11/05-interim-after-completion-visible.png)
- [Interims restored after refresh](tmp/browser-run-11/06-interim-restored.png)
- [New interim visible before stop](tmp/browser-run-11/07-interim-before-stop-visible.png)
- [Stopped state](tmp/browser-run-11/08-stopped.png)
- [Typed selection and plan](tmp/browser-run-11/09-typed-plan.png)

## Evidence and cleanup

- Full launcher/browser transcript, including `ok: true`, request-level results, and final cleanup: [browser-run-11.log](browser-run-11.log).
- Browser proxy allow/deny records: `tmp/browser-run-11/proxy-requests.json` and `tmp/browser-run-11/proxy-blocks.json`.
- HTTP/HTTPS origin facts: `tmp/browser-run-11/browser-http-context.json` and `tmp/browser-run-11/browser-context.json`.
- Actual Node child audit: `tmp/node-network-audit-11.jsonl`.
- Launcher reports `fixture_stopped: true`, browser return code 0, browser PGID stopped, backend PGID stopped, and fixture support source hashes unchanged before and after the run.

The source tree remains at the recorded commit; only this tester-owned worktree evidence is untracked. All earlier failed browser attempts remain separate and are not added to this run's pass count. In particular, run 10 reached the stop gate but exited 1 on a Selenium helper looking for `role=region`, while the product correctly rendered a named `<section aria-label>`. Run 11 uses the visible section label, completes the typed plan flow, and exits 0. The earlier harness and setup failures are preserved in their own logs rather than treated as product failures or combined with this result.

This result is limited to the single Firefox 136 HTTPS journey with the controlled model and knowledge ports listed above. It is not personal acceptance, real-provider validation, or evidence for every supported browser. The journey did not separately test duplicate-click idempotency or an active network disconnect followed by SSE reconnection; refresh restoration is not a substitute for those gestures. Other cloud HTTP/DOM results remain tied to their separately recorded source pins and are not added to this local run's coverage.
