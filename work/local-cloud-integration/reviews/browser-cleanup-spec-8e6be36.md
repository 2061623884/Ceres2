# Browser support cleanup: independent Spec delta review

Support repository: test-support/browser.
Baseline: `ce90cc8c19e2e0c616a6a738759e17bb97eba239`.
Target: `8e6be367986d35afe6211642cb81172347844d0f`.
Commands: git diff ce90cc8...8e6be36 and matching git log; outputs saved alongside. Read-only source review; no execution.

No actionable Spec finding. The cleanup change stays within the authorized bounded Tester fixture and supports the requirement to preserve truthful evidence rather than claim unperformed success.

stop_owned now checks the exact owned process group independently of leader liveness. It polls/reaps the known leader, sends TERM then KILL only to its start_new_session group when still present, and bounds each wait at five seconds. Both owned groups receive cleanup attempts. OS errors are retained; unverifiable group absence yields fixture_stopped=false and status 75. Support drift remains a separate failure. No broad PID search, external service action or product change is added.

The public launcher regression deliberately exits its group leader while a TERM-resistant descendant remains, then checks launcher status, lifecycle truthfulness and descendant absence. Failure repair targets only the test-recorded owned group. Required test source/build inputs and controlled nature are documented; observed GREEN results belong to the Tester, not this static review.

The prior cleanup Standards P2 is consistent with being closed by this source. Packaging must retain this exact target and update source/hash provenance. Controlled API/21-HTTP checks still do not establish native browser UI, live-provider, retrieval-quality or user acceptance; their blocked/unpassed status is unchanged.
