# Real local BGE/hybrid smoke on the current worktree index

- Command (from `backend/`): `CERES_REAL_BGE_INDEX=<absolute current-worktree data/indexes/hybrid.sqlite3> PYTHONPATH=<work/local-followup/tmp/offline-guard> PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ../.venv-graphrag/bin/python -m pytest -q tests/test_graph_real_bge.py`
- Result: exit 0; `4 passed` in 9.70s. The public retrieval development subtest passed all 18 cases; its full per-case output is retained at `work/local-followup/tmp/real-bge-public-dev-report.json` (SHA-256 `8cc721432f7a48a8370d073a53edb490addc0eba8d1e16299063126206f19c22`). The report records zero failed cases.
- Runtime: `.venv-graphrag` Python 3.11.15, GraphRAG 3.2.0, Torch 2.14.1+cpu, Transformers 5.19.0, Hugging Face Hub 1.33.0. Pytest was loaded from this worktree's business `.venv` site-packages via the offline guard; knowledge/model packages resolved from `.venv-graphrag`.
- Network isolation: same ignored test-only audit hook SHA-256 `0594ee798adc38be17d8503ea747376eb1ce6febd1e8f1eef4dc57d5492fa06f`; all socket connect/DNS/bind/sendto operations are denied, with HF/Transformers offline flags. No paid or external model/provider request occurred.
- Current index: `data/indexes/hybrid.sqlite3`, SHA-256 `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`, 499,712 bytes. Its embedded hashes exactly match the current worktree's knowledge implementation and all five current `data/fixtures` source files. Counts are 73 product, 8 recipe, 11 policy documents; embeddings are 512-dimensional.
- Model: public `BAAI/bge-small-zh-v1.5`, revision `7999e1d3359715c523056ef9478215996d62a620`, loaded from this worktree's own `.cache/huggingface` snapshot. `model.safetensors` is 95,827,648 bytes, SHA-256 `354763b9b1357bc9c44f62c6be2276321081ed2567773608c0d0785b61d5a026`; the snapshot's six required files all resolve inside this worktree.
- Test SHA-256: `a109c81fd51495a2790f6e24846538c2fe45d7d9e4cbc3725e8387c6debf1942`.
- Implementation SHA-256: `bge.py` `08dbcbd1206f600fcda8674807381203caaab74f19e329e110dbc989232b3e16`; `corpus.py` `819e216dcc7a0eaaeee3daaafd037a18910b05a26be4c65220177d8915eaaacd`; `hybrid.py` `2fcf437313526cb564939adca2c6198edbdcb073293ec1079797b64467a6d8ca`.
- Retrieval development source SHA-256: `eb47a57f89fc65d56d3e74a9b68947d096ba485d5c08051f29dc9a97aa12652e`.
- Knowledge lock SHA-256: `3a82d620102bec1f9495be30ecc6705ba1109b4a20e9a48154e66de2a71df72e`.
- Raw output: ignored `work/local-followup/tmp/graph-real-bge.log`, SHA-256 `faa512581a6cd4cf424ea75b2f0b2ce63c1b22b070e2033dfcf83d8291ec3463`.

This verifies the current real local embedding/index path and the finite public development retrieval set. It is not a real-provider GraphRAG build/query or independent acceptance evaluation.
