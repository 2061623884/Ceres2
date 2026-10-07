# T03 same-pin Spec supplement: non-primary references

Pin: `e315c387f31ac130e831b37544c7cf3e82f82a4b`, baseline `ccf272b752f096ce0d80f7d0a4f29b19c05b0a77`. Uses the already saved `t03-spec-e315c38.diff` and commit list. Static inspection only; no tests or product edits.

P2 — Non-primary reference fields can bypass the promised per-reference validation. T03 contract explicitly says “Python 逐引用校验”; story 8 says “混合合法引用都经过 Python 校验”. `runtime/pi/src/worker.ts:116–128` exposes independently optional reference fields. `backend/app/services/pi_product_runtime.py::_answer_value:644–654` accepts waiting with clarification_slot and returns before product reference checks. `_answer:481–492` supplements policy validation only. Thus a native completion containing status=waiting, clarification_slot=target and product_refs=['foreign'] is structurally permitted and its unknown product reference is ignored rather than rejected. Comparable non-primary references can be ignored by other early-return kinds.

This is a completion-contract validation defect, not demonstrated unauthorized execution or disclosure: ignored references are neither rendered nor used for business writes.

Minimal correction: at the Python boundary, reject reference fields inapplicable to the selected primary response kind/status, while preserving authorized composable policy_ref/policy_refs and role_boundary fields. Alternatively, if non-primary references remain accepted, validate each against its actual request/scope/current-state evidence. Neither approach requires multi-primary-answer orchestration or rendering unused references. Public native completion coverage should include waiting plus an unknown non-primary reference and confirm rejection/no final publication or business side effects; retain existing legal mixed-reference coverage.

The parent has now explicitly defined the minimal nonempty optional_items structure for the separate recipe finding: same ingredient_id and optional quantity_* shape as required items. This is newly clarified implementation scope, not a claim that the prior corpus schema already specified it. Re-review must use the forthcoming correction pin.
