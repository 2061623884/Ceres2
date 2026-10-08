# Batch annotation multi-capture/identity GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k 'test_annotate_batch_cli_labels_every_capture_and_final_capture_alias or test_annotate_batch_cli_rejects_capture_identity_reused_across_rows'`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256: `b09eefc1f5c8c8d9d5cdfce32be4a87569497bcee29ca92f4ce343f8d62f2721`.
- Implementation `backend/app/evaluation/annotate_batch.py` SHA-256: `0e44aecfeceba5ae1c49c6f10bd2bd4e08d327c6ed5e61ac9f5bdf27a9ef46bf`.
- Result: exit 0; `2 passed, 8 deselected` in 0.57s.
- Verified exact owner/run joins for every captured turn, synchronized labels on the final capture alias, and rejection of an owner/run identity reused across rows. Synthetic `tmp_path` only; no server or provider was started.
