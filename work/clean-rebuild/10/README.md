# TASK10 — recoverable post-reply extraction and Dream

Implementation owner: `implement_clean_memory_dream`. Root owns release/commits, Tester alone executes validation. Root released controlled technical acceptance at 2026-10-05 18:43 UTC. This document is not live-model, browser or user acceptance.

## Runtime and authority

- Pi's final fenced `GuideTurnReceipt` / messages transaction and Mercury's guarded canonical case publication enqueue a source once. Only completed non-memory-management turns qualify. Enqueue performs no model call. Guide integration belongs to TASK05; shared composition/configuration/migration belongs to the foundation owner.
- The existing canonical `ShoppingMemory` table remains the only memory authority. One additive SQLite `memory_jobs` table records immutable source identity and full accepted user text, captured per-key revisions plus an explicit-change watermark, pending/running/completed/failed status, token/expiry lease, successful completion time, and sanitized failure code. No generic queue platform, shopping monitoring, or push messaging exists.
- The explicit watermark is `(COUNT(explicit rows), SUM(explicit revisions))`, including tombstones. Canonical explicit save/update/delete monotonically changes it, including equal-clock changes and automatic-to-explicit corrections. Any intervening explicit change invalidates the old background result, even when its model proposes another key. Per-key revision checks independently protect automatic updates. SQL `BEGIN IMMEDIATE` serializes claims/publication; token and live lease are rechecked at commit. The explicit fence is also checked before dispatch; Dream additionally validates captured effective winner IDs/revisions/expiry before dispatch and at commit, including expired-lease recovery.
- An unfinished job is recoverable after its 60-second lease expires. A late prior worker cannot publish after another worker reclaims the lease. Publication SQL failure preserves the unfinished lease and propagates the original SQL exception; the managed loop retries only recoverable SQL work. Model/validation failures remain durable failures and never produce a saved chat receipt. Stored errors include phase and exception class, not provider exception prose or credentials.
- The application lifespan starts/stops the memory worker. Independent extraction and Dream calls use separate settings (`MEMORY_EXTRACTION_MODEL`, `MEMORY_DREAM_MODEL`), each explicitly defaulting to `qwen3.8-27b`; there is no fallback to the main chat model. Model timeout is 20 seconds, no SDK retries; worker shutdown join is bounded to 25 seconds. The main reply does not join or wait on these model calls.

## Memory policy

- Four categories remain user / feedback / project / reference. Evidence must quote the immutable user's actual source. Current-only scope, one-off budget/people keys, forged links, assistant-only quotes and role-inappropriate domains are rejected. Automatic candidates cannot change an existing key's domain or category. A legitimate same-domain change updates origin role and source evidence truthfully.
- New automatic records expire in 30 days. Identical extraction does not change expiry, revision or original source. Dream never renews expiry or changes provenance. Expired/deleted/explicit records cannot be rewritten by Dream or extraction.
- Complete accepted source text is retained. Extraction supports up to 8,000 characters. A longer Mercury source is diagnosed as `MEMORY_SOURCE_TOO_LONG` without calling the model or extracting a misleading prefix. Evidence quotes are bounded to 4,000 characters; outputs to ten extraction records. This is a truthful bounded failure, not a claim to process every arbitrarily long Mercury message.
- Dream requires at least ten eligible automatic memories and 24 hours since the last successful Dream. Each owner has at most one active Dream, enforced by a partial unique index. Source identity includes the prior successful Dream job ID so an unchanged successful set can run at the next due period; an unchanged failed set does not hot-loop. Model context is bounded to fifty records / 20,000 serialized characters, separate from SQL revision authority.
- Dream uses the same explicit-before-automatic winner selection as TASK09 recall. Explicit-shadowed or tombstoned automatic predecessor text is excluded before eligibility counting and model input, not merely skipped at commit. The shared winner helper preserves existing recall relevance/size/current-condition behavior.

## Migration and rollback

