# TASK04 purchase confirmation

Fresh implementation after controlled TASK03 release. Public HTTP/SSE plus the approved ConfirmationService/CartService unit-of-work failure seam are the test boundaries. First tracer RED: actual Pi rejects the nonexistent proposal tool (Tester evidence under `work/ceres2-runtime-upgrade/04/test-runs/red-purchase-public`).

Source: current TASK04, proactive-upgrade-spec §4, ADR0001/0002, purchase-contract-map and TASK03 HANDOFF-P04. No archived source copied; no archive/reference runtime dependency. Store delivery uses explicit fixture-backed reachability and version, never live delivery claims. Plan expiration policy is version/supply invalidation rather than an invented time limit (`expires_at: null`).

Controlled technical scope is released; see the final release section and RELEASE.json. Controlled tests do not establish actual qwen3.8-27b behavior, real browser or user acceptance; those remain unverified.

## Controlled progress

- First actual SDK proposal tracer red → green (1 case).
- Text and button confirmation + selection-only revision red → green (7 cases).
- Row-add/write-hold red → green with supply, owner, task, race, rollback and migration coverage (27 cases); UI typecheck and row/restore DOM passed.
- Follow-up preserved-confirmation migration/hold case and expanded button/text/remount DOM passed separately.
- Root review identified an actual displayed-authority gap: App refreshed chat admission from a newer unseen plan, and proposal chat did not itself contain factual rows. New RED cases precede fixing a separate displayed-plan reference and deterministic factual message. The previous green runs do not imply this gap was already covered.

Memory hooks in guide/runtime/worker are coordinated TASK09 work. Its service and schema remain TASK09-owned; final source evidence must freeze both owners' hooks. All test/build/typecheck/DOM execution belongs to the dedicated Tester. Current formal state stays in progress pending review fixes, two equal-source runs and separate final acceptance layers.

## Purchase transaction / next-slice handoff

- Displayed-plan authority is independent of the run's fresh general-chat admission anchor. The actual App sends `{task_id,plan_id,plan_version,state_version,session_version}` on every chat; host text confirmation requires an exact current match. Later semantic confirmation paths must reuse this gate. No current model tool can grant cart authority.
- Exact supported confirmation phrases use the deterministic host path; actual Pi prepares factual proposals. Ambiguous ACKs ask clarification. The factual proposal text itself now presents items/counts/prices, so a closed plan sheet is not a hidden offer.
- PurchaseService.confirm is caller-owned UoW: no commit inside it or CartService.add_in_transaction. HTTP button/row adapters commit once; text finalization commits run events/messages with cart, task ledger and confirmation receipt. Receipt replay precedes stale/hold checks. Stop first blocks the claim; committed result remains factual.
- Ledger is per task/SKU and records only this task's actual added quantities. Selection/quantity revisions retain it; changing tasks or abandoning never removes cart items. Row explicit partial quantity means part of that selected row, not permission for supply-shortage partial procurement.
- A selected-only revision requires the existing SKU set; new SKU selection returns through actual Pi and host refs. No generic `partial_ok` authorization is carried forward from the retained frontend.
- Later recipe/group/supply slices should extend this plan's rows and metadata, keeping integer sale packages, fen amounts, explicit quantities and the same confirmation/display fences. TASK04 does not infer recipe coverage or merge unrelated goals.

## Review resolution and final candidate

Independent axes are recorded in [review-closures.md](review-closures.md). Both initial display-authority defects were demonstrated with new RED tests, then fixed: every chat has a separate displayed-plan reference, and App only promotes it after the factual plan sheet actually renders. A fetched plan changed by another tab is visibly reopened even when the refresh followed an unrelated question. Factual proposal/revision chat messages also contain actual selected SKU/count/price/remaining totals. Model prose is not purchase authority.

Standards duplication was removed through one existing CartService noncommitting row writer shared by shelf and confirmation; transaction ownership did not move. Duplicate internal positive-integer validation was removed because proposal-tool and public revision schemas already guarantee it.

[FINAL-CANDIDATE.json](FINAL-CANDIDATE.json) includes consumed TASK09 hooks after the separately authorized `committed=false` read-only memory-list fix. The prior TASK09 pair remains unchanged historical evidence for its exact earlier source; its owner records the narrow post-pair validation separately. TASK04 final pair starts after that correction and includes purchase, Pi/guide and checkout/cart regression.

## Controlled release: 2026-10-05 17:55 UTC

Root accepted the technical scope. Baseline final runs passed 88/88 at one exact scope fingerprint; the later one-line App lost-success recovery fix passed dedicated RED→GREEN twice plus purchase/background DOM, typecheck and build. Consumed TASK09 deletion-tombstone recall change is independently verified (focused twice +21 memory tests), and is not mislabeled as part of the older 88-case snapshot. See RELEASE.json, POST-PAIR-DELTA.json and the exact successor evidence links.

Both review axes and the narrow recovery re-review closed. Overall ticket remains 待验收 with real qwen3.8-27b, real browser and user acceptance pending. Root owns commits; no push was made. Unique guide/runtime/worker/App ownership passes to TASK05; TASK08 and TASK10 coordinate their patches through that owner.
