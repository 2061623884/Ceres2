# Recipe / Product 关系检索与 Microsoft GraphRAG 取舍

调查日期：2026-10-07。只读核对当前 Ceres2 代码与本地 reference 资料，未运行检索、GraphRAG 或性能实验。Microsoft 官方文档使用当前 main 页面；截至调查日 GitHub Releases 页面最新列为 v3.2.0。论文来源为 2024-04-24 的 arXiv 预印本，版本和数据范围均与本次小型目录不同。

## 结论

- 商品既定 sparse + dense hybrid + RRF 保持；政策仍走各自的 hybrid RAG。Recipe→Ingredient→SKU 是结构化关系查询的补充，不是把商品检索改成全 GraphRAG。[当前优化规格](/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007/docs/plans/ceres2-optimization-spec.md)
- 当前 Ceres2 已有确定性的“选菜谱 → 查食材 ID → 找 SKU”路径和宿主数量计算。更有意义的新增场景是反向问“已有这些食材能做什么／哪些菜还缺什么”，以及扩展当前仅有的菜谱覆盖，而不是让 Graph 数据库重算已有 2 跳查询。[dish_service.py](/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007/backend/app/services/dish_service.py:11) [数量与包装计算](/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007/backend/app/services/dish_service.py:27)
- 对当前 70 SKU，小范围内用 Python/现有关系存储即可验证收益；若需要逐边来源、审核和扩展维护，再评估显式关系表。独立图数据库和完整 Microsoft GraphRAG 都需要分别证明它们解决了 SQL 关系查询无法承担的产品问题及运维负担。

## Microsoft GraphRAG 的官方语义

