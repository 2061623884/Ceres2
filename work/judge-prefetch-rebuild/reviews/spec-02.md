# Spec review: ticket 02

One P2 finding; no scope-creep finding.

## P2: Recheck freshness before resuming Pi after a blocking tool

Spec `docs/plans/ceres2-judge-prefetch-spec.md:63` requires “每次进入检索／Pi 及发布结果前检查取消、当前请求与相关剩余时间”. At `backend/app/services/pi_product_runtime.py:353–358`, a tool returns and only receipt cancellation/deadline are checked before its result is sent to Node, allowing the next Pi model call. The preceding freshness check was before the potentially blocking lookup.

A concurrent public new-goal/abandon transition changes the session anchor without stopping this receipt (`guide_lifecycle_service.py:72–93`); `should_stop` only checks cancellation/receipt status (`pi_product_turn_service.py:69–75`). If that happens during the ordinary policy lookup, the stale result can reach Pi before the next loop detects the change. Final publication remains fenced; this finding concerns unauthorized-by-current-state model continuation, not duplicate writes. Recheck `assert_current` after the tool and before sending its result, then recheck stop/deadline after that potentially blocking read. Add a public lifecycle/lookup-boundary regression. This is source analysis, not an executed reproduction.

## Reviewed coverage and limits

Full-original-query/category-None prefetch, genuine scoped Python refs, lower-priority same-Pi evidence, all judge fallbacks, empty/error/partial distinctions, exact-scope failure recovery, mixed waiting/general/dish/history/memory projection and provenance, business authorization, deterministic confirmations and transactional late-publication rollback otherwise match ticket 02. Dedicated Tester evidence records 40 policy tests passed; I ran no tests/builds/models.

Ticket-03 deduplication/multi-reference requirements remain deferred. User-local frontend/browser acceptance remains open and is not a missing cloud implementation.

## Candidate pin

Base `4b576321317d6755cb2ef5845ceca6f89ba3e2b5`; actual HEAD `79d34be1037a5fd910fd49bdb735afbea99b17b0` plus working changes and untracked safety tests. Full tracked diff SHA-256 `04db3628b6ab26b0d4bcf43aa51fe5d584510a444e1b99b0ff234e8cae7360e6` is unchanged from review start. All 246 frozen source hashes match Tester manifest `59d88c396ac92c38f002fad67acf43ff39c8b336344ac12586cc2fd9623b974e`. Complete changed-file hashes and product/test patch hash are in adjacent `spec-02-source-pin.json`.
