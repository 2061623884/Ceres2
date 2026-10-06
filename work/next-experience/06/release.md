# TASK06 controlled candidate

Base integration: `dddac9c5d3ef3ab2c61f2957aec82ecc4fab10cd`, after05 controlled release,04/09 integration and08 activity guard. Source owners coordinated:05 transferred shared Pi/Prompt ownership;03 provided the scoped App patch; main/merges remain integrator-owned. No push or external publication.

## Delivered

- Structured category/filter/selection results and cart/application receipts render before an independent expression request. Results are already committed; expression cannot delay acknowledgment, roll them back, or re-enter business execution.
- Main-model Pi expression process is tool-free and never calls Kev. Each complete JSONL unit references host-rendered facts from the exact immutable result. Brief non-business connective text passes the existing byte-identical general-claim check. No raw token or arbitrary referenced factual prose bypasses that boundary.
- Up to two validated units can reach the real HTTP/SSE client while generation remains in progress. Generator and per-unit validator calls/usage are measured separately within the expression budget; no latency/cost saving is claimed.
- Existing receipt/event/message infrastructure handles idempotency, explicit stop, transport reconnection and history. Exact digest/kind/source provenance prevents ordinary-turn ID collision. Owner/task/version/opening/new-turn and Momo selected-case/history fences prevent stale publication.
- Cards/actions remain usable while introduction loading is separate. Failure/timeout/stop retains business success and ends introduction loading; UI does not ask users to repeat a committed purchase/application.
- Original04 prompt clauses,05 context selection/general-text guard,08 activity callbacks and09 receipt/recovery behavior remain intact. Pure expression messages do not shadow semantic dialogue context.

## Trigger matrix

Introductions start for category/filter/product-choice command results, eligible newly created text results/plans or empty search, full/per-row cart confirmation and aftersales application confirmation. They use the original command/confirmation/receipt identity. A retained question or plan during unrelated chat is not a new trigger.

Legacy standalone quantity/revision/quote/partial controls keep their immediate deterministic feedback and cancel stale introduction. They do not request another model call on every adjustment. This is the deliberate bounded06 scope.07 is language refinement, not a deferred implementation bucket. See [full contract](contract.md).

## Sole-Tester evidence

All paths below are under integration `work/next-experience/10/`; runs/checks contain `record.json` and `output.log`.

- `runs/next06-red-01`: actual loopback HTTP result exists; missing expression endpoint returns404 instead of202.
- `runs/next06-green-01`, `runs/next06-green-02`: result first, validated host-grounded unit before provider generation end, no tools, one generator plus one checker for the tested unit, no generation or cart write on replay.
- `runs/next06-receipt-red`: purchase source initially rejected422. GREEN pair then rejects forged payment/delivery wording without changing the committed cart receipt.
- `runs/next06-public-matrix`:16/16 controlled public cases passed, including actual socket closure before provider completion and recovery after the last sequence, malformed/unsupported references, fabricated price/execution claims, uncertain validation, explicit stop/new task/new turn/role close, actual30-second timeout, text/empty-query and refund/owner boundaries.
- `runs/next06-matrix-context`:22/22 selected stream/context cases passed, excluding the separately passed timeout once.
- `checks/next06-receipt-dom-red`, `checks/next06-app-dom-red`: actual components reproduce missing post-render expression admission.
- `checks/next06-app-green`, `checks/next06-own-ui-green`: App and AfterSalesPanel result-first/incremental/failure/stop/interaction/navigation/restoration isolation and sequence-deduplication scenarios pass.
- `runs/next06-review-red`: all3 targeted reviewer findings reproduced, including deterministic request-ID collision and actual30.5-second SQL stalls at metric commit and final unit lock.
- `runs/next06-review-green`:4/4 pass after the minimal fixes, including a pre-authorized Momo query completed before final unit publication without changing opening metadata. No late unit, altered business receipt or repeated application.
- `checks/next06-review-fix-runtime`: runtime typecheck/build pass.
- `checks/next06-all-ui`:31/33 behavior scenarios pass initially;2 inherited fixed-file compilers omit the newly required helper and fail setup. `checks/next06-legacy-ui-dependencies` recompiles complete dependencies temporarily and both unchanged harnesses pass. No source compiler or assertion was weakened. Frontend build/strict checks pass. Together with the2 new06 scenarios:35 DOM/client scenarios pass.
- `runs/next06-regression-rest`:103/103 pass in150.14 seconds; exactly the4 review cases are deselected to avoid duplicate real30-second stalls. Across this initial broad snapshot,107 cases passed and its20 new06 cases were covered. The subsequent usage correction is verified on the current source below.

- `runs/next06-usage-red`:3/3 public timing/metric cases reproduce omitted provider usage being reported as SDK zero,17 prompt-total tokens being reported as12 cache-subtracted input, and omitted cache fields being reported as zero.
- `runs/next06-usage-green`:3/3 pass after a minimal read-only `onProviderStreamEvent` observer. Omitted fields are null, provider17/9 and cache3/2 are preserved, and explicit0 remains0. Both generator and validator preserve provenance while the actual client still receives the first approved unit before generation completes.
- `runs/next06-usage-review`:4/4 reviewer lifecycle cases pass on the usage-fixed source in66.93 seconds.
- `runs/next06-usage-regression`:102/102 remaining selected cases pass in149.43 seconds; exactly7 cases (the3 usage/timing and4 reviewer cases above) are deselected because already covered. These disjoint current-source runs total109 cases, including all22 new06 cases. Runtime build/typecheck pass. UI source is unchanged from the35 passing DOM/client checks.

Provider token fields are observed before SDK normalization. `input_token_scope=prompt_total` includes cached input; cache counters are separate detail, not extra tokens to add again. `usage_source=provider` indicates an observed usage object, while every missing numeric field remains null. No missing usage is converted to zero, and no token/cost saving is claimed.

The named final checks recorded unchanged source during execution. Final commit/source equality is a separate integrator/Tester check; completion of this implementation is not formal acceptance.

## Limitations and remaining acceptance

Factual wording is deliberately host-rendered; the model supplies validated connective expression. Tests establish controlled concurrency and grounding boundaries, not real-provider language quality or guaranteed first-fragment speed. The same provider may finish generation before its checker on some samples; those timings must be measured honestly in real-provider validation.

30-second Keke/15-second Momo expression guards are checked after waits and before publication. Arbitrary blocked SQLite I/O may delay terminal persistence, so this is not a universal end-to-end response-time SLA. Existing business receipts still remain authoritative.

Live-provider sampling, actual browser/page verification, natural-language review and user acceptance are unverified. Provider choice is unchanged and out of scope. Parent owns the formal task state and any controlled release to07.
