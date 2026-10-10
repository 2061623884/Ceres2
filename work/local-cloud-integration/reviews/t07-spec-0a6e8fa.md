# T07 Spec fix re-review

Frozen HEAD: 0a6e8fa83d14165844e81f3d8e8d1a016c35ece2. Baseline: 37c98400e7152b89e4a58f02fff3bceaa73b0eac. Worktree: /workspace/scratch/0c1b4cfa2ef3/ceres2_t07_aftersales (HEAD verified, clean at inspection). Full baseline...HEAD diff and commit list saved alongside this report. Delta examined against prior reviewed fc6a3ada162dbeef393972a6ba68f635355fa80f. Scope remains the two T07 Spec findings, excluding unrelated planning/static-source changes.

## Result

Both previously reported findings are resolved by static inspection. No remaining blocking Spec finding identified in this correction delta.

- P1 resolved: the requirement “人工视图和照片读取以该 ticket 的实际关联证据为范围” is now enforced by AfterSalesApplication.human_ticket_id == ticket.ticket_id in backend/app/human/service.py::ticket_evidence, in addition to owner/case/order/generation fences. backend/app/mercury/aftersales.py::submit sets the exact application link after create_ticket and before the same transaction commits. Photos still originate only from that application's confirmed receipt photo_ids. The nullable FK migration leaves historical applications unassociated; it does not invent links. Public regression source covers same-generation return→quality and return→manual handoff, preserving independent owner receipt history; migration source covers legacy NULL and invalid FK rejection.

- P2 resolved: backend/app/mercury/aftersales.py::upload_photo retains the 4 MiB compressed-byte maximum, restricts Pillow formats to JPEG/PNG/WebP, checks actual format against declared MIME, verifies structure, reopens and loads pixel data, and turns Pillow decompression-bomb warnings/errors into PHOTO_INVALID. Genuine tiny format fixtures replace the fake PNG; regression source includes valid roundtrips and header-only/truncated rejection. Pillow 12.3.0 appears in both dependency declaration and lock. No decoder execution or installation was performed by this reviewer.

## Phase boundary

This is static Spec re-review only, not test acceptance. Current Tester execution is independent and its pending results are not inherited. T01 Mercury deadline/category wiring remains deferred, requiring a later delta review. Whole-branch stop/deadline behavior, integrated test acceptance, and final baseline-to-integration review remain outstanding. Existing additive NULL event-time behavior and non-destructive recovery instructions remain intact.
