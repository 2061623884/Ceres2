# T06-A final corrective delta: Standards

Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T06-graph`.

Exact diff: `git diff 2ad494c424ec5f7fda348176063e24376430cd1a...26028b3786c136f5c56010059671cfe0998de841`.

Commit list: `git log 2ad494c424ec5f7fda348176063e24376430cd1a..26028b3786c136f5c56010059671cfe0998de841 --format='%H %s'`. Diff and list are saved alongside this report. Prior fixed reviews cover 333e0bd → c96e099 → 826d71e → d37b5e8 → 2ad494c; applicable standards and smell baseline remain unchanged.

## Findings

The remaining CLI causal-diagnostic finding is resolved on static inspection. `supervise_graph_job` records the bounded private exception category before converting timeout/interruption to the public result. It does not echo command arguments, stdin, query or exception bodies. Existing kill/reap and manifest invalidation behavior remains unchanged.

New regression source covers both actual timed-out subprocess cleanup and simulated KeyboardInterrupt, checks the private cause category and verifies a private query marker is absent from both JSON output and stderr. This is source inspection only, not a reviewer-executed test.

The separately reviewed six-file BGE allow_patterns delta at 2ad494c also remains clear: it preserves pinned revision and local-only/no-token/no-remote-code constraints while intentionally changing implementation fingerprints. It does not establish that real BGE encoding or new index construction has succeeded.

Outcome at 26028b3786c136f5c56010059671cfe0998de841: zero open hard Standards violations and zero open judgment findings for the reviewed T06-A backend scope. The two original violations and subsequent CLI diagnostic issue are all closed.

No tests, builds, installations, services, APIs or product edits were performed. Tester must independently bind current controlled and real-BGE evidence to this final source. T06-B Pi tools/refs, full ticket acceptance and final integrated review remain outside this backend-only clearance.
