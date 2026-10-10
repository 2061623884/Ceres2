# Baseline client/SSE timing GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k baseline_cli_measures_client_sse_arrival_and_keeps_missing_interim_unknown`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (current uncommitted implementation slice).
- Test source: `backend/tests/test_local_followup_baseline.py`, SHA-256 `d8b21c6d16f9879960bdb70837676f03d4aa8ebdc114c9655567465c03ebe4ab`.
- Implementation: `backend/app/evaluation/run_baseline.py`, SHA-256 `f7ddf61f3ee594833438906a279e39270481025c45ba989b6363aa1d9ac4d592`.
- Result: exit 0; `1 passed, 3 deselected` in 1.06s.
- The test uses a loopback fixture, shuts it down/closes it/joins its thread in `finally`, and does not start the app or a model provider. It checks client-side SSE arrival timing and leaves missing interim timing unknown.
