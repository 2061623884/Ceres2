# GraphRAG official build attempt

Date: 2026-10-07 (Asia/Shanghai)\
Worktree: `Ceres2-optimization-20261007`\
GraphRAG environment: isolated `.venv-graphrag`, Python 3.11.15, GraphRAG 3.2.0\
Provider config source: current Ceres2 `.env`, selected values loaded into this test process only; reported model `deepseek-flash`, host `api.deepseek.com`. No key was printed or persisted.

## Commands and result

| Command | Working directory | Exit |
| --- | --- | ---: |
| `../.venv-graphrag/bin/python ../work/ceres2-optimization/testing/graph_schema_smoke.py` | `backend/` | 0 |
| `../.venv/bin/python ../work/ceres2-optimization/testing/provider_config_probe.py` | `backend/` | 0 |
| `../.venv-graphrag/bin/python ../work/ceres2-optimization/testing/provider_smoke.py` | `backend/` | 0 |
| `../.venv-graphrag/bin/python ../work/ceres2-optimization/testing/graph_build_smoke.py` | `backend/` | 1 |
| `.venv-graphrag/bin/python work/ceres2-optimization/testing/bge_concurrent_init_smoke.py` | worktree root | 1 (reproduced) |

The schema smoke used synthetic config values and made no provider requests. The separate provider smoke used the approved current Ceres2 config: structured Pydantic response succeeded (166 prompt, 11 completion, 177 total tokens); a short streamed response succeeded (49 prompt, 4 completion, 53 total tokens).

## Build failure

The official BYOG workflows wrote deterministic graph inputs, generated communities and community reports, then failed in `generate_text_embeddings`. The error was `ImportError: cannot import name 'AutoModel' from transformers` at `backend/app/knowledge/providers.py` while `embedding_async()` dispatched model initialization through `asyncio.to_thread(encoder)`.

A minimal two-thread barrier smoke reproduced the same failure: one worker initialized BGE successfully and the other failed importing `AutoModel`. The existing single-thread BGE smoke had passed, so it did not cover concurrent first use. This points to concurrent initialization through the current cached encoder call path; the Tester did not modify product code.

Partial GraphRAG output has 44 entities, 61 relationships, 26 text units, 26 documents, 11 communities, and 11 community reports. One `text_unit_text.lance` dataset began writing. The application did not write `manifest.json`, because `graph.build()` raises as soon as a workflow result contains an error. No GraphRAG query was run. The failed output is preserved under `tmp/graph-build-partial-2026-10-07/` for inspection and is git-ignored; it is not a complete index.

## Clean retry after the initialization fix

The production BGE loader was changed to single-flight initialization. The same two-thread first-use smoke then passed (both calls returned the same 512-dimension encoder instance), exit 0; the original failure JSON above remains unchanged.

The GraphRAG build was rerun into a clean default worktree index and passed, exit 0. It wrote 44 entities, 61 relationships, 26 text units, 26 documents, 11 communities, 11 community reports, and the three 512-dimensional Lance tables. Build made 11 completion calls and 8 local embedding calls. Completion usage totals were 31,817 prompt, 12,111 completion, and 43,928 total tokens. The manifest records the exact fixture and knowledge implementation source hashes.

The artifact audit passed: all 44 graph entities appear in community membership; all three Lance tables have the expected row counts and 512-dimensional vectors. `community.relationship_ids` cover 39 of 61 edges; GraphRAG does not assign every cross-community edge to a community. This was recorded for review but was not a build acceptance condition.

Both requested real queries completed, exit 0. Local search returned the tomato and egg quantities, seasoning facts and candidate SKUs with source citations. The global response named several egg dishes but incorrectly stated that the `番茄炒蛋` recipe did not record an egg requirement, despite the canonical fixture's `egg 3pc` and graph relationship. Treat that output as a quality limitation, not an accepted fact. Both result contexts passed the entity/relationship source-map round-trip checks. The v1 query sample and successful GraphRAG index are preserved under ignored `testing/tmp/graph-query-v1-2026-10-07.json` and `testing/tmp/graphrag-v1-success-2026-10-07/`; the v1 hybrid index is under `testing/tmp/hybrid-v1-success-2026-10-07.sqlite3`. Artifact and build summaries are in `graph-artifact-audit-2026-10-07.json` and `graph-build-smoke-2026-10-07.json`.

The v1 build emitted a tokenizer warning for a 1,080-token string above the model's 512-token limit. The model input itself was truncated to 512; the warning came from uncropped token-count instrumentation. The v2 provider count now applies the same 512-token truncation and the warning did not recur.

## Current v2 build and query

After the source fixtures were versioned `optimization-demo-v2`, the hybrid index and GraphRAG output were rebuilt from clean paths. Commands `../.venv-graphrag/bin/python -m app.knowledge.cli build-hybrid`, `../.venv-graphrag/bin/python ../work/ceres2-optimization/testing/retrieval_dev_eval.py`, `../.venv-graphrag/bin/python ../work/ceres2-optimization/testing/graph_build_smoke.py`, `.venv-graphrag/bin/python work/ceres2-optimization/testing/graph_artifact_audit.py`, and `../.venv-graphrag/bin/python ../work/ceres2-optimization/testing/graph_query_smoke.py` all exited 0. The v2 Graph build has no tokenizer-length warning.

The 18-case v2 hybrid report contains raw sparse, dense and RRF rankings plus filtered hits: 13/13 positive targets are within hits Top 3, 5/5 negative cases have no hits, and potato-chip SKUs are absent from hits. As before, this is a development sample, not an independent acceptance set.

The v2 Graph output keeps the same 44/61/26 source graph counts, 11 communities and 11 reports, 44/44 entity coverage, and three 512-dimensional Lance tables. Completion usage was 33,478 prompt, 12,784 completion, 46,262 total tokens. Local query and global query both passed source-map round trips. The sampled answers report `番茄 300g / 鸡蛋 3pc` and all four recipes with egg quantities matching `optimization-demo-v2` fixtures. A content audit also found a remaining contradiction: the global answer lists pork as `meat`, then claims pork's kind is unknown; canonical `ingredients.json` sets `pork.kind=meat`. See `graph-query-v2-content-audit-2026-10-07.json`. This single sample does not establish general GraphRAG answer reliability.
