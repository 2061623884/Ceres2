# Kev policy prefetch and Guide response pilot plan

Status: predeclared before execution; not a quality pass.

## Frozen public inputs

Source dataset: `evals/ceres2-local-followup-dev.json`, version `ceres2-local-followup-dev-2026-10-08-v2`, SHA-256 `032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d` (40 public regression cases). The two cases below retain their original messages and checks. They are not private acceptance cases.

| Case | Exact message | Existing expected behavior and checks |
| --- | --- | --- |
| `dev-24` | 签收后多久可以按无理由退货规则申请？ | Explain the seven-day window and returnable-product flag, distinguish unknown order facts, and make no eligibility promise. Checks: `capture.status == completed`; `after.guide.plan == null`. |
| `dev-36` | 生鲜商品是否一律不能退？只想了解一般规则。 | Distinguish no-reason return limits from quality, missing-item, wrong-item, and safety issue registration; do not blanket-refuse. Checks: `capture.status == completed`; `after.guide.plan == null`. |

These are two independent, fresh-owner, single-turn public observations. There will be one execution per case and no automatic retry. They are not part of the 100-run baseline and do not change the existing public cases or rubric.

## Measurement contract

- Use only the isolated Ceres public API at `127.0.0.1:8017`; each case gets a new cookie, owner, and Guide session. Submit the exact dataset message once through `/api/v1/guide/sessions/{session_id}/turns/stream`.
- Preserve the existing 15-second Guide deadline and 3-second Kev timeout. Record client wall time separately from server/runtime timings. A timeout, provider/schema error, rejected run, or incomplete SSE is retained as observed; do not retry it.
- Capture only safe structured fields: HTTP status, SSE event types/sequence and elapsed values, Guide terminal status, answer kind/message ID/hash/length, role-entry and policy-judgment outcome/elapsed/reason codes, policy lookup origin/outcome/source revision, policy reuse count, primary provider stage/model/observed token usage, and current Offer/plan checks. Do not store raw provider request/response bodies, credentials, or full session history.
- Sample the existing Kev model-card numeric counters before and after each complete Guide run. The counters are service-global, not per-owner; concurrent external requests cannot be excluded. A delta is an observation window, not proof of sole attribution.
- Inspect only aggregate counts/status/usage for memory jobs tied to these two new runs. Keep their extraction work separate from the formal 100-owner batch.
- No product, prompt, fixture, index, route, or business-data edits are in scope. Do not call other Guide cases, change an outcome, write to cart/order/after-sales, or rebuild the hybrid/Graph index.

## Frozen execution pin

- Git HEAD: `9e9be1da8ef7dd7ba630a2025e63835612e4795e`; tree: `e28d6b06da5a174a6d739907dc4c5dfacaf7f6d8`.
- Isolated baseline API: `work/local-followup/04/kev-followup-20261009/serve_baseline.py`, bound to `127.0.0.1:8017`; fresh database/checkpoint under `data/runtime/kev-followup-20261009/baseline/`.
- Runtime model selected by the harness: `deepseek-flash`; actual Kev endpoint remains the existing `127.0.0.1:8009`, model `kev-latest`.
- `data/fixtures/policies.json` SHA-256: `7a370431a1a9c2df2b818218f3c54cb01946f93fa027aad44021dd1637f10502`.
- Hybrid index SHA-256: `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`.

No result is recorded in this plan; actual outcomes belong in the companion results report.
