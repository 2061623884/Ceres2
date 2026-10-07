# T06-A final test-only binding: Standards

Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T06-graph`.

Exact delta: `git diff 26028b3786c136f5c56010059671cfe0998de841...14b6ad11c0c92d2b816f8b01c87b0a9c8a3253e6`.

Commit command: `git log 26028b3786c136f5c56010059671cfe0998de841..14b6ad11c0c92d2b816f8b01c87b0a9c8a3253e6 --format='%H %s'`. Two commits, b1063f5 and 14b6ad1; full SHAs/diff saved alongside this report.

## Result

Zero new hard or judgment findings. The entire delta adds only `backend/tests/test_graph_real_bge.py`; production code, fixtures, dependencies, runtime and deployment configuration are identical to reviewed 26028b3. No repeat production review or execution was performed.

The helper explicitly opts into a Tester-supplied fresh index. Smoke/dev reads use the index read-only; stale-fingerprint testing modifies only a copied temporary index and clearly identifies the historical fingerprint as planted. Calls use local hybrid/BGE only, with no LLM/provider or graph-build invocation. The persistent-worker test inherits the guarded test environment, uses a fresh process, and assigns each request its own unchanged 15-second budget. It introduces no production warmup or thread override.

Read and verified separate Tester records under `test-evidence/runs/`:
- `real-bge-default-thread-cold-warm`: exact HEAD 14b6ad1, exit 0, no source/harness drift; default-thread cold 9.427866 seconds, same-worker second request 0.085104 seconds, same PID 11.
- `real-bge-smoke-dev-cold-warm`: exact HEAD 14b6ad1, exit 0, no source/harness drift; explicitly test-only OMP_NUM_THREADS=2/MKL_NUM_THREADS=2, cold 6.351068 seconds and same-worker second request 0.012954 seconds, same PID 27.

Both timing reports record no pre-warm and a 15-second request budget. The separate public development report contains 18 cases and no failed cases, explicitly labeled development calibration rather than independent holdout acceptance. No holdout source is read by the helper.

All three report SHA256 values match `test-evidence/bge-results/manifest.json`. These are reviewed Tester artifacts, not reviewer-run tests, production latency guarantees, or real-LLM evidence.

Final T06-A Standards clearance binds to `14b6ad11c0c92d2b816f8b01c87b0a9c8a3253e6`. T06-B, full integration and user acceptance remain separate.
