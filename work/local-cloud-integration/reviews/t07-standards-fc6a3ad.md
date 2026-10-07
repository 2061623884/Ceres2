# T07 independent Standards review

## Pin and scope

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_t07_aftersales`
- Fixed baseline (resolved): `37c98400e7152b89e4a58f02fff3bceaa73b0eac`
- Reviewed frozen head (confirmed by owner): `fc6a3ada162dbeef393972a6ba68f635355fa80f`
- Full diff: `git diff 37c98400e7152b89e4a58f02fff3bceaa73b0eac...fc6a3ada162dbeef393972a6ba68f635355fa80f`
- T07 code/test scope: `git diff 37c98400e7152b89e4a58f02fff3bceaa73b0eac...fc6a3ada162dbeef393972a6ba68f635355fa80f -- backend/app backend/tests`
- Planning and static-fixture changes excluded. Recovery/handoff read for context. No product edits, tests, installations, services, or real API calls performed.
- Standards sources: `AGENTS.md`, `docs/agents/{domain,issue-tracker}.md`, `GLOSSARY.md`, `docs/adr/0001-canonical-shopping-authority.md`, `docs/adr/0002-python-business-pi-langgraph-runtime.md`. Contract context: T07 TASK and integration spec.

## Standards findings (under 400 words)

Hard documented violations: none established in this scoped review.

Judgment finding, possible Primitive Obsession (P2): `backend/app/human/service.py:47–63`, `ticket_evidence`, uses `AfterSalesProposal.responsibility_generation == ticket.generation - 1` as the identity of a ticket's applications. Responsibility generation is a concurrency fence, not a specific application-to-ticket association. `AfterSalesService.submit` leaves the generation unchanged for ordinary returns, so a return on line A followed by a quality/fulfillment application on line B can share the same generation. The latter ticket then lists both confirmed applications. A manual handoff after an ordinary return similarly infers membership. Existing tests cover separate generations and unrelated photos, but not this same-generation sequence.

Persist the actual application-to-ticket association in the existing confirmation transaction, and make both ticket views and photo reads follow that association. Add a public regression with a prior return and a subsequent problem application on different lines before the first handoff. This is a design judgment with a concrete scope consequence, not a newly invented hard style rule. Applicable documented principles: AGENTS “Python 是唯一业务事实和写入权威”; ADR 0001's single canonical business-fact/transaction boundary. Neither document endorses replacing this distinct association with generation arithmetic.

Owner/selection checks, receipt replay, atomic ticket creation, sequential simulated-order CAS, and additive nullable legacy event times are present on static inspection. That statement is not executed verification. No speculative abstractions or unsupported defensive branches otherwise warranted a finding; the missing-photo-list fallback is grounded in the existing refund/return receipt contract.

This is only a T07 slice review. T01 Mercury deadline/category hookup remains pending, and the final integrated branch must receive a fresh whole-branch review and exact-pin Tester verification.

## Commit list

Command: `git log 37c98400e7152b89e4a58f02fff3bceaa73b0eac..fc6a3ada162dbeef393972a6ba68f635355fa80f --oneline`

```text
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
93ac1d4 data: stage frozen corpus prerequisite for policy integration
fbd90a9 Merge commit '28957f9677d7f92879152f66a49e3ca3a39e43b8' into codex/merge-t07-aftersales
a3a4741 test: define T07 confirmed ticket evidence HTTP boundary
28957f9 docs: prioritize real policy snapshots over legacy constants
45f15c8 docs: assign retrieval deadline propagation ownership
f50f040 docs: freeze local-cloud integration spec and nine-ticket frontier
```

## Association-fix addendum, 2026-10-07 18:08 UTC

- Fixed pin: `8666c70db909d77ea5d99db856bddc1c2555ff9d`.
- Exact delta: `git diff fc6a3ada162dbeef393972a6ba68f635355fa80f...8666c70db909d77ea5d99db856bddc1c2555ff9d -- backend/app backend/tests`.
- Commits: `6e87adf test: expose unassociated prior return leaking into new human ticket`; `8666c70 fix: persist exact ticket application association atomically`.
- The judgment finding above is resolved on static inspection: `AfterSalesApplication.human_ticket_id` records the actual ticket returned by `create_ticket` inside the existing transaction; `ticket_evidence` now requires that exact link. Legacy rows retain NULL instead of an inferred association. Added public regression covers earlier ordinary return followed by quality and manual handoffs, preserving independent owner receipt history. Added migration regression checks legacy NULL, idempotent marker, and actual foreign-key constraint.
- No additional Standards findings in this delta. Tests were not executed by this reviewer. The implementer reports a dedicated Tester 23-pass result; this report does not independently certify that run. Image-decoding work is still pending and excluded from this fixed-pin addendum. Final whole-branch review remains pending.

## Final T07 slice addendum, 2026-10-07 18:10 UTC

- Final scoped pin: `0a6e8fa83d14165844e81f3d8e8d1a016c35ece2`; worktree clean when inspected.
- Overall exact command: `git diff 37c98400e7152b89e4a58f02fff3bceaa73b0eac...0a6e8fa83d14165844e81f3d8e8d1a016c35ece2` (planning/static corpus excluded from review as above).
- Decoder delta: `git diff 8666c70db909d77ea5d99db856bddc1c2555ff9d...0a6e8fa83d14165844e81f3d8e8d1a016c35ece2`.
- Additional commits beyond the preceding addendum: `b12dfaa build: declare Pillow for verified aftersales image decoding`; `f0f6ab4 test: require decodable photos with genuine bounded image fixtures`; `0a6e8fa fix: verify and decode bounded aftersales images before storage`.
- Combined full commit list is the original list plus the two association-fix commits and the three decoder commits recorded here; reproduce with `git log 37c98400e7152b89e4a58f02fff3bceaa73b0eac..0a6e8fa83d14165844e81f3d8e8d1a016c35ece2 --oneline`.

Standards outcome: zero open hard violations or judgment findings. The original generation-as-association finding is resolved. Image validation now compares actual JPEG/PNG/WebP format with declared MIME, verifies structure and decodes pixels before persistence, retaining the 4 MiB byte bound and Pillow's decompression-bomb checks. Error conversion preserves original causes and directly supports the legal-image input contract; it is not speculative defensive logic under AGENTS. Pillow is identically pinned in dependency declaration and lockfile. Positive synthetic transport fixtures and truncated/header-only negative cases are documented; no personal image state is imported.

This remains static read-only review, with no tests or tools executed by the reviewer beyond repository/file inspection. The implementer reports a dedicated Tester 32-pass result for public/migration coverage, which is not independently certified here. T01 Mercury deadline/category forwarding, final integrated whole-branch Standards/Spec review, and exact-pin aggregate verification remain outside this completed T07 slice review.
