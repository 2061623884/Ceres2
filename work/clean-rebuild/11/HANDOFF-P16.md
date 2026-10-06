# TASK11 → TASK16 integration handoff

Root released TASK11 controlled technical scope at 2026-10-05 20:26 UTC. Shared guide/runtime/worker/App/saleGuide/purchase integration ownership transfers to the new TASK16 owner. This owner will not make further application/test changes or commits.

## Released behavior

Owner-scoped immutable historical sources; explicit fresh task/plan creation; source-once relevant unfinished reminders that check current cart and factual ledger, retain unresolved partial/missing gaps, and stop after ignore/decline or abandonment. Ambiguous history lists/clarifies. Current people, budget, exclusions and effective memory apply; distinct target people use exact source-group mapping, newer global people changes supersede older values, and deleted remembered defaults cannot become persistent explicit conditions. Selected mixed-pack specification shares survive as source preference while current requirements/counts/supply are recomputed.

New source selection never inherits old approval, partial-purchase consent, ledger, price or stock. Current supply preview, explicit alternative/partial decision and fresh confirmation remain separate. Existing receipt, ownership, canonical task, stop and transaction fences remain in the Python authority. Historical source and current differences are shown in retained App, with explicit source selection through actual Pi.

## Public seams and retained state

- GET `/api/v1/guide/sessions/{session_id}/history`
- POST same prefix `/history/repurchase`, with source, request key and current task/state/session anchor
- POST same prefix `/history/reminder`, explicit current-task ignore/decline
- Actual Pi `history_command` list/select, host-issued latest history reference, typed preference defaults and fresh effective memory ID/revision validation
- Existing plan-revisions, partial/alternative decisions and separate TASK04 confirmation

No DB schema change. Existing task/plan JSON and session command receipts hold source, reminder decision/dedup and selection replay. Protected task fields include history_source, history_memory, history_memory_defaults and history_reminder. Recreated group source_group_id and people_origin distinguish target identity and remembered defaults. Do not let ordinary task conditions overwrite these fields or expose a direct restore/confirmation shortcut.

## Evidence and limits

Final pair: 182/182 twice, exits 0/0, identical four snapshots/current 314 files. Fingerprint `0f1be6b11ad91dc1cdd881aace1154101fbe6ed29a2787d0357e4ea202e57d53`. History DOM twice, eight affected UI flows, compile/typecheck/build all green on the same map. Both Standards/Spec axes closed, including narrow fixes. Exact reviewed history/purchase hashes and evidence paths are in `RELEASE.json`; full reconciliation is `work/ceres2-runtime-upgrade/11/test-runs/final-history-source-comparison.json`.

Nineteen TASK11 public cases use reusable isolated two-owner Pi/dish fixtures and current-supply mutations. DOM script: `work/clean-rebuild/11/ui_history.mjs`. No inherited historical pass claims, active/old database, archive runtime import, credentials, pushes or commits by this owner.

Controlled Pi fixtures do not establish actual qwen3.8-27b provider/model behavior. DOM is not real-browser E2E. Those layers and user acceptance remain independently incomplete; overall TASK11 is 待验收.
