# Standards re-review: ticket 02 freshness repair

Result: **No new Standards issue identified.** The prior review is retained; this report covers only the subsequent scoped freshness repair and its four public regression cases.

## Frozen scope

HEAD remains `79d34be1037a5fd910fd49bdb735afbea99b17b0`; baseline remains `4b576321317d6755cb2ef5845ceca6f89ba3e2b5`.

Comparison against the previous 246-file frozen manifest identifies exactly two changed source files:

- `backend/app/services/pi_product_runtime.py`, SHA-256 `88fa9110aec6439c02776e95a4507a690b6001cbb5a68939b3de3db002a511de`.
- `backend/tests/test_judge_policy_safety_public.py`, SHA-256 `6bae6e95d4878dffa9d7fd0435d9a28ff4dead7510e8c45ef015090168521a9b`.

Full tracked binary diff from baseline: `5bb7bda5a9e3f575a7481cb1683aa8656d464b7d29072588931d6cc642c7bc1f`. Product-source manifest: `e953dddb3c15c9fed79506225480356693dbc4302d5f706cda670dcac8fd1ac6`. Test-source manifest: `a68469360683e87984e97ce7f49f7dcfad1b138fe5592b07fbcaa5ee142777a3`.

## Review

- `pi_product_runtime.py:246–251,354–360` now checks the current request immediately after prefetch or an ordinary tool returns, before the next read/model continuation. The existing cancellation/deadline checks follow that potentially blocking freshness check. This directly implements REBUILD-DECISIONS §7's current-request and budget boundary rather than adding speculative validation (AGENTS:20–24).
- Freshness errors propagate through the existing failure path; they are not converted into policy misses, swallowed, or retried. No new provider logging, business write, model, budget, or authority is introduced.
- `test_judge_policy_safety_public.py:308–372` drives the public run and concurrent new-goal/abandon commands, then observes catalog reads, actual model requests, SSE failure, history, current task and cart. It does not replace the product freshness method or invent a private testing API. This follows REBUILD-DECISIONS §6's approved boundary fixtures.
- Reusing the existing guard at both handoff points is justified. No actionable smell is raised or generic abstraction demanded.

No tests, builds or installs were run by this reviewer. Tester results must correspond to this new candidate; the prior 40-case result does not certify the repair. Ticket-03 work and local frontend/browser/real-provider gates remain outside this re-review.
