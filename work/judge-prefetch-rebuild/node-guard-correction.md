# Node verification guard: evidence correction

2026-10-07, Dedicated Tester. This is an explicit correction to earlier isolation wording; earlier records and failures have not been rewritten.

## Earlier enforcement gap

The original `run_check.py` set `NODE_OPTIONS=--require=.../node-local-only.cjs`. The production Pi runtime correctly uses an explicit child-environment allowlist, which does not include `NODE_OPTIONS`. Consequently, that particular Node guard was not inherited by the real Pi SDK worker. Earlier blanket claims that every Python/Node child had enforced loopback-only IO were too strong, including the statement in the 01 verification report.

The distinct facts remain: controlled runs had sanitized environments, synthetic credentials, loopback fixture endpoints and temporary business state; Python's audit guard was active; no real-provider credentials were used. The passing test counts and exact source hashes are unchanged. Those facts must not be presented as proof that the missing Node enforcement was active. The old 01 full suite has not been retroactively rerun or relabeled under the stronger harness.

## Repair without changing production permissions

The Tester-only harness now places a task-local `node` launcher first on PATH. It executes the existing Node binary with an explicit `--require` guard, so the product's unchanged PATH-preserving allowlist cannot drop it. The launcher and guard write only process IDs, launched script paths and fixed enforcement event names into the capture directory. No provider payload, hostname, credential or environment dump is recorded in this audit.

Each new capture records the launcher hash/runtime, invocation list, guard events, and before/after hashes of the harness, guard and Tester-only regression tests. Drift is explicitly listed. The product's explicit environment allowlist was not broadened.

The old Node loopback predicate also accepted hostnames beginning with `127.`. It now accepts a `127.` address only when Node's `net.isIP` confirms a real IPv4 literal. A sentinel transport proves lookalike rejection without DNS/network even during the RED run. Python already uses `ipaddress.ip_address(...).is_loopback`; a direct predicate probe confirmed its strict behavior without making a socket request, and its code did not change.

## Direct proof and retained probe failure

- `02-node-guard-probe`: a Node child launched without NODE_OPTIONS was denied a non-loopback socket and a dotenv read.
- `02-node-guard-regression`: 3 passed / 1 failed. The real-worker negative probe initially used port 9, which fetch rejected via its own bad-port rule before the socket guard ran. The assertion correctly refused to count that as guard enforcement. This failed probe remains recorded.
- `02-node-guard-regression-02`: **4 passed**. The corrected synthetic non-loopback destination used port 18080. Public Guide SSE failed safely, and PID-correlated records prove that the actual `runtime/pi/dist/worker.js` process loaded the guard and was blocked by it. The same capture passed the missing-NODE_OPTIONS negative probe and normal actual-SDK policy-prefetch/product-query loopback journeys.
- `02-node-lookalike-guard-red`: **1 failed**, safely reproducing the old `127.` hostname-prefix predicate through a no-network sentinel.
- `02-policy-evidence-green-05`: **17 passed**, including the stricter guard regressions, all then-current prefetch behaviors and complete guide semantics. This is a feature checkpoint, not final four-ticket acceptance.
- `02-node-guard-final-proof`: **4 passed**, plus the direct Python strict-loopback predicate check. This is the final narrow guard proof: real-worker blocking, lookalike rejection without network, no-NODE_OPTIONS protection and intended SDK loopback journeys all pass. Product and harness before/after hashes are identical, and the launcher before/after hash is identical.
- From `02-policy-evidence-red-04` onward, policy captures use the repaired harness. Existing current prefetch cases are rerun under it, and all final whole-phase gates must use it.

The two harness regression tests live outside product tests at `verification_tests/test_node_worker_guard.py`. Future source changes require their normal targeted/full candidate verification; this guard proof is not a substitute for product or frontend acceptance.
