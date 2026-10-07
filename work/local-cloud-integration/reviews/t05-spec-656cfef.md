# T05 order navigation correction: independent Spec re-review

Fixed HEAD: `656cfef8e0c0a5cd23d812c3e4840b64cb4c8495`; previously reviewed product: `3892f6fbcafd9fc438edcb878ecd2a0c4799ae93`. Clean worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T05-ui`. Commands: `git diff 3892f6fbcafd9fc438edcb878ecd2a0c4799ae93...656cfef8e0c0a5cd23d812c3e4840b64cb4c8495` and matching `git log --format=fuller`; outputs saved alongside. Implementation handoff read; review closure is based on the fixed source.

## Result

The prior P2 order-navigation finding is resolved by static inspection. No new Spec finding identified in this narrow delta.

T05 requires “同订单/异单、关闭重开和前后导航”. `frontend/src/SimulatedOrders.tsx::SimulatedOrdersScreen` now advances a view generation on each detail opening, Back, and unmount. An asynchronous detail response/error can affect the screen only if its captured generation remains current. Order advancement also captures the selected order ID; success changes the visible detail only for both the original generation and identity. Failure cannot clear a later order or inject its error into that later view.

A previously authorized A advancement still updates A's list row on success, preserving its actual business outcome without taking over B's detail. Back or reopening even the same order invalidates the earlier view completion. Unmount invalidates the old instance, so its result does not populate a newly mounted orders screen. The underlying authorized operation is neither retried nor cancelled by navigation.

The new controlled public DOM regression exercises delayed success and delayed failure across A→advance→Back→B, checks B remains displayed and “联系墨墨” targets B, and asserts exactly one advancement request. The only other delta is an embedded synthetic PNG-byte replacement in the browser script; production changes are confined to SimulatedOrders.tsx.

## Limits

No tests, builds, server or browser execution by this reviewer. Tester-reported RED→GREEN and related orders/contact DOM, strict TypeScript and build checks are separate execution evidence. This closes the static Spec finding only. CUA remains pending; the earlier Chromium IPC launch failure is not rewritten as a browser pass. Final same-pin integrated and user acceptance remain separate gates.
