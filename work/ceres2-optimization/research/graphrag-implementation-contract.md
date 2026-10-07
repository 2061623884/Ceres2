# GraphRAG 3.2.0 实施契约

核验日期：2026-10-07。本文按用户已批准的完整 GraphRAG 路线整理接口边界，不再讨论是否采用图检索。代码/API以 Microsoft `v3.2.0` tag 为准；DeepSeek 文档与 BGE 模型卡按核验日的官方页面为准。这里是源码与文档核验，不代表已完成索引、查询或效果测试。

## 结论

1. **BYOG 不负责从 text units 自动抽取实体和关系。** GraphRAG 的 BYOG workflow 明确假定文本切分、实体抽取、关系抽取已经完成。把确定性生成的 `entities.parquet`、`relationships.parquet`（以及 `text_units.parquet`）放到 `output_storage` 指定的目录，再运行 `[create_communities, create_community_reports, generate_text_embeddings]`：它会生成 communities、community reports 和 configured embeddings。Global 使用 entities/communities/reports；附上 text units 和 relationships 后，Local 也具备所需表与 embedding。GraphRAG 不会从 text units 补造缺失的实体/关系。[BYOG v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/docs/index/byog.md) [默认索引工作流 v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/config/init_content.py)

2. **Python API 已确认，CLI 不适合注册本地模型。** `graphrag==3.2.0` 独立环境已安装，Tester 只读确认 `from graphrag import api` 与 `api.build_index` 可用，未执行 index/query。正式实现可从 Python 注册自定义 completion/embedding，再调用 `await api.build_index(config=...)` 和 `await api.global_search(...)` / `await api.local_search(...)`。`load_config` 应从 `graphrag.config.load_config` 模块显式导入；该模块的 `load_config(root_dir, cli_overrides=None)` 返回 `GraphRagConfig`。[API 导出 v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/api/__init__.py) [index API v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/api/index.py) [query API v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/api/query.py) [load_config v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/config/load_config.py)

