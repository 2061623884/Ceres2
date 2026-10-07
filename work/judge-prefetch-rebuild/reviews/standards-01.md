# Interim Standards review: ticket 01 and thinking transport

Reviewed 2026-10-07. This is an interim read-only source review, not final four-ticket acceptance. No tests, builds, installs, or product edits were performed.

## Frozen source

- Baseline: `4bed9c891261e382122d424825b649989ea92c92`.
- HEAD: `a676f3ecf6ed4bd13052852cc7a78e41bc070afe`.
- Command: `git diff 4bed9c891261e382122d424825b649989ea92c92 --binary` (includes tracked worktree changes).
- Diff SHA-256: `5437bf0280969694abfbf368a2c614dc9802be4f4d1b386c9129de04e86d5167`.
- Additional untracked source SHA-256:
  - `backend/app/schemas/navigation.py`: `4722016d24edc408f5d915f7bd4a1ee38519a408ef98295146cb77a4b99b8a5c`.
  - `backend/tests/test_judge_legacy_navigation_public.py`: `1e5b3d42ad6cf3705f95282b1330ba264d18ef3efee9cb0e147f11ba976447a9`.
  - `backend/tests/test_judge_role_entry_public.py`: `f9b13a2f495ab4491b6187f80385784fbe42573743a2ed11dadd59615628aa6b`.
- All pins rechecked unchanged at 04:23 UTC. Generated evidence is excluded from source conclusions.

## Finding

**P2, documented-standard breach: recovered Kev failures discard their underlying diagnostic cause.** `backend/app/services/kev_provider.py:68–71` chains the original exception but reduces the recovery reason to its class. `backend/app/services/navigation_service.py:140–142` then consumes the exception and persists only that class. HTTP 401, 429, and 500 all become `HTTPStatusError`; distinct schema faults become `ValidationError`. Neither this catch nor a global handler records the chained cause. This violates `AGENTS.md:23` (preserve original cause when recovering/converting) and `docs/REBUILD-DECISIONS.md:38` (record actual failure reason).

Keep the safe public outcome/reason; retain correlated sanitized cause diagnostics server-side. The existing `guide_run_service.py:242–255` fingerprint/frame pattern is suitable. Do not log raw provider content, headers, credentials, or URLs. Add controlled fixtures showing distinct HTTP/validation causes remain diagnosable. This conclusion is statically demonstrated, not runtime-reproduced.

## Scope and limits

No other blocking Standards finding identified in changed authorization/replay, initial context, Python write boundaries, exact-host thinking helpers, or unchanged deadline/configuration handling. No heuristic smell elevated to a hard violation. Legacy eleven-way classification must remain retired. Frontend was unchanged and remains a separate local handoff; controlled test outcomes belong to Tester, and real-provider/browser/user acceptance is not asserted.
