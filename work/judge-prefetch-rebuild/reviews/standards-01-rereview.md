# Standards re-review: ticket 01 and DeepSeek transport

Reviewed 2026-10-07. Read-only source review of the six-file repair over the preserved ticket-01 implementation. This is not final four-ticket acceptance.

## Frozen candidate

- Baseline: `4bed9c891261e382122d424825b649989ea92c92`.
- HEAD: `ec625a27db5418f0851a5da946c384531534309c`.
- Full tracked comparison: `git diff --binary 4bed9c891261e382122d424825b649989ea92c92`.
- Full-diff SHA-256: `a9e058dcf742c47aed2a682ab2507e539235af609f79e3522e8527d6107261d3`.
- Six-file repair (`git diff --binary`) SHA-256: `500f395d80a9bdf6af9201a4f10d63ce254320cdb5cea8c773bf1ffbcf81b3f0`.
- Untracked product/test source: none; only generated evidence is untracked. No additional source hashes required.
- HEAD and both diff hashes rechecked unchanged at 04:53 UTC.

## Closed finding

**Prior P2, lost recovered Kev cause: closed at source level.** `backend/app/services/navigation_service.py:141–148` now correlates the recovered failure with session/request IDs and records the chained cause through `guide_run_service.py:243–250`. The existing helper emits fingerprints and stack-frame metadata, not provider messages, URLs, headers, or credentials. Original chaining remains at `kev_provider.py:68–71`. This satisfies `AGENTS.md:23` (retain original causes during recovery/conversion) and `docs/REBUILD-DECISIONS.md:38` (record genuine failure reasons). New controlled HTTP/validation cases at `backend/tests/test_judge_role_entry_public.py:314–358` check distinct fingerprints, correlation, redaction and replay.

## New findings

**None identified.** Boundary composition at `pi_product_runtime.py:331–340` and `pi_product_turn_service.py:224–227,257–264` retains validated primary/policy messages and generates a host-owned explicit navigation action. Strict boolean validation guards a real model-output boundary, supported by the prompt contract and malformed-marker fixture, consistent with `AGENTS.md:20–24`.

The unchanged exact-host helpers and seven transport consumers retain existing configuration and official-only fields, consistent with `docs/REBUILD-DECISIONS.md:82–85`. No new generic abstraction is warranted; smell heuristics do not override `AGENTS.md:15`.

## Limits

No tests, builds, installs or product edits performed. Earlier 46-pass evidence is not attributed to this candidate; independent Tester results must establish current execution status. Frontend remains deliberately excluded and pending local validation under `docs/REBUILD-DECISIONS.md:19–28`. Real-provider, browser and user acceptance are not asserted.
