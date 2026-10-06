# TASK01 selective migration

Source: read-only `Ceres-workspace/archive/ceres2-before-clean-20261005/` snapshot, inspected 2026-10-05. This is provenance only: no runtime imports, symlinks, database, node_modules, virtual environment, credential or active state is inherited.

Approved public seams: existing guide HTTP/SSE → actual Pi Agent SDK → read-only Python catalog service → persisted user-visible history/receipt; controlled HTTP model transport and stdio; transactional driver concurrency fault.

Selected source files:
- `runtime/pi/{package.json,package-lock.json,tsconfig.json,src/worker.ts}`: actual SDK 1.0.3, bounded tool runtime and sanitized lifecycle events; independently installed/built by Tester.
- `backend/app/services/pi_product_runtime.py`: host-owned candidate refs, finite clarification slots, host-rendered facts, subprocess budget and diagnostic boundary. Worker path resolves only inside the clean repository; added bounded event/frame buffers and host run-handle/sequence validation.
- `backend/tests/test_runtime_pi_product_query.py`: isolated two-owner synthetic catalog fixture and public behavioral scenarios. Imports adapted to canonical identity/guide modules; unrelated old cart endpoint assertions omitted because this slice exposes no cart tools or routes.

New implementation, not copied: guide SQL models, minimal guide HTTP/SSE API, atomic history/receipt service. Imports only clean `app.core`, canonical `app.models.identity`, clean `app.services.catalog_service`, SQLAlchemy/FastAPI/Pydantic and Python standard library. No old TurnStreamService, graph, shopping workflow or Mercury dependency.

Verification starts from zero. Red/green commands and results belong to dedicated Tester evidence. Controlled provider transport proves real SDK behavior, not live provider compatibility or autonomous model quality. Actual qwen3.8-27b and real-page/user acceptance remain explicitly unverified until secure configuration and fresh execution.

## Fresh verification outcome

2026-10-05 16:08 UTC: Dedicated Tester completed initial public RED, first actual-SDK GREEN, IPC correlation RED/GREEN and unexpected-host-diagnostic RED/GREEN. Final public test module passes 21 cases twice in 49.57s and 49.58s. Exact scoped four-snapshot fingerprint: `fed4017d9923ecc8ba976f65b16b0ea0f6513fb68fddd18b25222759382e66c0`. Evidence lives under `work/ceres2-runtime-upgrade/01/test-runs/final-pi-{01,02}` with comparison JSON. Runtime build/typecheck independently pass. These are offline controlled-provider results only; root approved controlled technical release at 2026-10-05 16:10 UTC after both independent reviews cleared. Formal task status is 待验收; real provider/page/user acceptance remains pending at TASK16.