3. **DeepSeek 可以通过官方自定义 completion 接口适配，但要做客户端 schema 校验。** GraphRAG 3.2.0 的标准 LiteLLM completion 使用 `litellm.completion`，而 DeepSeek Chat Completions 官方当前只公布 `text` / `json_object` 两种 `response_format`，没有 Chat JSON Schema 模式。DeepSeek 新 Responses API 则列出 JSON Schema，但 GraphRAG 3.2.0 的默认 completion provider 不是 Responses API。可实现一个 `LLMCompletion` 自定义 provider：取 GraphRAG 传入的 Pydantic `response_format`，把其 schema 纳入 DeepSeek Chat JSON-mode 提示，提交 `response_format={"type":"json_object"}`，再用该模型校验返回 JSON 并放入 `LLMCompletionResponse.formatted_response`。这保证应用只接收符合模型的解析结果；DeepSeek 本身只保证 JSON 语法，模型字段形状仍必须由真实请求 smoke 验证。非法 JSON/不符合模型时让校验错误原样失败，不猜测修复、fallback 或重试。[GraphRAG 模型要求](https://microsoft.github.io/graphrag/config/models/) [GraphRAG LLMCompletion 与结构化响应 v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/completion/completion.py) [response structuring v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/utils/structure_response.py) [DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/) [DeepSeek Responses API](https://api-docs.deepseek.com/api/create-response/)

4. **本地 BGE-small-zh-v1.5 可通过 GraphRAG 的 embedding registry 实现。** `LLMEmbedding` 的实现需要提供 sync/async embedding，返回 `LLMEmbeddingResponse`；`register_embedding(type, initializer)` 是官方扩展点。另一种方式是将 BGE 部署为 OpenAI-compatible `/v1/embeddings` 本地服务，再由 LiteLLM 的 `openai` provider 配置 `api_base` 调用。该模型是 512 维、MIT 许可。GraphRAG 的 `vector_store.vector_size` 用来设置各 embedding index 的默认维数；本模型应设 512。模型卡建议 query-only 短查询前缀、passage 不加前缀；由于 GraphRAG 的统一 embedding 协议只收 `input`，没有 query/document 标记，先采用两端都不加 instruction 的 v1.5 模式更适合一致实现，之后再由评测决定是否需要拆分 query embedding 行为。[GraphRAG embedding protocol v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/embedding/embedding.py) [embedding registry v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/embedding/embedding_factory.py) [GraphRAG v3.2.0 vector config](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/config/models/graph_rag_config.py) [BGE-small-zh-v1.5 model card](https://huggingface.co/BAAI/bge-small-zh-v1.5)

## v3.2.0 数据表契约

BYOG 文档列的最小社区构建字段与完整输出字段有区别。建议输入采用 GraphRAG 的完整 final schema，避免只满足 communities workflow 却在 Local query adapter 中缺列。

| Parquet | BYOG 明确要求的最小字段 | 建议使用的完整 v3.2.0 final 字段 |
|---|---|---|
| `entities.parquet` | `id`, `title`, `description`, `text_unit_ids` | `id`, `human_readable_id`, `title`, `type`, `description`, `text_unit_ids`, `frequency`, `degree` |
| `relationships.parquet` | `id`, `source`, `target`, `description`, `weight`, `text_unit_ids` | `id`, `human_readable_id`, `source`, `target`, `description`, `weight`, `combined_degree`, `text_unit_ids` |
| `text_units.parquet` | 查询需要 `id`, `text` | `id`, `human_readable_id`, `text`, `n_tokens`, `document_id`, `entity_ids`, `relationship_ids`, `covariate_ids` |

这些 final-column 名称来自 v3.2.0 的 `data_model/schemas.py`；Local adapter 明确将 `id/title/type/human_readable_id/description/text_unit_ids/degree` 读作实体字段，将 `id/human_readable_id/source/target/description/combined_degree/weight/text_unit_ids` 读作关系字段，将 `id/text` 读作 text unit 字段。[schema v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/data_model/schemas.py) [query adapters v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/indexer_adapters.py)

关系端 `source` / `target` 必须是对应实体的 `title`，不是实体 `id`：community builder 会按关系端点与 `entities.title` 精确 join，再映射到 entity IDs。`text_unit_ids` 是实体/关系所引用的 text-unit IDs；text unit 的 `entity_ids` / `relationship_ids` 则引用实体/关系 ID。BYOG 文档特别说明 edge `weight` 对 Leiden community clustering 有用。数量、单位和 SKU 匹配应保留在确定性业务数据中；GraphRAG reports 与自然语言检索不作为购物数量或交易写入的计算来源。[community workflow v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/index/workflows/create_communities.py)

### BYOG workflow 与输出

将原始/规范化的 graph tables 放在 `output_storage.base_dir` 指向的目录。按 GraphRAG v3.2.0 项目初始化模板，设置文件用 `output_storage:`（不是旧文档中出现的 `output:`）；`GraphRagConfig` 还使用 `input_storage:`、`table_provider:` 和 `vector_store:`。BYOG 的说明文档将 tables 描述为 output folder 中的 parquet 文件。[初始化 YAML 模板 v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/config/init_content.py) [GraphRagConfig v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/config/models/graph_rag_config.py) [BYOG v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/docs/index/byog.md)

最小 settings 形状（completion registry 名称按 Python 实现注册；embedding registry 同理）：

```yaml
completion_models:
  deepseek_json_mode:
    type: deepseek_json_mode
    model_provider: openai
    model: deepseek-flash
    api_base: https://api.deepseek.com
    api_key: ${DEEPSEEK_API_KEY}
    auth_method: api_key

embedding_models:
  bge_local:
    type: bge_local
    model_provider: local
    model: BAAI/bge-small-zh-v1.5

output_storage:
  type: file
  base_dir: output

vector_store:
  type: lancedb
  db_uri: output/lancedb
  vector_size: 512

workflows:
  - create_communities
  - create_community_reports
  - generate_text_embeddings

cluster_graph:
  use_lcc: false

embed_text:
  embedding_model_id: bge_local
  names:
    - text_unit_text
    - entity_description
    - community_full_content

community_reports:
  completion_model_id: deepseek_json_mode

global_search:
  completion_model_id: deepseek_json_mode

local_search:
  completion_model_id: deepseek_json_mode
  embedding_model_id: bge_local
```

`output_storage`, `vector_store.vector_size`, and custom type loading are sourced from the installed v3.2.0 config classes/template and the Python provider factories. The official BYOG docs say the three-workflow list is sufficient for all three outputs; include `text_units.parquet` to enable Local/DRIFT/Basic. Global specifically uses generated `entities`, `communities`, and `community_reports`; Local additionally reads `text_units` and `relationships`, and its query engine opens the `entity_description` vector index. With all three embedding names enabled, the entity, text-unit, and report vector stores use the same 512-dimensional BGE instance.[BYOG workflow details](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/docs/index/byog.md) [Local query implementation v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/api/query.py)

### `use_lcc` warning

Set `cluster_graph.use_lcc: false` for the initial BYOG build unless graph titles are normalized to uppercase and their coverage is explicitly checked. v3.2.0 `stable_lcc.py` uppercases relation endpoints, while `create_communities.py` later joins those values back to the case-sensitive original entity titles. Microsoft issue #2427 remains open/backlog and reports silent community omissions for mixed-case BYOG titles; it reports v3.1.0, but the normalization and exact join are still visible in the v3.2.0 tag source. With LCC disabled, smoke should verify `communities.entity_ids` covers the intended graph entities.[stable_lcc v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/graphs/stable_lcc.py) [community join v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/index/workflows/create_communities.py) [open issue #2427](https://github.com/microsoft/graphrag/issues/2427)

## 最小 Python 调用

```python
from pathlib import Path
import pandas as pd
from graphrag import api
from graphrag.config.load_config import load_config

root = Path("<graphrag-project-root>")
config = load_config(root)

# register_completion("deepseek_json_mode", DeepSeekJsonModeCompletion)
# register_embedding("bge_local", LocalBgeEmbedding)
# Import the module that registers both before creating providers.

index_results = await api.build_index(config=config)
# Inspect each PipelineRunResult.error before declaring the index ready.

output = root / "output"
entities = pd.read_parquet(output / "entities.parquet")
relationships = pd.read_parquet(output / "relationships.parquet")
communities = pd.read_parquet(output / "communities.parquet")
reports = pd.read_parquet(output / "community_reports.parquet")
text_units = pd.read_parquet(output / "text_units.parquet")

# Select an actual level from this built index.
level = int(communities["level"].max())
answer, context = await api.global_search(
    config=config,
    entities=entities,
    communities=communities,
    community_reports=reports,
    community_level=level,
    dynamic_community_selection=False,
    response_type="Multiple Paragraphs",
    query="<query>",
)

local_answer, local_context = await api.local_search(
    config=config,
    entities=entities,
    communities=communities,
    community_reports=reports,
    text_units=text_units,
    relationships=relationships,
    covariates=None,
    community_level=level,
    response_type="Multiple Paragraphs",
    query="<query>",
)
```

Actual signatures in the `v3.2.0` source are:

- `await api.build_index(config, method=Standard, is_update_run=False, callbacks=None, additional_context=None, verbose=False, input_documents=None) -> list[PipelineRunResult]`.
- `await api.global_search(config, entities, communities, community_reports, community_level, dynamic_community_selection, response_type, query, callbacks=None, verbose=False)`.
- `await api.local_search(config, entities, communities, community_reports, text_units, relationships, covariates, community_level, response_type, query, callbacks=None, verbose=False)`.
- `load_config(root_dir, cli_overrides=None) -> GraphRagConfig`.

These public APIs are marked experimental/unstable by GraphRAG itself; pin `graphrag==3.2.0` and treat an upgrade as a versioned migration, not an unpinned dependency refresh.[index API](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/api/index.py) [query API](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/api/query.py) [release v3.2.0](https://github.com/microsoft/graphrag/releases/tag/v3.2.0)

## DeepSeek adapter contract

The standard OpenAI-compatible endpoint parameters are `api_base=https://api.deepseek.com`, `model=deepseek-flash` (or another currently supported DeepSeek model ID), and an API key. That endpoint configuration alone does not provide JSON Schema mode on Chat Completions. The Chat API currently documents `response_format.type` as only `text` or `json_object`; its Responses API documents a `json_schema` text format. [DeepSeek first API call](https://api-docs.deepseek.com/guides/codex) [Chat API response_format](https://api-docs.deepseek.com/api/create-chat-completion/) [Responses API format](https://api-docs.deepseek.com/api/create-response/)

The registry seam and concrete response fields from installed/tagged 3.2.0 source:

- `register_completion(completion_type: str, completion_initializer: Callable[..., LLMCompletion], scope="transient")`.
- `LLMCompletion.__init__(*, model_id, model_config, tokenizer, metrics_store, metrics_processor=None, rate_limiter=None, retrier=None, cache=None, cache_key_creator, **kwargs)`.
- Implement `completion(**LLMCompletionArgs)` and `async completion_async(**LLMCompletionArgs)`. For structured calls, `response_format` is a Pydantic model class and streaming is not supported.
- Return an `LLMCompletionResponse` that follows the ChatCompletion shape and sets `formatted_response` to the validated Pydantic instance. The default GraphRAG/LiteLLM wrapper runs `structure_completion_response(content, response_format)`, whose behavior is JSON parse plus model construction. The custom DeepSeek adapter should do the same validation explicitly after requesting JSON mode, then return the original valid JSON text in `choices[0].message.content` and typed value in `formatted_response`.
- The custom provider is activated by the model's `type` name, such as `type: deepseek_json_mode`; custom registry use requires library integration, not the CLI.

The implementation should include schema fields in the message sent to DeepSeek because DeepSeek's Chat JSON mode guarantees syntactically valid JSON, not conformance to a Pydantic schema. When local validation fails, surface that failure so the smoke identifies incompatibility. Do not silently accept fields that fail the schema, repair the response with another model call, or change the user's selected model. If any GraphRAG code path consumes plain `.content` instead of `.formatted_response`, its local validation still has to happen in the adapter before returning.

## Local BGE registry contract

`BAAI/bge-small-zh-v1.5` is a Chinese model with a 512-dimensional embedding and MIT license. Official model-card Transformers usage uses CLS pooling and L2 normalization; it supports omission of the query instruction for v1.5 with only slight retrieval degradation. Keep the exact same model revision, pooling, normalization, preprocessing, and 512 dimensions across index and query. Do not change models without rebuilding the corresponding vector indexes.[model card](https://huggingface.co/BAAI/bge-small-zh-v1.5)

`LLMEmbedding` requires sync/async implementations and a `metrics_store` / `tokenizer` property; `LLMEmbeddingResponse` is an OpenAI `CreateEmbeddingResponse` carrying `data[].embedding`. The factory passes `model_id`, `model_config`, `tokenizer`, metrics/rate-limit/retry/cache components, and extra model-config fields to the initializer. Implement the wrapper as a small GraphRAG adapter over the loaded BGE model, return one response item per input string, and register it before `build_index` and query provider creation. For an OpenAI-compatible local server, use the `litellm` provider with `model_provider: openai`, `api_base: http://<local-service>/v1`, the server's embedding model ID and configured API key; it must implement the embeddings response shape and return 512 floats per item. The source supports the `api_base` field and forwards it to LiteLLM.[Embedding API](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/embedding/embedding.py) [embedding factory](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/embedding/embedding_factory.py) [ModelConfig](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/config/model_config.py)

## Smoke gate before full indexing

Use a tiny, hand-checked slice of real recipes/catalog data and the real configured DeepSeek/BGE implementations; do not use GraphRAG's mock providers. The smoke is a gate before the full corpus, not a quality claim. Verify:

1. Input parquet contains the stated required columns; every edge endpoint exactly matches an entity title; all linked text-unit IDs exist; IDs are stable; numeric quantities and units are preserved in their canonical business records/text, not derived from GraphRAG's generated report.
2. `await api.build_index(...)` completes all three configured workflows without `PipelineRunResult.error`; generated entity and relationship tables retain intended rows; generated communities cover all intended entity IDs (especially with LCC disabled); reports exist and are non-empty; BGE writes 512-dimensional vectors to all configured index names.
3. A real Global and Local query each returns a response and a context object with relevant source records. Inspect the selected context for recipe↔ingredient↔SKU facts and ensure any report-synthesized claims remain attributable to those inputs.
4. Exercise each Pydantic structured response used by the real indexing workflows at least once through the DeepSeek adapter. Confirm `formatted_response` is typed and validation failures stop the workflow. JSON mode syntax alone is not a pass.

### Verification record

Tester reports `graphrag==3.2.0` installed in the isolated worktree environment `.venv-graphrag/lib/python3.11/site-packages`; `from graphrag import api`, `api.build_index`, and explicit `from graphrag.config.load_config import load_config` were introspected successfully. Their report says no GraphRAG indexing or query has run yet; a BGE local encoding smoke was still in progress when this file was prepared. This research did not run tests, index a corpus, call a model, or measure retrieval quality.


## Installed 3.2.0 provider and context addendum

This addendum cross-checks the installed graphrag==3.2.0 / graphrag_llm sources in the isolated worktree environment. It is source inspection only; no provider, index, or query was run.

### Minimal provider imports and response shapes

The supported public import paths are:

    from collections.abc import AsyncIterator, Iterator

    from graphrag_llm.completion import LLMCompletion, register_completion
    from graphrag_llm.embedding import LLMEmbedding, register_embedding
    from graphrag_llm.types import (
        LLMCompletionChunk,
        LLMCompletionResponse,
        LLMEmbeddingResponse,
    )

The registry functions are register_completion(completion_type, completion_initializer, scope="transient") and register_embedding(completion_type, completion_initializer, scope="transient"). The custom type string in each ModelConfig must exactly match the registered key, and registration must happen before GraphRAG creates providers. Each initializer receives model_id, model_config, tokenizer, metrics_store, metrics_processor, rate_limiter, retrier, cache, and cache_key_creator, plus extra fields from ModelConfig.

LLMCompletion requires sync completion(**kwargs) and async completion_async(**kwargs) plus tokenizer and metrics_store properties. Messages accept either a plain string or a sequence of message objects/dicts. GraphRAG 3.2.0 uses these relevant paths:

- Index extraction and community-report generation use non-streaming calls; report generation passes a Pydantic class in response_format and consumes response.formatted_response.
- Global map calls pass response_format_json_object=True and parse .content themselves.
- Local final answers and Global reduce answers call completion_async(..., stream=True) and read chunk.choices[0].delta.content.

Thus a full Local/Global provider needs sync and async completions, async chunk streaming, non-streaming typed JSON validation, and JSON-object mode. Construct a response from the actual OpenAI-compatible result with LLMCompletionResponse(**response.model_dump(), formatted_response=typed_value); preserve its id, model, created time, choices, and usage. Construct chunks from each SDK stream item with LLMCompletionChunk(**chunk.model_dump()). For a typed call, validate JSON content locally with response_format.model_validate_json(content) and set that instance as formatted_response; reject streaming with a typed response_format. response_format_json_object is GraphRAG-specific: pop it before the SDK call, request JSON-object mode, and include the schema in the prompt for DeepSeek. [completion interface](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/completion/completion.py) [completion types](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/types/types.py) [Local stream](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/structured_search/local_search/search.py) [Global stream and map JSON](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/structured_search/global_search/search.py)

LLMEmbedding requires sync and async methods and the same two properties. It receives input: list[str] and returns LLMEmbeddingResponse, an OpenAI CreateEmbeddingResponse shape. Required payload fields are object="list", model, data=[{"object":"embedding", "index": i, "embedding": list[float]}], and usage={"prompt_tokens": ..., "total_tokens": ...}. The wrapper exposes .embeddings and .first_embedding as computed properties. Preserve input order and return one vector per input. [embedding interface](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/embedding/embedding.py) [embedding types](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/types/types.py) [OpenAI embedding schema](https://github.com/openai/openai-python/blob/v1.109.1/src/openai/types/create_embedding_response.py)

Provider factories pass metrics, retry, rate-limit, and cache components but do not automatically wrap custom methods in LiteLLM middleware. The ABC requires a metrics_store property; custom providers do not automatically call its update_metrics. ModelConfig.metrics defaults to a non-null config, so factories normally create a metrics store/processor; metrics=None yields NoopMetricsStore. Consume a GraphRAG metrics kwarg if present instead of forwarding it to the SDK. To collect metrics or apply retries, throttling, and caching, explicitly use the supplied components or wire with_middleware_pipeline as LiteLLM does. [completion factory](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/completion/completion_factory.py) [LiteLLM middleware wiring](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/completion/lite_llm_completion.py) [metrics config](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/config/metrics_config.py)

### Direct GraphRagConfig construction

GraphRagConfig can be constructed without a settings file. Supply model maps for the IDs referenced by report generation and search, an output table store, vector URI/dimension, the workflow list, and embedding names. An explicit configuration shape for the existing BYOG plan is:

    from graphrag.config.models.graph_rag_config import GraphRagConfig
    from graphrag_llm.config import ModelConfig
    from graphrag_storage import StorageConfig
    from graphrag_vectors import VectorStoreConfig

    config = GraphRagConfig(
        completion_models={
            "deepseek_json_mode": ModelConfig(
                type="deepseek_json_mode",
                model_provider="deepseek",
                model="deepseek-chat",
                api_base="https://api.deepseek.com",
                api_key=deepseek_key,  # source this outside code/config files
                metrics=None,
            ),
        },
        embedding_models={
            "bge_local": ModelConfig(
                type="bge_local",
                model_provider="local",
                model="BAAI/bge-small-zh-v1.5",
                local_model_path="<resolved model path>",  # custom extra field
                metrics=None,
            ),
        },
        output_storage=StorageConfig(type="file", base_dir="<output dir>"),
        vector_store=VectorStoreConfig(
            type="lancedb", db_uri="<output dir>/lancedb", vector_size=512
        ),
        workflows=[
            "create_communities",
            "create_community_reports",
            "generate_text_embeddings",
        ],
        embed_text={
            "embedding_model_id": "bge_local",
            "names": ["text_unit_text", "entity_description", "community_full_content"],
        },
        community_reports={"completion_model_id": "deepseek_json_mode"},
        global_search={"completion_model_id": "deepseek_json_mode"},
        local_search={
            "completion_model_id": "deepseek_json_mode",
            "embedding_model_id": "bge_local",
        },
    )

ModelConfig requires model_provider and model, allows extra fields, and passes custom extras such as local_model_path to the registered initializer. The custom type bypasses LiteLLM-specific credential validation, leaving endpoint/auth handling to that adapter. table_provider defaults to Parquet. input_storage, cache, reporting, prompts, and unrelated search configs have defaults, so the shown BYOG workflow does not need further settings unless those defaults are intentionally changed. [GraphRagConfig](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/config/models/graph_rag_config.py) [ModelConfig](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag-llm/graphrag_llm/config/model_config.py)

### Local and Global context tables

The public Local and Global search APIs return context_data as a mapping of table names to pandas DataFrames. These are the records selected for the prompt context, not a citation guarantee or an independent correctness judgment.

- Global normally returns reports when records are selected; the key may be absent when none are selected. The API-created context requests report content (not summary), rank, and occurrence weight. Base columns are id, title, any report attributes, content, rank; occurrence weight may be one of the dynamic attributes.
- Local may return reports, entities, relationships, sources, and covariate frames. With defaults and return_candidate_context=False, base columns are reports: id,title,[attributes],content; entities: id,entity,description,[attributes]; relationships: id,source,target,description,[attributes]; and sources: id,text,[attributes]. Default Local context omits entity rank and relationship weight. Keys can be missing or frames empty when no records match. If candidate context is enabled, candidate rows add in_context and may include records outside the prompt.

Consumer code should support dynamic attributes, missing keys, and empty frames. Global reduce_context_data is a separate map/reduce prompt representation; public api.global_search returns the original reports table as context. [Global context parameters](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/factory.py) [community frame builder](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/context_builder/community_context.py) [Local context builder](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/structured_search/local_search/mixed_context.py) [Local frame builders](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/context_builder/local_context.py) [source frame builder](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/context_builder/source_context.py)


## Prompt-fix feasibility for community reports and Global reduce

The reported omission is consistent with the v3.2.0 report-input boundary, not necessarily a lost edge in the full relationships table. The report workflow builds one context per community: it takes nodes assigned to that community level and filters edges to those whose source and target are both in that node set. It prepares entity node details (including descriptions) and selected intra-community edge details for the report input. The source groups edges by source and target with an aggregation of first, then joins those records onto nodes, so not every within-community edge is necessarily serialized. An edge crossing the selected community boundary is excluded from that report context (it may appear in a parent report if both endpoints belong to the parent set). The context builder also adds entity details through sorted edge endpoints and enforces max_input_length, so a prompt instruction cannot preserve a fact that was not included in that report input; for this sample, verify the recipe node and its complete description are present in the extractor input if omission persists after the prompt change. [community report context v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/index/operations/summarize_communities/graph_context/context_builder.py) [context ordering and truncation v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/index/operations/summarize_communities/graph_context/sort_context.py) [community report extractor v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/index/operations/summarize_communities/community_reports_extractor.py)

The proposed constraints are compatible with the existing grounding and response schema and do not require changing the clustering or query algorithms. Narrowly phrase the recipe rule as: when a recipe entity description explicitly lists ingredients or quantities, preserve every listed item and its stated quantity/unit somewhere in the report; do not add items from inference. State that each report describes a partial community subgraph, and missing entities/edges from that subgraph are not evidence that the facts are absent from the full dataset. State that a SKU's shelf/department category is a retail classification, not by itself an ingredient type or proof of a recipe role. These rules clarify what the current prompt leaves implicit while respecting its existing instruction to ground claims in supplied records.

There is an existing prompt-file path for both changes, not an inline prompt-prefix API. CommunityReportsConfig.graph_prompt is read as a filesystem path by resolved_prompts(); GraphRAG's init template points to prompts/community_report_graph.txt and graphrag init writes the default prompt there. Setting graph_prompt to raw prompt text will be treated as a path and fail. Copy or edit the generated/default file, retain the {input_text} and {max_report_length} format placeholders, and point community_reports.graph_prompt at that file. [community prompt config v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/config/models/community_reports_config.py) [init prompt paths v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/config/init_content.py) [init writes prompt files v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/cli/initialize.py)

Global reduce also has an existing full-prompt file setting. The configured global_search.reduce_prompt is loaded from disk and passed as reduce_system_prompt; if absent, GlobalSearch falls back to REDUCE_SYSTEM_PROMPT. The active reducer formats {report_data}, {response_type}, and {max_length}, then streams the final response. Preserve all three placeholders when editing the generated prompts/global_search_reduce_system_prompt.txt. Because a configured prompt replaces the built-in full prompt, copy the default and insert the new rule rather than writing only a short fragment. Its current default already says not to make up information and not to include claims without supporting evidence, but it does not distinguish a partial set of community reports from an exhaustive dataset. A useful extra reducer rule is: “The analyst reports are summaries of selected communities, not an exhaustive inventory. Omission of an ingredient, entity, or relationship from these reports does not establish its absence from the underlying data; state absence only when the reports provide explicit, exhaustive evidence.” The reducer only receives map key points, not the original graph/entity descriptions, so this can suppress unsupported dataset-wide negative claims but cannot restore the omitted egg fact. [Global prompt loading v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/api/query.py) [prompt file loader v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/utils/api.py) [reducer implementation v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/structured_search/global_search/search.py) [default reducer prompt v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/prompts/query/global_search_reduce_system_prompt.py)

The map prompt is also configurable by file and sees report batches; it has a similar generic “do not make anything up” rule. If the map stage itself turns an omitted report fact into a global absence statement, add the same non-exhaustiveness sentence to prompts/global_search_map_system_prompt.txt as well. The knowledge_prompt is not the right hook for the normal closed-world query path: the query factory constructs GlobalSearch with allow_general_knowledge=False, so the knowledge instruction is only appended when general-knowledge inclusion is enabled. [map prompt configuration v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/config/init_content.py) [GlobalSearch construction v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/factory.py)



Additional query-boundary note: Global reduce only runs when at least one map key point has a positive score. With no positive points and general-knowledge mode disabled, GraphRAG returns the canned NO_DATA_ANSWER without consulting the custom reduce prompt. The API factory sets allow_general_knowledge=False. This does not make a false absence claim, but it means the reduce prompt cannot recover a fact omitted from reports or alter the no-data branch; preserving recipe facts in the report input remains the effective fix for this sample. [reduce no-data branch v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/structured_search/global_search/search.py) [GlobalSearch factory defaults v3.2.0](https://raw.githubusercontent.com/microsoft/graphrag/v3.2.0/packages/graphrag/graphrag/query/factory.py)
