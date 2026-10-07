# Hybrid policy retrieval runtime

T01 selectively carries the hybrid implementation and development calibration from
incoming `6734c7fe79e670df2dae12b065dcc49c0b10a307`. This is source provenance,
not evidence that its historical model/evaluation results pass this integration.

## Runtime contract

- Python remains business authority. Retrieval does not authorize orders,
  eligibility, current Offer prices, stock or writes.
- `policy.source_snapshot()` validates all five static corpus files against the
  persisted index manifest, actual corpus/encoder/ranking source hashes, calibration
  digest, and all recorded model/pooling/tokenizer/relevance/RRF build parameters.
  The worker uses the same validator before loading model dependencies.
- Source identity contains the fixture name/version and policies.json SHA256.
  Index identity is SHA256 of the canonical persisted manifest. The worker checks
  the expected identity inside its SQLite read transaction. Policy acquisition
  rechecks the current source after the response before creating evidence.
- Pi reuse requires exact request scope, query text, category and all source/index
  identity fields. Successful/empty evidence can be reused; failures have no ref.
  Multiple independently acquired policy refs retain their individual scopes.
- Complete policy facts and identities reach Pi; duplicate raw retrieval lanes,
  candidates and manifest remain in host-owned evidence, avoiding repeated
  context inflation. Neither model context limits nor output caps were raised.
- Guide admission uses a 15-second budget (correcting the cloud baseline 30).
  A direct Guide request includes synchronous role judgment in that budget. An
  independent navigation preflight is a separate HTTP boundary; user confirmation
  and waiting between requests are not counted in the subsequently admitted run.
  Replays/reconnections never create a fresh deadline for the same run. This is
  not a promise that the entire multi-request interaction finishes in 15 seconds.
- Run callers pass the original absolute monotonic deadline and cancellation
  callback. Queue waiting, startup, nonblocking pipe writes and partial-line
  reads consume that budget. Only the lock-owning query can retire its worker.
  Cancelled queue waiters cannot interrupt another request. Worker reaping cannot
  prolong an expired caller. Independent API callers retain their explicit budget.
- Missing index/model/dependencies and invalid protocol results are unavailable;
  stale provenance is stale; neither is represented as an empty match. There is
  no production keyword-only fallback or automatic model download.

## Reproducible environment and index

`backend/knowledge-requirements.lock` is the exact incoming frozen stack. Its
GraphRAG dependencies are retained for the authorized T06 environment but are not
imported, enabled or accepted by T01. Direct consumers are distinguished in
`backend/knowledge-requirements.txt`. Business Python uses its separate lock.
Torch CPU wheels use the official `https://download.pytorch.org/whl/cpu` index.

The service expects `.venv-graphrag/bin/python`. The pinned BGE model revision in
`app/knowledge/bge.py` must already exist in `.cache/huggingface`; loading is
local-only. The Tester owns dependency installation, builds and verification.
After provisioning the approved local model, the supported build entry point is
`python -m app.knowledge.cli build-hybrid`, run from `backend/` in the isolated
knowledge environment. `--fixtures` and `--index` explicitly select matching
sources and destination; default paths are `data/fixtures` and
`data/indexes/hybrid.sqlite3`. Index build writes a temporary SQLite database and
atomically replaces the destination. `hybrid` and `serve` use the same source
validation. The development calibration file is
`evals/ceres2-optimization-retrieval-dev.json`; holdout data is not consumed.

## Verification boundaries

Public policy HTTP tests control model recall at the worker boundary while
retaining actual snapshot construction, Pi SDK execution and host ref validation.
They do not demonstrate BGE accuracy. Separate tests launch the actual JSONL
worker for stale index/current fixture rejection and missing dependencies, and
controlled subprocesses exercise contention, partial lines, cancellation and
pipe backpressure. Actual local BGE model loading/index build/retrieval quality
remain unverified until the approved local model and environment are available.