`0010_recoverable_memory` is additive; model registration follows the already registered memory module. Synthetic pre-TASK10 memory, repeat initialization, and the active-Dream unique index are tested. No active/archived database, session, index or credential is imported. Returning to pre-TASK10 code leaves canonical memories and business facts intact and merely stops consuming the additional jobs; it must not remove existing confirmation guards or delete the new table to simulate rollback.

## Evidence

Raw Tester artifacts are under `work/ceres2-runtime-upgrade/10/test-runs/` (not this directory).

- `red-memory-background` → `green-memory-background-01`: completed real Pi chat → durable extraction → subsequent chat list; paired explicit save/list.
- `red-dream-gates` → `green-dream-gates-02`: ten / 24-hour gates and unchanged TTL. First candidate exposed a controlled-fixture hook left in list mode; fixture was corrected without weakening assertions.
- `red-managed-background-reply` → `managed-background-green`: actual application lifespan, blocked independent model, main reply delivered first; foundation regression.
- `red-late-extraction-delete` → `green-background-explicit-fence`: explicit deletion while extraction is blocked, including a model-chosen different key.
- `background-recovery-regression`: 17 passed. Duplicate source, interrupted/expired lease, stale claimant, failures, four categories, source/domain restrictions, TTL, independent config and additive migration plus TASK09 public regression.
- `background-expanded-regression-02`: 19 passed. Actual installed OpenAI SDK with controlled localhost JSON provider, two distinct configured model calls, actual LangGraph source, managed restart, Dream recovery/failure/single-owner/correction/expiry. The first Mercury fixture repeatedly issued list tools; it was corrected to finish after the real list result, preserving production behavior.
- `red-background-cross-role` → `green-background-cross-role`: actual Pi → Mercury same-key domain collision and truthful shared-domain origin.
- `red-background-review` → `green-background-review`: trailing correction beyond 4,000 characters and SQL publication fault recovery; 11 passed with regressions.
- `red-unchanged-dream-cooldown` → `green-unchanged-dream-cooldown`: unchanged successful Dream eligibility after 24 hours without failed hot retries.
- `red-dream-effective-memory-filter` → `green-effective-dream-facts`: exposed and fixed automatic predecessor text included despite an explicit same-key tombstone; 13 passed with TASK09 deletion/priority/cross-role regression, owned source stable.

Final independent runs `final-memory-background-01` and `final-memory-background-02` passed **109 / 109** (116.69s / 113.91s), including TASK09, TASK03 recovery, Mercury14/15 and foundation. `final-background-source-comparison.json` confirms the consumed backend/Pi/config/schema/tests match in all four captures: `65f02da9b92bef9ed56c6bdec659522746087d6f2497aa0bdf91d011cf62f0f1`. Only unrelated TASK06 UI/tests changes were excluded. Both Standards and Spec closed on the exact final source; see `release-source-manifest.json`. Earlier captures that flag other task lanes are not substituted for this final scoped comparison.

- `red-reclaimed-dream-privacy`: three independent source changes (explicit delete, TTL expiry, newer automatic revision) proved the old recovery path dispatched stale prose. The pre-dispatch freshness fix passed 16 cases with Dream/review/recovery regressions in `green-reclaimed-dream-privacy`.

- `red-recovered-dream-count` → `green-recovered-dream-count`: an omitted context row could expire and lower the effective count below ten; the same dispatch/commit helper now rechecks the ten-record threshold, with four focused cases passing before the final 109×2 runs.

## Visible journey and unverified layers

Use the existing 可可 / 墨墨 chat, express a sustained preference, receive the normal answer immediately, then ask “查看全部记忆”. A successful extraction appears as automatic memory with evidence/expiry; a failed model does not create a false saved record. Explicitly correct/delete during blocked background work, then query again: the explicit decision remains authoritative. Restart the isolated application with unfinished work, wait for any outstanding lease to expire, and query the recovered result.

Controlled tests run actual Pi SDK / LangGraph and, separately, the installed OpenAI SDK against local controlled HTTP. They are not live model quality/latency evidence. Secure live-provider credentials remain unavailable; no real provider sampling is claimed. Actual browser interaction and the user's own acceptance remain unverified. No new memory settings page is introduced.
