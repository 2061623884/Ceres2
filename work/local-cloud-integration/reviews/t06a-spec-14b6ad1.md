# T06-A final test-only pin binding

Final HEAD: `14b6ad11c0c92d2b816f8b01c87b0a9c8a3253e6`; reviewed production pin: `26028b3786c136f5c56010059671cfe0998de841`. Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T06-graph`, clean. Commands: `git diff 26028b3786c136f5c56010059671cfe0998de841...14b6ad11c0c92d2b816f8b01c87b0a9c8a3253e6` and matching `git log --format=fuller`; outputs saved alongside.

## Result

No new Spec findings. The entire delta is the new `backend/tests/test_graph_real_bge.py`; production code, fixtures, configuration and existing tests are unchanged from 26028b3. Prior production-review conclusions therefore remain bound to unchanged source, without rerunning that review.

The opt-in helper requires a Tester-supplied fresh real index, uses the actual hybrid encoder path, checks fixed BGE revision, normalized 512-dimensional embeddings and all three namespaces. Its 18-case input explicitly identifies itself as public development relevance calibration, not independent acceptance. It verifies RRF arithmetic and records case results, evaluation hash and index manifest.

The stale-implementation check copies the fresh index and plants the actual pre-fix bge.py fingerprint, then proves rejection occurs before encoder invocation. I verified the recorded historical hash against `git show d37b5e8:backend/app/knowledge/bge.py | sha256sum`. The helper correctly disclaims having built a historical real index.

The deadline helper creates a fresh service/worker without warming that worker, gives each query its own original 15-second deadline, and asserts both queries succeed on the same PID. This is cold worker/model startup, not a claim of cold OS disk caches.

Read-only inspection of Tester records distinguishes the two configurations: default-thread run records 9.4279s cold and 0.0851s same-worker second query; the OMP_NUM_THREADS=2/MKL_NUM_THREADS=2 run records 6.3511s and 0.0130s. These are separate observations, not interchangeable performance claims. Each record has exit_code 0; source/build attribution remains Tester's responsibility.

## Limits

No tests, builds, installs, models or APIs executed by this reviewer. This is a test-only delta review/final-pin binding, not a new production acceptance run. Real BGE smoke/development evidence does not establish real-LLM GraphRAG quality, independent holdout quality, B-stage Pi integration, or UI/full-ticket acceptance.