GraphRAG 不是“只有 community summary”。官方查询概览列出 Local、Global、DRIFT、Basic 等方法：Local 结合 AI 抽取的知识图谱与原始文本块，查询实体、邻接实体、关系、协变量和关联 text units；Global 对指定层级的 community reports 做 map-reduce，官方明确称它资源消耗较高，适合整体主题问题；DRIFT 把 community 信息用于 local query 起点，并以生成的 follow-up questions 深挖；Basic 是 top-k text-unit 向量检索。[Query Overview](https://microsoft.github.io/graphrag/query/overview/)、[Local Search](https://github.com/microsoft/graphrag/blob/main/docs/query/local_search.md)、[Global Search](https://microsoft.github.io/graphrag/query/global_search/)、[DRIFT Search](https://microsoft.github.io/graphrag/query/drift_search/)

GraphRAG 官方使用 structured_search 作为部分查询实现的代码命名空间；官方面向使用者的查询方法列表仍是 Local、Global、DRIFT、Basic，没有单独称为“Structured Search”的第五个 query mode。[Global Search 官方示例的导入路径](https://microsoft.github.io/graphrag/examples_notebooks/global_search/)

官方 BYOG（Bring Your Own Graph）允许用现有图谱输入 entities 与 relationships 表；GraphRAG 输出默认是 Parquet。Global 的最小 graph-summary 工作流可只用社区与报告；Local、DRIFT、Basic 还需要 text_units 和 embeddings。也就是说，可把已审定的图关系供给 GraphRAG，不必由模型从头抽取，更不要求 Neo4j。[BYOG](https://github.com/microsoft/graphrag/blob/main/docs/index/byog.md) [Outputs](https://microsoft.github.io/graphrag/index/outputs/)

CSV、JSON 和 Parquet 可作为 GraphRAG structured input，但每个输入行会进入统一 documents DataFrame；结构化行保留在 raw_data，可在 chunking 时 prepend 字段。结合 BYOG 要求 entities/relationships 表的说明，可以推断“把 JSON 行交给 GraphRAG”本身不等于自动得到有类型、可审计的 RecipeIngredient 或 SkuIngredient 业务边；需要显式映射/构图。实际实现前应按所 pin 的版本核对。[Inputs](https://microsoft.github.io/graphrag/index/inputs/) [BYOG](https://github.com/microsoft/graphrag/blob/main/docs/index/byog.md)

原始 GraphRAG 论文针对大约百万 token 规模的 corpus-level query-focused summarization，报告的是该任务与数据上的结果；不能外推为 70 SKU 的精确候选召回优势。[From Local to Global (arXiv:2404.16130)](https://arxiv.org/abs/2404.16130)。版本参考：[Microsoft GraphRAG v3.2.0 release](https://github.com/microsoft/graphrag/releases/tag/v3.2.0)。文档 main 可变，若以后要实测，应先固定代码、prompt、索引流程和 embedding 版本。

## Ceres2 与 reference 的资料现状

当前 worktree 的 products.json 为 v1、70 个 SKU，记录均标为 demo / approved；59 个 SKU 有 ingredient_ids，合计 46 个不同 ingredient ID。recipes.json 为 v1、只有 2 道菜，required/pantry 合计涉及 7 个不同 ingredient ID；静态匹配显示这 7 个 ID 在当前 SKU 中都有映射。以上只是 fixture 静态盘点，不是质量验收或召回实验。[products.json](/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007/data/fixtures/products.json) [recipes.json](/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007/data/fixtures/recipes.json)

当前实现以 JSON 中的 recipe required/pantry ingredient_id 和 SKU ingredient_ids 做精确 ID 匹配；DishService 搜索菜名/别名，候选阶段遍历已审核商品并按 ingredient ID 匹配。人数缩放、单位是否兼容、按销售包装向上取整均由 Python 确定逻辑完成，不由 LLM/图查询推算。[dish_service.py](/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007/backend/app/services/dish_service.py:19) [CatalogProduct](/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007/backend/app/models/catalog.py:7) [CatalogService 与 Offer](/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007/backend/app/services/catalog_service.py:17)

这些 fixture 适合关系检索原型，但 edge provenance 较弱：SKU 行只有 source=demo、review_status=approved 和 ingredient_ids，没有逐条 ingredient 映射的证据、审核人或 revision；recipe 行也没有来源引用。ingredient_ids 的语义也不能未经校准解释为“含有”或“可互相替代”。若关系成为业务召回依据，应先定义边含义及来源/版本/审核状态；未审定的相似词、别名不能自动变成替代品。

本地只读历史 reference 是 origin Ceres 固定提交 e24debf670db02a86cb79c40933b901827db8a55：含 65 个 demo SKU、102 项 ingredient catalog、105 道菜谱，另有 2 条 catalog-review quarantine 记录。可用于研究关系覆盖与数据 QA，但不是 Ceres2 当前数据或历史验收结果，不能直接混入 70 SKU 基线。[reference manifest](/home/amax/Documents/projects/Agent/Agent产品/reference/README.md:68) [historical ingredient catalog](/home/amax/Documents/projects/Agent/Agent产品/reference/origins/Ceres/data/fixtures/ingredient-catalog.json) [historical demo products](/home/amax/Documents/projects/Agent/Agent产品/reference/origins/Ceres/data/fixtures/demo-products.json) [historical recipes](/home/amax/Documents/projects/Agent/Agent产品/reference/origins/Ceres/data/fixtures/chinese-dishes-v1.json) [quarantine review](/home/amax/Documents/projects/Agent/Agent产品/reference/origins/Ceres/data/fixtures/catalog-review.json)

旧 reference 中的 retrieval_index-langgraph 当前指针只包含 audit_only manifest，记录的 handoff projection hash 不匹配；当前指向的 manifest 记载 105 道菜、308 SKU、0 个新嵌入和 0 个复用向量，索引目录只看到 manifest。它不是可用的 GraphRAG knowledge-graph index，也不能作当前 hybrid 检索结果的基线。[old index pointer](/home/amax/Documents/projects/Agent/Agent产品/reference/origins/Ceres/data/retrieval_index-langgraph/current.json) [audit manifest](/home/amax/Documents/projects/Agent/Agent产品/reference/origins/Ceres/data/retrieval_index-langgraph/idx-22ffeee222e95b2e/manifest.json)

## 方案的收益与代价

| 方案 | 能解决什么 | 对本 70 SKU / 当前菜谱集的判断 | 主要代价 |
|---|---|---|---|
| 现有字段 + Python 确定性映射 | Recipe↔Ingredient↔SKU 的 1–2 跳精确连接；当前用例已有 recipe→ingredient→SKU 路径。可增加 ingredient→recipe 反查、缺项列表。 | 最小且已有真实调用方。当前 2 道菜、7 个食材 ID、每 ID 1–2 个候选，没有理由为查询性能加图数据库。 | JSON 数组边不便逐边审核、来源追踪和查询审计；用例扩大后需维护数据规范。 |
| 同一业务 DB 的显式关系表 | 为 recipe ingredient、SKU 映射、别名和可选 substitution 加稳定 edge ID、source/ref/revision/review_status；用 SQL join 做多跳查询。 | 如果接下来要人工审核映射、反向查询或评测来源质量，是优先考虑的最小结构化升级。它改变数据覆盖/审计能力，不天然提高同一批边的 recall。 | schema、导入、迁移、去重、edge QA；若没有多个当前调用方或边级治理需求，暂不需要预先抽象。 |
| 独立图数据库 | 图结构动态、多跳路径类型丰富，且需要图遍历/图算法或多业务复用时，可提供图原生查询。 | Recipe→Ingredient→SKU 只有两跳且 70 SKU，SQL join 足够；Neo4j/FalkorDB 等不是前置要求。 | 新服务部署、权限、备份、监控、双写/同步、跨存储一致性和数据权威分叉。是否值得要以运维与查询收益实测。 |
| 完整 Microsoft GraphRAG | 从大量非结构化文本抽取实体关系；Local 结合图邻居与原文，Global 汇总 corpus 级主题，DRIFT 做带 follow-up 的 local/global 探索。 | 未来有大量菜谱叙述、商品说明、用户研究，且要回答跨文本组合/主题问题时可做独立 Local/DRIFT 研究。当前 2 道菜的结构化字段不提供明显社区/全局摘要价值；不要拿 Global 替换商品 hybrid。 | 图抽取/报告生成/向量索引和 prompt 调优，重新索引与模型调用成本；从非结构化文本抽取的关系仍需 provenance 与人工校验。 |

独立图数据库和显式 SQL 表解决的是存储/查询组织问题；GraphRAG 解决的是从文档形成图语义并用 Local/Global/DRIFT 等方法构建检索上下文。三者不是同一个选型维度。上述“运维代价与小库不匹配”是根据当前 schema/规模作出的架构推断，不是 GraphRAG 官方基准结论。

## 最小对照实验建议

1. **先冻结来源与任务面。** 首轮用当前 Ceres2 fixture v1 的 70 SKU / 2 recipes；建 gold 时逐条审核 recipe→ingredient 与 ingredient→SKU 边。只用现有事实判定结果，不能把 embedding 相似、商品名近似或模型解释反过来当 gold。若用 reference 的 105 recipes 扩大覆盖，另建一个明确标为 historical 的实验集，保留 origin commit 和 JSON SHA，不混成当前基线。
2. **拆开“数据增益”和“检索方法增益”。** A：当前菜名/别名查询与确定性食材→SKU 映射。B：同一 fixture、同一 gold，加确定性 ingredient→recipe/SKU 反向关系候选通道。商品 sparse+dense hybrid+RRF 是既定但尚未实现的主线；实现并冻结后，再作为新的候选基线与关系通道组合比较，不能把它当作当前已运行基线。C（可选研究臂）：同一数据文本化后跑 Microsoft GraphRAG Local；只有另有 corpus-wide 主题问题才评 Global，DRIFT 作为探索性比较。再用完全相同的 edge set 对比 SQL join 和 graph DB，检验执行、变更和维护成本；同数据同语义关系的查询不应预设图查询 recall 更高。
3. **用小而分层的查询集，不声称统计代表性。** 可先手工标注约 20–30 条：菜名及别名、用户口语食材反查菜谱、recipe 缺项、SKU 语义问法、无映射/无货/单位不兼容、要求替代但无经审核替代边。记录每路候选及身份、rank、source edge/version，比较 Recall@k、MRR/nDCG、relation edge precision/coverage、错误替代率、拒答/缺项是否正确；记录 index build、模型调用/tokens、端到端 p50/p95，但运行前不填性能结论。
4. **把安全与确定性条件作为硬约束。** alias、同一食材映射、可替代是不同关系；替代必须有明确边类型、适用条件和来源审核。价格、库存、可售性从当前 Catalog/Offer 权威服务重读，绝不由知识图谱或 RAG 索引提供。检索只返回 SKU/reference 候选，不授权加购。人数缩放、单位换算、销售包装数量继续走 Python 确定逻辑；未知或不兼容规格不能由 LLM/graph path 猜算。

验收先回答两件不同的事：现有数据是否需要补来源/边级审查；补齐后关系召回是否比现有商品 hybrid 带来有用的候选。只有关系规模、动态多跳查询或多调用方维护证据支持时，才单独立项证明图数据库收益；只有存在更大、来源清楚的非结构化语料与 corpus-level 问题时，再评估完整 GraphRAG。
