# Product baseline 170 full backend regression

- Source: detached commit `170fac0bc75fcc855897b073337ba218abeb5b7d`, tree `295499ee22cc30485d38eba82e96330a39d7d573`. Frozen source copy: [product-baseline-170](../tmp/product-baseline-170); aggregate tracked-source manifest SHA-256 `bb492de3fc0f58a319805c0fa2c3138918dce4cdc8edb2ffe7f8a600447290e0`.
- Worktree source path: `work/local-followup/tmp/product-baseline-170`; suite ran from its `backend/` directory with a clean environment, the independent GraphRAG Python environment, loopback-only test guard, offline Hugging Face flags, and the current worktree's 170-compatible BGE index. No `.env`, database, session, checkpoint, or external provider was used.
- Full command: `python -m pytest -q` from the frozen copy's `backend/`, via `.venv-graphrag/bin/python` and the isolated environment described above. The exact initial shell invocation was not persisted separately; raw output is retained below. This provenance gap is recorded rather than reconstructing an unverified full command string.
- Result: exit 1; **752 passed, 4 failed, 12 warnings** in 1587.15 seconds. Raw log SHA-256 `6bec1b819f6ced39da7ec4d7e1e3f739cbadaeaa160b8c6e2edce57d22ba3c9b`.

The four failures were test-environment setup failures in the frozen copy, not product assertions:

- `test_collection_ignores_parent_credentials_and_dotenv`: its nested clean subprocess uses `sys.executable -m pytest`; the selected `.venv-graphrag` interpreter does not install pytest. Rerunning this exact test from the same frozen source with the worktree's business `.venv/bin/python` passed: 1 passed. The child retains synthetic-only settings and the test's audit hook.
- `test_real_bge_index_shape_and_three_namespaces`, `test_real_bge_public_dev_relevance_and_rrf`, and `test_real_bge_cold_and_same_worker_query_deadlines`: the frozen copy's `HF_HOME` had no pinned model snapshot, while network was intentionally disabled. Copied the current worktree's own fixed-revision BGE cache into the ignored frozen copy; all six files match the current model download record, including `model.safetensors` SHA-256 `354763b9b1357bc9c44f62c6be2276321081ed2567773608c0d0785b61d5a026`. Rerunning the complete `test_graph_real_bge.py` file with offline flags and the loopback guard passed: 4 passed. It used the worktree-generated `data/indexes/hybrid.sqlite3`, SHA-256 `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`.

The four affected tests therefore passed under their corrected test-only environments, but the original full-suite result remains 752/4 and is not relabeled as a full-suite pass. No product source was modified. Corrected-scope logs:

- Isolation interpreter correction: `work/local-followup/tmp/baseline170-isolation-interpreter-fix.log`, SHA-256 `a1454a5c39c18e1948d9b22b80323d50591f8b398985c78999d8d0b8b6a822a5`.
- Offline BGE-cache correction: `work/local-followup/tmp/baseline170-real-bge-cache-fix.log`, SHA-256 `6b378b265b8065787bfbddf5774cf6a7e0b373a816ca46a75d934cdbb17818d4`.

The reruns used baseline test sources `test_controlled_test_isolation.py` SHA-256 `1b9f268780c0532d477494d072c340ec57443a2744394a4bdd6953d71700b933` and `test_graph_real_bge.py` SHA-256 `a109c81fd51495a2790f6e24846538c2fe45d7d9e4cbc3725e8387c6debf1942`. The baseline product scope remains distinct from the later evaluation-tool source and tests.
