# Browser support cleanup: Standards delta closure

Fixed external support source: ce90cc8c19e2e0c616a6a738759e17bb97eba239...8e6be367986d35afe6211642cb81172347844d0f. Worktree: test-support/browser, frozen at inspection. Exact git diff and two-commit list retained alongside this report. Read root integration standards and prior browser-support/full-branch findings; no product changes are covered by this helper delta.

## Findings (under 400 words)

The prior cleanup P2 is closed on source inspection at 8e6be36. stop_owned now probes the exact PGID created by start_new_session independently of leader exit. It reaps only its known Popen leader, gives TERM and KILL bounded five-second windows, and does not search the process table or select any unrelated PID/group. ProcessLookupError means absence; other OS failures are retained explicitly. Both known groups are attempted even if one fails.

The final lifecycle flag is the conjunction of the two observed cleanup results. Unproven absence is reported as fixture_stopped=false and exit 75, rather than unconditional success. Source drift remains separately reported with exit 70 when cleanup succeeds. README states the two-group, bounded escalation behavior. These cleanup windows can extend beyond the interaction lifetime by at most approximately twenty seconds total, which is explicit bounded cleanup rather than a new interaction budget.

The public CLI regression starts a same-group descendant that ignores TERM, waits until its handler/identity file are ready, and exits the leader normally. It checks the actual child PID is gone after the launcher returns. RED repair targets only the exact recorded group while confirming that child's current PGID. It does not use scans, subreaper changes or OS settings.

Hard documented violations: none. New judgment/smell findings: none. Root/Tester report targeted RED at 674a079 and GREEN at 8e6be36 (1 passed, 8.90 seconds); this reviewer did not execute or independently rerun tests. Wider helper/API lifecycle validation is still pending and must be bound to this exact pin. Canonical packaged helper at 81b02f9 remains the old source until Merger selectively includes and binds this fixed delta. This closure does not clear the separate product tail-alias P2, nor claim browser UI acceptance.

## Subsequent verification notice

At 21:29 UTC Merger relayed Tester terminal GREEN: targeted cleanup 1, portable helper 3, real API smoke and 21-request HTTP contract on frozen product 81b02f9, with exact owned PGIDs stopped. This supersedes the wider-validation pending sentence above as a received terminal report; the reviewer did not execute tests. Canonical inclusion/equivalence and product-fix verification remain separate.
