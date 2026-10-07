# Ceres2 混合检索最小方案

调研日期：2026-10-07。目标是给 Ceres2 当前优化 worktree 提供可以实现、可评测的最小设计；不是已实现能力或效果报告。Ceres 代码基线为 `b118dbea3852026c6a04c790b1e27df67c3c9c18`。RAGFlow、MaxKB、Dify 仅作为相邻仓库的只读版本化参考，不导入代码、运行时依赖、索引或数据。

## 事实边界

- 当前 Ceres 的政策检索是对静态 4 条规则做关键词子串计分并返回最多 3 条；商品检索是 Python `CatalogService` 对名称、中文名和品牌做 SQL `ILIKE`。`backend/requirements.lock` 有 `sqlite-vec==0.1.9`，但业务源码没有 FTS5、`vec0`、BM25、embedding 或 RRF 调用。因此“锁了 sqlite-vec”不等于当前已有向量检索。[policy.py:3-29](../../../backend/app/mercury/policy.py) · [catalog_service.py:45-61](../../../backend/app/services/catalog_service.py) · [requirements.lock:48](../../../backend/requirements.lock:48)
- 项目约定 Python 是售后 LangGraph、确定性业务和写入的唯一权威；Pi/TypeScript 应通过现有业务入口取数/调用，不另建一份可写事实。[AGENTS.md:5-9](../../../AGENTS.md)
- 本轮讨论确认的范围是商品与政策混合检索，补齐 8 个政策域及批准办理场景。当前政策语料是版本 `2026-10-06` 的 4 条静态规则，尚未覆盖目标范围；商品候选需沿用当前 Catalog 查询语义：按服务的 `store_id` 关联 Offer，仅包含 `review_status='approved'` 商品，品类等明确业务条件继续适用。自然语言 query 在混合检索中是召回输入，不能再统一用原 SQL ILIKE 当作两路的硬过滤，否则会阻断同义表达的 dense 召回。检索只能提供候选证据，不能授予退货资格或执行订单写入。现有退货判断仅基于签收、7 天和 `returnable`；生鲜质量问题没有区别处理分支，需把讨论稿规则补进确定性政策与流程。[policy.py:3-29](../../../backend/app/mercury/policy.py) · [catalog_service.py:34-61](../../../backend/app/services/catalog_service.py) · [aftersales.py:60-92](../../../backend/app/mercury/aftersales.py) · [orders.py:15-43](../../../backend/app/mercury/orders.py)

## 可行动结论

