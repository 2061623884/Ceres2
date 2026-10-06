# TASK10 final controlled verification plan

Status: preparation only. The final suite is not run until TASK07 is released. Earlier RED/GREEN, full-baseline failures, and their scoped repairs remain historical evidence, not a substitute for the final candidate.

## Freeze and execution

1. The integrator creates a detached snapshot of the exact released candidate. Record commit, clean/dirty source inventory, current fixtures, all Prompt files, lockfiles, installed versions, and generated runtime JS. Source stays fixed through execution; each process uses its own temporary DB/checkpoint state. Do not import archive/reference runtimes or read credentials/holdout.
2. Tester uses the fresh project dependencies already installed from committed locks. Build/typecheck Pi; build/strict-typecheck frontend. No lint command is declared in current project manifests, so lint must be labeled not configured, not passed.
3. Run the entire backend public/controlled suite with run_controlled.py against that snapshot. It installs a clean synthetic environment before imports, disables dotenv, denies dotenv reads, restricts Python network IO to loopback, and captures before/after source plus every generated Pi JS artifact. Preserve complete output, timing, exit and failures. Do not skip failed requirements.
4. Execute the actual OS-process restart probe from inside that same snapshot, with the same installed Python and freshly built runtime. It creates/kills only its own process group and temporary data. Check source and harness hashes. Capture scoped result separately from the full backend suite.
5. Execute run_all_dom.py against freshly compiled actual frontend, then both TASK06 streaming UI harnesses and any TASK07 harness supplied. Include all inherited race, contact, human, order, comparison, plan and reconnect variants. The compiler must materialize all frontend dependencies before older fixed-file TSX compilers; tests and assertions remain unchanged. Keep the observed inherited ShelfScreen/ShoppingApp render warning distinct from assertion results.
6. Independently review Standards and Spec against the exact same frozen source. Any fix returns to its owner, receives focused RED/GREEN as appropriate, and requires a new freeze plus affected final rechecks. Do not mix source revisions into one final pass.

## Requirements and exact pointers

coverage-manifest.json maps 16 requirement families to existing test files and exact function selectors read from their AST. It includes:

- Snack/drink supply-driven choices, typed identity, constraints, quantities, stale supply, concurrent text/clicks, and explicit idempotent confirmation
- Policy sources/conditions, role/capability routing, opening ACK/quota, stale handoff/order races and explicit compound return
- Result-before-expression, real loopback incremental SSE/socket reconnect, stale/stop/deadline/SQL wait fences, invalid claims, canonical receipt persistence, and numeric usage provenance
- Activity finished-product scope and explicit exit
- New order/aftersales/shopping return; human acquisition versus application transaction races
- Inherited dishes/people/packages/budget, alternatives/partial procurement, and fresh-fact historical repurchase
- Explicit memory CRUD, cross-role fences, deletion/correction races and extraction leases
- Dream at 9 versus 10 effective records, 24-hour cooldown, 30-day expiry, one active job, lease reclaim and effective-fact revalidation
- Schema/seed repeatability, shutdown/recovery and actual installed SDK/protocol boundaries

The Dream tests actually trigger controlled Dream callbacks with explicit clock advances. They are not evidence of a live-provider Dream or observed 24-hour wall-clock lifecycle. Existing app-recreation tests and the new real-process probe have separately labeled scope.

## Required final report layers

- Controlled backend/API/SSE: final exact-source results and command records
- Controlled DOM/client: final actual-component interactions; no browser/layout claim
- Installed SDK + loopback provider/transport: report scripted/fixture provenance, calls, usage nulls and timings honestly
- Real Kev/main/extraction/Dream models: unrun unless separately authorized and executed; no credentials inspected
- Real browser and user experience: unrun under current browser restriction; user handoff remains required
- Natural-language quality/performance: synthetic prompt delivery and deterministic output do not prove naturalness, token savings or latency improvement
- Private unseen holdout: unread/unrun; never expose private cases to implementers; retested failures become regression, not fresh independent evaluation
- Frozen V3 comparison: not established by inherited tests or historical reports
- Human acceptance: only the user can provide it

A controlled technical pass does not mark TASK10 accepted while these external/independent gates remain open.
