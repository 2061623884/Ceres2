# Official GraphRAG library/adapter component test

- Command (from `backend/`): `PYTHONPATH=<work/local-followup/tmp/offline-guard> PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ../.venv-graphrag/bin/python -m pytest -q tests/test_graph_official_library.py`
- Result: exit 0; `5 passed` in 25.91s; 12 deprecation/config warnings.
- Runtime: Python 3.11.15, `graphrag==3.2.0`, CPU Torch `2.14.1+cpu`. The GraphRAG environment does not include pytest, so test execution used its Python and imported pytest from this worktree's business `.venv` site-packages, appended by the guard's `sitecustomize`; GraphRAG and its dependencies resolved from `.venv-graphrag` first.
- Network isolation: test-only audit hook SHA-256 `0594ee798adc38be17d8503ea747376eb1ce6febd1e8f1eef4dc57d5492fa06f` rejects socket connect/connect_ex/getaddrinfo/bind/sendto. A separate preflight showed hostname resolution blocked before DNS. Pytest plugin autoload and Hugging Face/Transformers online fallback were disabled. The tests use the controlled `httpx.MockTransport`; no external provider call occurred.
- Scope: official BYOG GraphRAG 3.2.0 build and local/global query over a temporary 2-recipe/8-product fixture, plus controlled wire/usage checks. The test replaces the encoder with a deterministic no-weight implementation and provider with a local MockTransport; this is adapter/library evidence, not a real Graph build, real model quality, or product acceptance.
- Test SHA-256: `66a5b516c3c49e7bbeea974d85e08bec172ff5ab6d94a774e83873eefd96a6e8`.
- Relevant implementation SHA-256: `graph.py` `8c94e8e02ac8857e0f53e89a6429b4420f5c72f2cd9cc0746860cd436dba8921`; `providers.py` `44c55f2581c2441712b4bc7fb719576b5a2800be2798dc3335a2ae01a3253bfb`; `graph_context.py` `a9a1354e10b378344e62682712b560425c58b864521f2f8790ac0c4803e256a6`.
- Knowledge lock SHA-256: `3a82d620102bec1f9495be30ecc6705ba1109b4a20e9a48154e66de2a71df72e`.
- Raw output: ignored `work/local-followup/tmp/graph-official-library.log`, SHA-256 `1522518be4d4396c4293ef3b9371e7bccbf389986de1389c905613ecaae38c7b`.
