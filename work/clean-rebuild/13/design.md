# TASK13 implementation boundary

Acceptance: an explicit Contact Mercury click carries the exact canonical order ID into the independent Mercury selection API, displays the selected order's canonical metadata, and never silently sends a chat message or confirms checkout. Owner-bound case query and restart use existing canonical store and real LangGraph.

Existing P02/P12 SimulatedOrder and MercuryCase already share the same Base, Session and business database. No new database/schema, migration, adapter or dual write is needed. Existing additive P12 migration and synthetic historical fixtures remain relevant regression targets; unknown store remains null. No archived database/owner/time is imported.

UI owns explicit entry sequence so repeated contact for the same order remains an action after a manual selection. Each restore/entry gets a generation token; late async reads, selections and stream results cannot overwrite the current case. The API still validates owner and selection version. Selection is not query consent and causes no automatic model invocation.

Fresh tests: backend/tests/test_order_case_journey.py and work/clean-rebuild/13/ui_contact.tsx. Dedicated Tester alone executes tests/build/typecheck. Controlled model/DOM evidence is distinct from live qwen, browser layout and user acceptance, which remain TASK16.

Source provenance: small edits to current clean P02/P12 implementation and retained frontend only. No source imported from archive/reference and no old runtime/dependencies used.

Spec-review correction: the contact intent lives in the App parent as an atomic {orderId, sequence}. Mercury acknowledges only the successfully consumed sequence; App clears that exact intent without touching the canonical selection. This prevents contact B → manually select A → leave the page (full unmount) → reopen from replaying B. Every fresh explicit contact still performs CAS, even if its ID equals the currently read case order, so a delayed previous selection cannot silently change the authority afterward.
