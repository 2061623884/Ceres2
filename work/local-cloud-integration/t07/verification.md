# T07 controlled verification

Product candidate: `0a6e8fa83d14165844e81f3d8e8d1a016c35ece2`. Cloud baseline: `37c98400e7152b89e4a58f02fff3bceaa73b0eac`. Incoming source: `6734c7fe79e670df2dae12b065dcc49c0b10a307`.

Final affected regression: **75 passed**, exit0,24.65seconds pytest time (27.164seconds capture). Eight files: `test_merge_aftersales_evidence_public.py`, `test_merge_business_migration.py`, `test_aftersales_public.py`, `test_human_public.py`, `test_checkout_public.py`, `test_aftersales_migration.py`, `test_aftersales_proposal_migration.py`, `test_guide_migration.py`. No source or harness changes during final capture. Exact commands/source sets/build/harness hashes are in verification-history.json and source-manifests.json.

## Meaningful RED/GREEN history

- Photo API first RED:2 failures (missing endpoint404); first GREEN plus inherited aftersales/human affected regression34passed.
- Sequential simulated order state RED:1 failure (missing demo-state404); GREEN plus checkout10passed.
- Additive event/photo migration RED:missing recorded_at_ms column; GREEN migration group5passed. Historical event time remains unknown/NULL.
- Expanded safety first run:17passed/2failed due to missing json import in test model; test-only correction yielded19passed. This was a fixture defect, not a product defect; failure retained.
- First candidate affected group63passed did not close review. Review exposed same-generation ordinary-return leakage into unrelated new quality/manual tickets. Both public reproductions failed. Explicit application→human-ticket foreign-key association then passed23evidence/migration checks. Unrelated owner history remains available to owner but absent from new ticket.
- Image validity RED:3 genuine PNG/JPEG/WebP passed;6 signature-only/truncated images incorrectly accepted200. Actual Pillow decoding fix produced32passed across evidence and migration tests, followed by final75affected regression.

Counts overlap and represent different candidates; never add them together.

## Isolation and dependency evidence

Fresh synthetic DB/checkpoints and fake credentials only. Python audit guard blocks dotenv/non-loopback IO; Node PATH launcher injects actual child guard even when NODE_OPTIONS is filtered. Raw logs and generated runtime files remain outside repository. No real provider, private database, original .env, model/index download or real-money workflow was used.

T07 uses a fresh Python3.12.14 environment installed from updated business lock. Only new pin is pillow12.3.0, matching incoming knowledge lock; pip check passed. PNG/JPEG/WebP static fixtures are genuine decoded1x1images. Full final capture retains source/harness hashes. Source-version variance from historical Python3.11 is explicit.

## Open gates

Postmerge T01 Mercury category/deadline wiring, final same-candidate integrated full regression, real browser and human acceptance remain separate. These75controlled tests do not satisfy those gates. Both independent review results are recorded by reviewers, not inferred from tests.
