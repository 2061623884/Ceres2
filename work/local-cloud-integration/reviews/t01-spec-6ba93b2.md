# T01 independent Spec correction review

Baseline: 37c98400e7152b89e4a58f02fff3bceaa73b0eac. Frozen HEAD: 6ba93b2b66a004fdfae1d7106d5f29a0512ddfd6. Worktree: /workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T01-policy; HEAD verified and clean at inspection. Full baseline...HEAD diff and commit list are saved alongside this report. Reviewed correction delta from 3edc663, primarily commit 6ba93b2; intervening T07 integration is not represented as new T01 review coverage.

## Result

Both prior P2 findings are resolved by static inspection. No new blocking Spec finding identified in this correction delta.

1. Actual provenance: corpus.implementation_hashes and hybrid.build_parameters provide shared actual source/calibration hashes and execution parameters. Both manifest creation and validate_manifest use these values, covering implementation, pooling, query instruction, RRF, relevance floors, named versions, model revision/dimensions and fixture hashes. The same validator protects source_snapshot and worker search. Regression source mutates the six formerly unchecked metadata fields while preserving revision literals. Stale-worker diagnostics retain mismatch context without sending source contents to the model.

2. Unknown-source recovery: PiProductRuntime._policy_unavailable_message removes only an earlier all-null-source attempt for the exact query/category when a subsequent success/empty arrives. Errors remain uncached, and unrelated query/category failures remain in projection. Runtime request isolation still comes from the request-owned policy_attempts collection and policy_scope. Public regression source covers success recovery, empty recovery and a distinct-query failure retained.

3. Approved 15-second Guide boundary: both /runs and /turns/stream now capture deadline = monotonic()+15 before owner lookup and synchronous route authorization, then pass that same absolute deadline through launch_run, Pi processing, policy retrieval and Node timeout. Replay launches only when admit reports is_new; reconnect reads events without restarting work. Direct role judgment therefore consumes the admitted request's budget. A separate navigation preflight remains a distinct HTTP operation; this does not establish a combined multi-HTTP 15-second limit. Node's timer cap and timeout text now match 15 seconds. Five tool rounds, model selection and output/token configuration are unchanged in this delta.

## Remaining phase boundary

No tests, installs or runtime commands were executed by this reviewer. Pending Tester aggregate results are not inherited; actual BGE quality is unverified. T07 Mercury deadline/category forwarding and final entire-integration Spec review remain outstanding. Existing T07 fix review remains separate.
