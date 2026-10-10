# Spec re-review: ticket 02 freshness repair

Original P2 closed in the reviewed source. No new scoped finding.

Spec `docs/plans/ceres2-judge-prefetch-spec.md:63` requires “每次进入检索／Pi 及发布结果前检查取消、当前请求与相关剩余时间”. The two minimal additions in `backend/app/services/pi_product_runtime.py` now enforce that requirement after blocking work:

- Lines 246–251: freshness is checked immediately after prefetch returns, before subsequent catalog access; stop/deadline checks follow the potentially blocking freshness read.
- Lines 354–360: freshness is checked after an ordinary tool returns and before `tool_result` can resume Node/Pi; stop/deadline checks again follow it.

These checks use the existing trusted session/task anchor and existing stale-state termination. Legitimate `guide_request` transitions still update their owned anchor before returning. The repair adds no budget, retry, authority, public protocol, or cache behavior.

The new four-case public fixture (`test_judge_policy_safety_public.py`, `test_request_changed_during_lookup_cannot_read_categories_or_resume_pi`) covers prefetch/ordinary lookup × new-goal/abandon, observes actual provider calls and catalog SQL, and verifies public history, task, and cart readback. I did not run it. Tester RED reproduction was reported; the 44-case GREEN and full backend gate were still independent pending work at this review.

Only the runtime and safety-test file changed from the original 246-file frozen source set. Removing exactly the two added freshness calls restores the previously reviewed runtime hash. All other product/test source hashes match. Original `spec-02.md` remains intact; ticket 03 and frontend/browser acceptance were not re-reviewed.

Candidate: HEAD `79d34be1037a5fd910fd49bdb735afbea99b17b0` plus working tree. Runtime SHA-256 `88fa9110aec6439c02776e95a4507a690b6001cbb5a68939b3de3db002a511de`. Full base-to-working tracked diff SHA-256 `5bb7bda5a9e3f575a7481cb1683aa8656d464b7d29072588931d6cc642c7bc1f`. Adjacent `spec-02-rereview-source-pin.json` records all changed-file hashes and the complete 246-file source manifest. Hashes were rechecked unchanged at completion. No source edits, tests, builds, or model calls performed.
