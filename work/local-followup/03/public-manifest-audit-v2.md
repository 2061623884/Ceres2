# Public local-followup manifest v2 audit

- Case set: `ceres2-local-followup-dev-2026-10-08-v2`, SHA-256 `032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d`.
- Static audit command: `python work/local-followup/03/audit_public_manifest.py` (exit 0).
- Audit script SHA-256: `18d7580676cc5b16668815277e87e8faf2b2a63351f9ffaae256c3aa8da6f0d9`.
- Machine-readable results: [public-manifest-static-audit-v2.json](public-manifest-static-audit-v2.json), SHA-256 `2149e44cc9b34f8a5385f0994350607d9c4d474d3b4b551effef9dd3443c4945`.

The set has 40 unique IDs and 40 unique scenario families, all split as public regression, with 20 core cases. Its 115 fact pointers resolve against current static fixtures, including the structured JSON pointer `experience.json#expression.keke`. The checks use 96 `eq`, 13 `min_length`, 2 `length`, and 2 `max` operators. Expected terminal states are 21 completed, 12 waiting confirmation, 3 waiting clarification, and 4 role-choice outcomes; the only declared follow-up actions are one `confirm_plan` and one `repeat_confirmation` on dev-01.

The dedicated pytest integrity check was attempted separately and failed on its then-current literal-substring pointer validator: the dotted JSON path exists structurally but not as literal text. Its source SHA at the attempt was `cbdca37bc5b129f9c0c86c4e7075a128d82f6baf3b9ec59a0e520546c03679a8`; the failed attempt and raw output are retained at [public-dev-manifest-integrity-v2-fail.md](../01/public-dev-manifest-integrity-v2-fail.md). The test file changed after that run; no corrected-version pass is claimed here.
