# Batch annotation multi-capture/identity RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k 'test_annotate_batch_cli_labels_every_capture_and_final_capture_alias or test_annotate_batch_cli_rejects_capture_identity_reused_across_rows'`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256: `b09eefc1f5c8c8d9d5cdfce32be4a87569497bcee29ca92f4ce343f8d62f2721`.
- Implementation `backend/app/evaluation/annotate_batch.py` SHA-256: `ef9575a46641851285d084e4b316e09715240691ea07cd11215259b6d002574c`.
- Result: exit 1; `2 failed, 8 deselected` in 0.75s.
- Failure 1: annotation lookup rejects a valid label for the first capture of a multi-turn execution (`Unknown annotation owner/run: multi-owner / first-run`); only the row-level/final capture alias is indexed.
- Failure 2: the same owner/run capture reused across distinct rows is accepted (subprocess exit 0, `annotated=0`) rather than rejected as ambiguous/reused identity.
- Synthetic input/output files were under pytest `tmp_path`; no server or provider was started.
