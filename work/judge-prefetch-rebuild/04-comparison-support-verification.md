# Bounded comparison support: controlled verification

Dedicated Tester, 2026-10-07. **22 support tests passed**, including the actual current application and Pi SDK through a loopback fixture. This helper is separate from the published core's 558-test backend gate. No real-provider experiment, old/new performance result, browser journey or user acceptance is claimed.

## Tested identity and evidence

- Canonical HEAD during final captures: `56f0e6f1d4e1e42d4e574f09df55fde0dce8615f`.
- Runner: `live_compare.py`, SHA-256 `ec4deeba2a98c2f028f7316b733d42507cc449466b5517688291465fd15cd8e5`.
- Test module: `verification_tests/test_live_compare.py`, SHA-256 `96a2027125a3facd302dda44ed1917bc110ef7a72c1cc0d565d483b4d62f6fa9`.
- Core's 248-file manifest remains `7c86cf268f5f4d7055626d6db1e3970d23735bd313ed148f638ede0a02c4368f`; no product change was made for this helper.
- [Final source/check/child audit](04-comparison-support-final-source.json) records the final helper, harness, core and generated-build maps, exact commands, source-provenance snapshots, sanitized smoke results and raw artifact hashes. [All 27 captures](04-comparison-support-history.json) retain failures, diagnostic probes and superseded passes.

| Label | Scope | Result |
| --- | --- | --- |
| `04-compare-actual-app-dependencies` | Exact installed Python locks/compatibility and Pi dependency tree | Exit 0; 62 locked Python versions match |
| `04-compare-actual-app-pi-build` | Current Pi typecheck/build | Exit 0; 8.696 s |
| `04-compare-alias-green-01` | Actual current app/public APIs/Pi SDK, same-source loopback smoke | **2 passed**, 10.32 s pytest / 10.658 s capture |
| `04-compare-final-full-02` | Entire support module, no exclusions | **22 passed**, 20.18 s pytest / 20.506 s capture |

Both smoke parameters are included in 22. Final smoke and full capture share exact source, helper/test and harness hashes before/after, with stable per-run launchers. The earlier dependency/build records apply to the unchanged core/runtime; subsequent fixture-test edits changed their helper-harness hash, so those records are not mislabeled as an identical final helper snapshot. The generated runtime artifacts match the final core build byte-for-byte.

## What the controlled tests establish

- No-argument preview does not import settings, read dotenv, use network (including loopback/DNS), start a subprocess or create output. Invalid caps/repeats/order/cases/provenance fail with specific safe codes before settings/output. Existing output is preserved.
- Local read-only source description and manifest validation pin source revisions/trees, runtime build attestations, static facts, prompts, numeric declarations and dependency locks. Unsupported/dirty sources fail closed. Build revision is a human attestation; a matching hash is not proof that a human actually rebuilt it.
- Static policy/source literals can be extracted into constants without a false fact mismatch; changed facts still reject. The exact historical/current Kev source timeout literal comparison likewise accepts unchanged 3.0 and rejects deliberate 4.0. No application import is used to inspect those facts.
- Synthetic execution gives each sample fresh temporary database/checkpoint paths and application-created owner/session. Deadline and cancellation preserve partial summaries and unstarted counts. A proven fixture-owned descendant is stopped before it can escape; cleanup never targets unrelated process groups. Fake key/provider-body text is absent from stdout/stderr/journal.
- The separate blocked-Git regression proves that source metadata waits obey the same execution cap and cancellation signal. The final .2-second case ends as deadline with zero samples; cancellation preserves a cancelled summary. Source-check success is recorded only after validation actually finishes.

## Actual application/Pi smoke, with explicit limits

The final public CLI smoke creates two independent temporary checkouts from identical current tracked product/static source and copies the matching generated Pi build. It reuses only this rebuild's verified Python virtual environment and locked SDK dependencies as a controlled test toolchain. Application imports resolve to the copied source and configuration root checks remain active. It uses a locally owned HTTP fixture, synthetic key and temporary business state; no dotenv or real configuration is supplied.

For both uppercase and lowercase supported configuration names, two chat samples complete through real bootstrap/navigation/Guide APIs and the actual Node Pi SDK. Each result retains **three observed primary Pi turns**, **two tool starts**, policy judgment **no**, and **zero policy lookups**. All four actual Pi worker PIDs in each final capture have guard-loaded audit events, with no unexpected guard block. Source/build snapshots agree across both copied checkouts.

The journal correctly calls this `same_source_smoke`. It is not an old/new result or a semantic-quality assessment. The optional CLI's policy/mixed/unmatched cases were not all executed against the actual app in this smoke; those core behaviors have separate backend public tests. Provider HTTP count, token usage, cost, render timing and quality remain `unknown`, not zero. The helper labels thinking transport and payload alignment unverified unless separately established. Observed SDK counters are not reconstructed into unobserved provider metrics.

## Failures retained, not relabeled

- Preview, manifest validation, source description and frozen provenance each began with a public RED against the absent/minimal implementation.
- The first static-policy comparison rejected harmless literal extraction; the repaired AST inspection retained changed-fact rejection. Its real baseline/current literal probe is preserved separately.
- Lifecycle RED initially reached the unimplemented execution branch. The first GREEN attempt then exposed a synthetic fixture import error: missing `app/__init__.py` allowed the canonical package to win. A read-only import-resolution proof confirmed this; the product-root isolation check correctly blocked before samples. A fixture-only initializer repaired it.
- The blocked-metadata RED reproduced exceeding a .2-second total limit and SIGINT yielding no partial journal. The narrow shared deadline/cancellation repair passed all 19 then-existing tests.
- The first actual-app RED rejected the current named Kev timeout declaration. The literal-only descriptor repair passed the historical/current equality and deliberate changed-budget regression.
- The next smoke failed at seeding because linking only a Python executable lost virtual-environment metadata. A guarded provenance probe confirmed base Python without SQLAlchemy. Linking the verified complete test environment preserved dependencies while retaining copied application imports. No network guard or real-provider boundary was relaxed.

- The lowercase alias RED reproduced a preflight model-configuration mismatch because Settings accepts case-insensitive aliases but the supervisor dropped lowercase names. The minimal repair matches only the existing eight configuration keys case-insensitively, preserving spelling/order and temporary database overrides; it does not forward arbitrary environment variables. Both uppercase/lowercase actual smoke parameters and the full 22-case suite passed. The prior 21-test record and its three curated files remain preserved under `evidence/04-compare-final-full-01/curated-21-checkpoint`; they do not certify this changed runner.

## Handoff boundary

See [LIVE-COMPARE.md](LIVE-COMPARE.md) for the human-operated procedure; its review gate is separate from these test results. Agents did not execute against real credentials. Any real run must be explicitly human-triggered with deliberate finite limits and matched source/build/configuration. Local process cleanup cannot cancel a request already accepted by a remote provider or guarantee remote billing stops immediately. Application lifespan may start its independent memory worker; this is part of exposure, not hidden free work.

These support results do not change the outstanding frontend/browser, real-provider, memory/Dream observation or user-acceptance requirements recorded in the core handoff. They do not authorize a spending budget or claim deployment/publication by themselves.

Final handoff document was completed after the tests: `LIVE-COMPARE.md`, SHA-256 `bcaa110e4bb2a92e6be08643a6c453f96a8a35e30e882f8149f7574f9ff2ca51`. This post-test documentation pin is separate from the original captured document hash, which remains unchanged in all raw evidence. Runner and test bytes did not change; documentation review remains separate.
