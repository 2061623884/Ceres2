# T03 Spec correction re-review

Frozen HEAD: `09ed3a3b54a0831b2774a5338cd0c5cb703c9e88`; prior reviewed pin: `e315c387f31ac130e831b37544c7cf3e82f82a4b`. Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T03-native`, clean at inspection. Commands: `git diff e315c387f31ac130e831b37544c7cf3e82f82a4b...09ed3a3b54a0831b2774a5338cd0c5cb703c9e88` and `git log --format=fuller e315c387f31ac130e831b37544c7cf3e82f82a4b..09ed3a3b54a0831b2774a5338cd0c5cb703c9e88`; outputs saved alongside.

## Result

Both prior P2 Spec findings are resolved by static inspection. No new missing, incorrect, or unrequested behavior identified in this correction delta.

1. Optional recipe facts: spec story 11 “必需/可选食材来自规范事实” and the newly approved minimal optional-items contract are implemented in `backend/app/services/pi_product_runtime.py::_answer_value`, recipe_facts branch. Optional items are included in source membership checks, rendered with recorded quantity or explicit “用量未记录”, and empty arrays render “来源未记录可选项”. The optional/required union is restricted to read-only candidate lookup; canonical purchase requirements are unchanged. Regression source includes nonempty, empty, unknown quantity, optional-only ingredient, and forged membership cases with no plan/cart assertions. The documentation accurately identifies nonempty optional structure as newly defined, rather than historically established.

2. Non-primary references: T03 “Python 逐引用校验” and its clarified one-primary-result boundary are enforced in `PiProductRuntime._answer` before dispatch. A host-side applicability map rejects unrelated primary reference fields, including all primary reference fields on waiting. Applicable fields continue through their existing scoped evidence validation; policy_ref, nonempty policy_refs, and role_boundary composition are preserved. Regression source covers waiting/product_refs, status/dish_refs, and policy_result/general_ref, asserting no final answer publication or cart changes. The correction does not introduce multiple primary answers or treat ignored references as prior unauthorized execution.

## Limits

No tests, installs, runtime services, real APIs, or repository edits were performed. The current Tester run has not been inherited as passed. This is only the two-finding correction delta; T02 final integration, same-pin affected verification, and final whole-branch independent review remain separate gates.
