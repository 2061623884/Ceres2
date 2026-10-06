# Controlled-test isolation follow-up

Verified 2026-10-06. Baseline: `3ba598656963b06e4250f73cfd2c9e566d68c9ad`.

## Problem and scope
After local live credentials were configured, pytest collection could instantiate cached Settings from root dotenv before the existing per-test controlled provider fixture. An application lifespan can also start the background memory worker. Foreground model mocking alone did not isolate that configuration.

## Change
Only test infrastructure changed: `backend/tests/conftest.py` installs explicit dummy provider/data defaults before collection, removes case-insensitive inherited aliases and proxy variables, disables dotenv discovery, and clears the Settings cache. The new subprocess regression uses synthetic data and rejects dotenv reads and networking. Fixtures may select their own loopback provider/data. Application configuration and user `.env` are unchanged.

The barrier covers direct pytest and capture-wrapper pytest. It is not a sandbox for arbitrary captured commands, external pytest plugins before conftest, or manually launched live scripts. Never treat controlled results as live-provider evidence.

## Independent review and verification
Standards and Spec reviewers closed the dotenv/import-order and lowercase-alias findings on the exact final files. The earlier Spec report combined an older source read with a newer hash; its finding was explicitly superseded by the corrected review.

- conftest SHA-256: `1f1bb7bffa7b29ca508cd67b8765621c024b28b7eb6b9cb656af2dce57c947f9`
- Regression SHA-256: `1b9f268780c0532d477494d072c340ec57443a2744394a4bdd6953d71700b933`
- Full controlled suite: **295 passed twice**, exits 0/0, separate executions.
- Four snapshots and current 322 source files match: `f84e7b2b06dcf009b88792a0b8333e7d4002b43c741fdebb7fc45d8f726ddd58`.
- Production code is unchanged from the previous 294-case pair; only the guard and its regression were added.
- Outer test execution used a synthetic environment, blocked dotenv reads and allowed only local fixture networking. No configured key was used or transmitted.

Summary evidence: [final-pair-verification.json](isolation_evidence/final-pair-verification.json). Historical raw runs remain in the cloud workspace under `work/ceres2-runtime-upgrade/16/test-runs/final-isolated-backend-01/02`.

## Remaining acceptance
Local configuration readiness was checked separately. Actual authenticated qwen invocation, real-browser E2E and user acceptance remain unverified. The manual connectivity helper must be user-launched and confirmed; neither saving credentials nor local readiness establishes provider validity or business acceptance.
