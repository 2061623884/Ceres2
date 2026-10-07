# T05 supplemental coverage handoff

Exact candidate4278eea (branch integration/t05-integrated-ui). Production remains byte-identical to656cfef; only test additions after that independently reviewed production pin.

New controlled DOM suite: work/local-cloud-integration/05/ui_demo_contracts.mjs, modes product/aftersales/orders. Sole Tester reports stable terminal GREEN for all three: t05-demo-product-dom, t05-demo-aftersales-dom, t05-demo-orders-dom. Actual retained React components and their client modules exercised against explicit synthetic responses, not a browser or real backend claim.

New real public HTTP suite: work/local-cloud-integration/05/http_demo_contracts.py, launched by existing bounded safe fixture. Initial test script used POST for Mercury selection and received405; test-only correction4278eea uses actual PUT contract. Corrected terminal GREEN t05-demo-public-http-corrected,21 public requests; product/helper/harness hashes stable and cleanup complete.

Covered behaviors: current product detail and explicit cart add, pending-click suppression, unavailable/unknown-price/read-error states; checkout idempotent replay; sequential demo progression with invalid skips/stale versions rejected409; unchanged item/amount snapshots; problem quantity overcount rejected422; photo upload error/retry in DOM, versioned photo/proposal/explicit confirmation; confirm replay identical, exactly one receipt/application/photo linked to ticket; operator ticket-specific photo bytes verified; object URL cleanup.

Production source did not require modification in this coverage pass. This is supplemental to earlier role/interim/typed/contact/snapshot and order-race DOM/client evidence, strictTS and builds.

Browser gate remains blocked, not passed: raw Chromium launch IPC EPERM; official CUA unique-host health URL ERR_CONNECTION_REFUSED before UI/cookie access. Neither DOM nor real HTTP results substitute for native browser layout/interaction acceptance. Original browser_journey.py remains unexecuted end-to-end. No real-provider or retrieval-quality claim.
