# Spec re-review: frozen 01 repair

Decision: original P2 closed for ticket 01; no new blocking 01 Spec findings. Read-only source review, 2026-10-07.

## Exact candidate

- Base: `4bed9c891261e382122d424825b649989ea92c92`
- HEAD: `ec625a27db5418f0851a5da946c384531534309c`
- Six-file `git diff --binary HEAD` SHA-256: `500f395d80a9bdf6af9201a4f10d63ce254320cdb5cea8c773bf1ffbcf81b3f0`
- Full base-to-worktree diff SHA-256: `a9e058dcf742c47aed2a682ab2507e539235af609f79e3522e8527d6107261d3`
- Frozen manifest file SHA-256: `58cb246bf7e055b8b904f6414e6001cd35fd08d477e918b3e5b306d9892feb83`; all 244 recorded source hashes matched at start/end. Manifest: `../worktrees/01-role-entry/work/judge-prefetch-rebuild/evidence/01-review-final-focused/frozen-candidate.json`.

## Closure

Original spec lines 37/42 (current spec 43/48): “具体售后由可可说明职责并提供显式入口” and “混合请求仍保留所有子问题和条件”.

`backend/app/services/pi_product_runtime.py:331–340` validates a strict Boolean marker, runs existing answer/reference validation first, then attaches fixed host responsibility text. `pi_product_turn_service.py:224–228,257–264` retains existing messages and creates only an explicit Momo button with no route ID. Existing completed shopping/policy results and waiting clarification survive; the marker introduces no after-sales write or replay authority. Public fixtures at `backend/tests/test_judge_role_entry_public.py:359–450` cover composition, fabricated prose suppression, pure navigation, replay and invalid marker types.

No additional source-level issues found in first-context preservation, absence of capability classification, Momo zero-Kev/button return, legacy receipt guards, or seven official-DeepSeek request paths. Model choices and caps remain unchanged.

## New 01 findings

None.

## Ticket 02 carry-forward, not an 01 regression

The documented waiting shape plus a valid `policy_ref` still loses policy output: `pi_product_runtime.py:336–337,416–426`. The five-kind attachment gate already exists unchanged at the base; the new marker does not discard anything that baseline retained. Ticket 02 lines 18/32 requires complete shopping-plus-policy handling. Cover waiting + policy + role boundary there; current waiting fixture omits policy (lines 366–380).

## Release boundary

Source-level 01 Spec gate is clear, subject to frozen Tester evidence and the independent Standards gate. No tests/builds/API calls executed here. Frontend is user-local, not missing cloud scope; DOM/browser/user gates remain pending. This is not four-ticket or overall acceptance.

## Six modified source hashes

- `backend/app/prompts/experience.json`: `ccad87a2f4e638c2cb2ed02b272193d2af7b76e538a0deb581c4b7894da26f18`
- `backend/app/services/navigation_service.py`: `0baa40f74f73a72f1f0ccc8eed5003acaba25ca0e71ff501458886a78892c0ce`
- `backend/app/services/pi_product_runtime.py`: `47ee06352906b5b2a96c8722304dc024ced81b17ab7bc0b9e378fd59befb1cad`
- `backend/app/services/pi_product_turn_service.py`: `6a509c77c49c42dbef91e5a97452f25d842ef85be4c0cc4891871721db0fe960`
- `backend/tests/test_judge_role_entry_public.py`: `4a9009c244dac24ad1485e63bab54009c001376a3f7239dbb339dd4f94a6c200`
- `backend/tests/test_next_snack_public.py`: `8d31e2903f46c7c7240695d81ee441035599a9af3336dead29f0bbb4f7b964f6`
