# Controlled browser fixture (Tester only)

Run through the dedicated Tester's guarded harness; implementation authors must not execute it.

Command:

    python launch_browser_fixture.py --source /absolute/frozen/source --frontend-dist /absolute/tester-built/dist --lifetime 300 --artifacts /absolute/test-evidence -- node /absolute/browser-journey.mjs

The browser command receives BROWSER_BASE_URL and FIXTURE_MANIFEST. Read the JSON manifest and install its synthetic cookie in the fresh Chromium context before navigating. This is fixture identity setup, not authentication acceptance. Manifest fields: base_url, product {sku_id,name}, owner_id, cookie, order_ids (two delivered synthetic orders), second_order_id, operator_token, scenarios, boundaries.

The launcher rejects source/.env or backend/.env by existence before application imports. It never reads their content. All provider settings are synthetic. Only PATH/PYTHONPATH and the dedicated Node guard audit/playwright paths are inherited; the subprocess gets a new HOME, TMPDIR, database and checkpoint. Tester must verify the real Node child guard; CERES_NODE_GUARD_AUDIT is required. Python also denies non-loopback connections/DNS and dotenv reads. Bindings use 127.0.0.1 port 0. The built frontend is served after API routes, on the same origin.

The browser runs only after public /health readiness. Backend and browser have separate owned process groups, bounded by the lifetime; the launcher terminates/waits/kills only those groups in finally. A temporary provenance-only manifest is freshly generated from tracked static fixtures; no old runtime DB/index is copied.

Scenario strings are in the ready manifest. Kev yes offers Momo; no/uncertain/error/timeout remain production navigation outcomes. Mixed produces shopping+policy+role boundary. Interim produces two separately audited messages; slow publishes one then waits in the controlled provider, enabling actual stop/reload tests. Typed uses the production category/product controls. Quality uses real LangGraph prepare_aftersales_proposal, one package, against the explicitly selected order; photos and confirmation use normal APIs/UI. The catalog, cart, order transitions, authorization and proposal/confirmation logic are unmodified.

Simulation limits: Pi and Kev model responses are scripted loopback HTTP; KnowledgeService.search is an explicitly controlled retrieval port with tracked-source manifest and deterministic candidate ranking, not real BGE/GraphRAG relevance. Background memory start/stop is explicitly disabled in this fixture; memory extraction/dreaming acceptance is not claimed. No paid-provider or human-language-quality acceptance is claimed.

Evidence should retain launcher/helper/test source hashes, frozen product/build hashes, ready manifest, actual guard records, browser artifacts, and cleanup result. Do not retain temporary database/checkpoint files as product data.

The launcher records all six support-source SHA256 values before startup and after cleanup, returns 70 on source drift, and retains backend.log, ready.json and lifecycle.json in a unique --artifacts subdirectory (even on failure). No runtime SQLite/checkpoint is copied there. Expression-only introductions use the real no-tool Pi worker and validator, with a neutral scripted introduction referring to a real host fact key.

For a non-browser backend-only check, pass `python /absolute/api_smoke.py` after --. This exercises actual Pi/independent audits/mixed policy/typed exploration and a real LangGraph order read through public HTTP, and asserts zero cart mutation. It explicitly reports browser_ui_acceptance=false. It is not a substitute for the Chromium journey.

## Official cloud-browser mode

Use --wait-for-cua without a trailing browser command, with --lifetime at most 900. The ready manifest includes entry_url and stop_file. The official cloud browser may open only this unique loopback entry_url; /__fixture__/start sets the predefined synthetic identity cookie and redirects to the same-origin frontend. This endpoint exists only in the test wrapper, never product source. All responses carry a restrictive CSP: self-only scripts/connect, self/data/blob images, self/data fonts, self/inline styles; no external frames/objects/forms. Do not use raw CDP or tunnels. Tester writes the exact emitted stop_file to request cleanup; timeout always cleans up the owned backend group. This route does not bypass an IPC restriction: it uses the separately available official cloud-browser tool.

Cookie isolation: each run generates an unpredictable `ceres-fixture-<nonce>.localhost` browser_url on its ephemeral port. Chromium uses its built-in localhost resolution; no hosts, proxy or OS settings change. The bootstrap rejects every Host except that exact host:port before setting any cookie. The cookie has no Domain attribute. `base_url` remains 127.0.0.1 for the guarded HTTP health/API smoke only; official CUA first checks browser_url/health then navigates entry_url. Never navigate generic localhost/127.0.0.1 to establish this browser identity. This avoids cross-port cookie collision in the cloud browser's existing profile.

Cleanup is verified independently for the two exact process groups created with start_new_session=True, even after a leader exits. The launcher allows up to five seconds after TERM, then sends KILL to that same surviving group and allows five more seconds. It reaps the known leaders and reports per-group observed signals/status. If group absence cannot be established, fixture_stopped is false and exit status is 75; no unconditional success claim, broad process search or unrelated PID/group targeting is used. The public descendant regression requires Tester-supplied CERES_BROWSER_TEST_SOURCE and CERES_BROWSER_TEST_DIST paths and deliberately spawns a TERM-resistant child within its owned group.