1. **在 Python/SQLite 边界内实现两路检索，先不引入完整 RAG 平台或外部向量库。** 建一个由 Python 维护的轻量派生索引：FTS5 保存已分词文本；SQLite 行保存 source ID、文本与真实向量；语料版本、embedding 模型/tokenizer 标识、维度及重建信息放入索引 manifest。当前规模约 70 个 SKU、8 个政策域，第一版可以逐行计算归一化向量点积作 dense 排序，不必先引入 ANN 索引；这是简化实现建议，不是已测性能结论。虽然锁文件已有 sqlite-vec 0.1.9，但无业务调用；该上游将其标为 pre-v1，首版采用 SQLite/纯 Python 排序可少一项扩展生命周期依赖，后续是否换 `sqlite-vec` 应由目标环境验证决定。[sqlite-vec v0.1.9 README](https://github.com/asg017/sqlite-vec/tree/v0.1.9) · [项目检索边界](../../../../reference/RAG-GUIDE.md:45-47)

2. **中文 sparse 使用相同的 Jieba 预分词，双方以空格分隔后交给 FTS5。** 对商品名、别名、品牌、品类及政策术语维护小型业务词表；SKU ID 保留为可精确命中的字段/词项。FTS5 默认 `unicode61` 把连续 token 字符视为一个 token，不做中文词边界切分；trigram 虽可做子串搜索，但小于 3 个 Unicode 字符的全文查询不匹配，不宜单独承担中文商品/政策检索。Jieba 词表与 query/document 分词版本应一起记录。MaxKB 的冻结快照也采用 Jieba 分词并把知识库术语加入用户词表，可作为模式参考而非 Ceres 依赖。[SQLite FTS5 tokenizer 文档](https://www.sqlite.org/fts5.html#tokenizers) · [Jieba 上游](https://github.com/fxsjy/jieba) · [MaxKB `ts_vecto_util.py`（commit `2c7c8c9f`）](../../../../reference/rag/maxkb/apps/common/utils/ts_vecto_util.py:85-111)

3. **Dense 必须由固定的真实中文 embedding 模型生成，不写假向量或关键词伪装语义检索。** 本轮已采纳本地中文 embedding；本报告的技术候选推荐为 `BAAI/bge-small-zh-v1.5`，具体型号不是用户指定值。模型卡给出中文模型、512 维，并提供 query 与 passage 编码示例；建议按卡片短 query 检索指令编码 query，passage 不加指令，归一化后用点积排序。固定模型仓库 revision、tokenizer、指令、维度和归一化方式，并写入索引 manifest。当前 backend lock 没有 `transformers`、`torch`、`sentence-transformers` 或 Jieba；采用本地模型需要新增并锁定 Python 推理依赖及下载/缓存模型权重。代码和权重当前都未验证；本报告不推断云端可用内存、延迟或吞吐。上游模型卡给出的 C-MTEB 是通用基准，不代表 Ceres 质量。[BAAI 模型卡](https://huggingface.co/BAAI/bge-small-zh-v1.5) · [模型卡对短 query 指令、维度与归一化示例](https://huggingface.co/BAAI/bge-small-zh-v1.5#usage-for-embedding-model) · [backend requirements](../../../backend/requirements.lock)

4. **稀疏、稠密各自独立取候选，再按稳定 source ID 去重并做 RRF。** 首轮建议两路各取前 20，按 `RRF(d) = Σ 1/(60 + rank(d))` 融合；k=60 是原论文 pilot 中使用的固定值，只作为可复现实验起点，不是 Ceres 最优参数。政策最后保留现有最多 3 条的接口上限；商品候选由调用方现有展示/选择约束裁剪。不要把 BM25 与 cosine 原始分数直接相加，也不要在融合前拿一个分支的分数阈值过滤另一个分支的候选。参考实现并不等价：冻结 MaxKB SQL 只从 dense top `top_k*10` 候选内把 cosine 距离和 `ts_rank_cd` 原始相加，可能使只被词法召回的文档进不了融合；Dify 将不同召回分支去重后交给 weighted-score 或 reranker；RAGFlow 的 Infinity 代码委托 `table.Fusion(method, ...)`，ES 代码明确解析 `weighted_sum`，这些代码不能证明 Ceres 已有 RRF。[RRF 论文（SIGIR 2009）](https://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf) · [MaxKB `blend_search.sql`（commit `2c7c8c9f`）](../../../../reference/rag/maxkb/apps/knowledge/sql/blend_search.sql:1-27) · [Dify `retrieval_service.py`（commit `e7d9c889`）](../../../../reference/rag/dify/api/core/rag/datasource/retrieval_service.py:894-928) · [RAGFlow Infinity（commit `cc72ecb0`）](../../../../reference/rag/ragflow/internal/engine/infinity/chunk.go:1190-1211) · [RAGFlow ES（同 commit）](../../../../reference/rag/ragflow/internal/engine/elasticsearch/chunk.go:1202-1234)

5. **沿用当前政策与商品语料边界，并在回答或操作前重读 canonical facts。** 商品检索先按 `CatalogService` 当前路径保留 `store_id` 对应 Offer、`review_status='approved'`、用户明确的 `q/category_id` 条件；政策检索使用当前 `2026-10-06` 版本规则及调用方明确传入的 category 条件。不要引入未定义的 page 作用域或新的来源状态字段。候选只返回 source ID 与检索 rank/score；Python 在回答前重读当前政策正文/版本，商品重读当前 Catalog/Offer，订单/购物车/资格由现有业务服务实时读取，来源版本或内容 hash 不一致时不得继续使用旧候选文本。价格、库存、订单状态与用户确认都不是 embedding 索引事实。MaxKB 快照在向量查询前按 knowledge、active、文档范围过滤，只能作为上游检索模式参考，不代表 Ceres 具有这些领域字段；来源/embedding 版本优先记入索引 manifest。[MaxKB `pg_vector.py`（commit `2c7c8c9f`）](../../../../reference/rag/maxkb/apps/knowledge/vector/pg_vector.py:112-193) · [Ceres policy source/version](../../../backend/app/mercury/policy.py:3-29) · [Ceres catalog scope](../../../backend/app/services/catalog_service.py:34-61) · [RAG-GUIDE 的证据边界](../../../../reference/RAG-GUIDE.md:45-47)

## 最小评测与数据闭环

给每条 query 标注预期 source ID/政策域、是否应无命中、引用版本，以及预期资格/操作结果。样本覆盖：精确 SKU/品牌词、中文同义表达、8 个政策域和每个批准办理场景、不同 `store_id`、`review_status`、用户明确的品类/预算等事实约束、语义 query 的不同表达、规则未知及质量问题。先对同一快照比较 sparse-only、dense-only、hybrid+RRF；检索用 Recall@5、MRR@5，业务用 source/version 命中、政策解释与资格/写入正确率。每轮报告同时记录代码 SHA、索引 manifest、embedding/tokenizer 版本和 eval 集版本。未得到专职 Tester 的实际运行和用户验收前，不宣称召回率、延迟、质量提升或已验收。失败样本经人工标注后再进入下一版 eval 集/词表/政策修订；禁止把线上用户文本未经授权直接并入训练或检索源。

## 引用快照与限制

`../reference/manifest.json`（2026-10-07）固定了本地 RAG 平台快照：RAGFlow `cc72ecb0af18ade5d58f84d107af7cd59a88c39f`、MaxKB `2c7c8c9f2097f48c2bf3fee6bbb2a6f422bbbe43`、Dify `e7d9c8897a4ddf104396e4efc8c321e0f8075bac`。[manifest](../../../../reference/manifest.json:445-499) 明确 RAG-GUIDE 是架构参考，不是 Ceres 当前实现证明。本轮仅做只读代码/文档调查；未运行测试、安装、构建、模型调用或性能测量。
