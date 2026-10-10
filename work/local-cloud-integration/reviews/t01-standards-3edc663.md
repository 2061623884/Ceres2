# T01 independent Standards review

## Pin and scope

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T01-policy`
- Baseline: `37c98400e7152b89e4a58f02fff3bceaa73b0eac`
- Candidate: `3edc663b4a0a67ccbc15d9a20c91f58d38d743a6` (resolved HEAD; clean on inspection).
- Full command: `git diff 37c98400e7152b89e4a58f02fff3bceaa73b0eac...3edc663b4a0a67ccbc15d9a20c91f58d38d743a6`
- Scoped command: `git diff 37c98400e7152b89e4a58f02fff3bceaa73b0eac...3edc663b4a0a67ccbc15d9a20c91f58d38d743a6 -- backend/app/knowledge backend/app/mercury/policy.py backend/app/services/knowledge_service.py backend/app/services/pi_product_runtime.py backend/knowledge-requirements.txt backend/knowledge-requirements.lock backend/tests runtime/pi/src/worker.ts docs/knowledge-policy-runtime.md evals/ceres2-optimization-retrieval-dev.json`
- Planning and static-corpus prerequisite excluded. Standards: AGENTS.md; docs/agents/{domain,issue-tracker}.md; GLOSSARY.md; ADR 0001/0002. Contract: T01 TASK and integration spec.

## Standards findings (under 400 words)

1. Hard violation, P2: `backend/app/knowledge/worker.py:21–22`, `serve`, catches `StaleIndexError` and returns only `KNOWLEDGE_STALE`, discarding its original message and stack. The generic-error branch preserves a traceback, but the stale branch does not. This loses the distinction between a caller/index race and a source/implementation mismatch. AGENTS “新增逻辑的依据” requires exception conversion to preserve the original cause. Retain the cause in host-side diagnostics without sending raw diagnostics into model context; add a worker regression.

2. Judgment, possible Duplicated Code / divergent contract, P2: `backend/app/knowledge/hybrid.py:22–29,43–50`, `validate_manifest` versus `build`, define separate partial representations of the manifest's implementation identity. `corpus.load_corpus` records implementation hashes; build adds pooling, query instruction, RRF, floors and calibration hash; validation checks none of those fields. Thus changed code/calibration/settings with unchanged revision literals can accept an old manifest and present it as current provenance. Share the actual current implementation identity between build and validation, and test stale recorded implementation/calibration before model recall. This is a design judgment supporting AGENTS' evidence-version provenance rule, not a blanket requirement to hash arbitrary code.

Static positives: shared source/worker validator runs before model loading; lock acquisition, pipe backpressure and complete-line reads check the same deadline; cancelled queue callers cannot close an owned worker; no production lexical fallback appears; raw retrieval remains host-side; controlled fixture documentation explicitly disclaims real BGE verification.

No tests, installs, builds or services were run by this reviewer. Candidate is not final: the owner reports a separately pending failure-recovery case (unknown snapshot failure followed by same-scope success). T07 Mercury forwarding and whole-branch integrated review are not covered here.

## Commit list

Command: `git log 37c98400e7152b89e4a58f02fff3bceaa73b0eac..3edc663b4a0a67ccbc15d9a20c91f58d38d743a6 --oneline`

```text
3edc663 feat: validate hybrid provenance and bound policy worker lifecycle
d7c8de4 wip: bind Pi policy evidence to actual retrieval snapshots
a2a88fb wip: validate policy source snapshots and bound retrieval queue
93ac1d4 data: stage frozen corpus prerequisite for policy integration
28957f9 docs: prioritize real policy snapshots over legacy constants
45f15c8 docs: assign retrieval deadline propagation ownership
f50f040 docs: freeze local-cloud integration spec and nine-ticket frontier
```

## Fixed-candidate delta, 2026-10-07 18:29 UTC

- Fixed pin: `6ba93b2b66a004fdfae1d7106d5f29a0512ddfd6`; clean worktree when inspected.
- Exact full delta: `git diff 3edc663b4a0a67ccbc15d9a20c91f58d38d743a6...6ba93b2b66a004fdfae1d7106d5f29a0512ddfd6`.
- T01 fix inspected independently of intervening T07 merge: `git show 6ba93b2b66a004fdfae1d7106d5f29a0512ddfd6`.
- Full baseline comparison remains `git diff 37c98400e7152b89e4a58f02fff3bceaa73b0eac...6ba93b2b66a004fdfae1d7106d5f29a0512ddfd6`; only the T01 paths listed above plus explicitly authorized `backend/app/api/guide.py` and its deadline tests are covered by this report.

Both findings are resolved on static inspection. `implementation_hashes` and `build_parameters` provide the actual recorded metadata to build and validation; changed fields cause stale rejection before model recall. The new tests mutate six previously unchecked fields. Worker stale errors now preserve original traceback in local stderr, with a regression checking the original error name/message. Diagnostics expose fixed schema field names rather than source text.

The unknown-source recovery change removes only the earlier null-identity failure for the same query/category after actual success or empty evidence. Different-scope failures remain. The parent-authorized Guide budget correction consistently changes both ingress deadlines, fallback constant, Node timer ceiling and user-visible deadline wording to fifteen seconds; tests retain direct-admission versus separate-preflight boundaries and replay behavior. No new hard or judgment findings in this delta.

No tests/builds/installations were executed by the reviewer. Full frozen-pin aggregate was still running when this addendum was issued. T07 Mercury forwarding and final whole-branch integration review remain separate.

Delta commit list (`git log 3edc663b4a0a67ccbc15d9a20c91f58d38d743a6..6ba93b2b66a004fdfae1d7106d5f29a0512ddfd6 --oneline`):

```text
6ba93b2 fix: bind actual index metadata and enforce fifteen-second Guide runs
2a411b3 Merge commit '15c0ad69a54312d82932875e6d4a3b1bcba404e4' into integration/t01-policy-hybrid
15c0ad6 docs: record T07 core evidence and correct Guide budget baseline
5f59257 merge: integrate verified T07 aftersales core, wiring pending
0ff65a0 docs: record fixed T07 core gates and deferred Mercury wiring
0a6e8fa fix: verify and decode bounded aftersales images before storage
f0f6ab4 test: require decodable photos with genuine bounded image fixtures
b12dfaa build: declare Pillow for verified aftersales image decoding
8666c70 fix: persist exact ticket application association atomically
6e87adf test: expose unassociated prior return leaking into new human ticket
fc6a3ad docs: record T07 source contracts test evidence and recovery handoff
79c5111 Merge commit '93ac1d4' into codex/merge-t07-aftersales
a44146c test: fix clarification fixture import and assert public ticket view
5361006 test: retain public model quantity clarification without submission
a0f9abb test: cover aftersales photo isolation quantities generations and rollback
fa5a729 feat: add reversible photo and nullable event-time schema upgrade
644e33c test: preserve synthetic legacy business rows during additive upgrade
0ef1fb9 feat: advance simulated orders with owner and version fences
cda3f1b test: specify sequential simulated order progress HTTP contract
6709dc9 feat: bind confirmed aftersales photos to exact ticket generation
fbd90a9 Merge commit '28957f9677d7f92879152f66a49e3ca3a39e43b8' into codex/merge-t07-aftersales
a3a4741 test: define T07 confirmed ticket evidence HTTP boundary
```
