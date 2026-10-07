# 本地优化交接：RAG、GraphRAG、同次请求多条回复

本文交接本地优化分支，不是合并方案或兼容性验收。任务状态以 [优化 TASK](../tasks/ceres2-optimization.md) 为准，目前为**待验收**。本次交接仅新增本文；不改变产品实现，不执行 merge、rebase、cherry-pick 或 force push。

## 1. 仓库、范围与版本

| 项目 | 已知版本 |
| --- | --- |
| 交付仓库 | [2061623884/Ceres2](https://github.com/2061623884/Ceres2) |
| 本地交付分支 | `codex/ceres2-optimization-20261007` |
| 本地优化起点 | `b118dbea3852026c6a04c790b1e27df67c3c9c18` |
| 已提交的本地功能实现 | `142b6fbd1f5fe411d26d518255a583dc716315b5` |
| 与云端各分支的已核对共同祖先 | `4bed9c891261e382122d424825b649989ea92c92` |
| 本地工作树 | `/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007` |

最终交付还包含本文的独立文档提交，其完整 SHA 由推送后的远端分支核实并在交付回执报告，不把功能提交 SHA 当作文档提交 SHA。

用户授权目标：完整搭建政策/商品混合检索和 RRF、菜谱 GraphRAG、可可在同一次用户请求中的可选多条发言、统一现有 Grok Bot 界面、最小商品/购物车/订单/售后闭环，以及评测采集与失败回流。只适当补充代表性 demo 数据，不全量搬入旧菜谱或旧数据库。

Python 仍是业务事实、权限、确认与写入权威；售前用真实 Node/TypeScript Pi SDK，售后用真实 Python LangGraph。价格、库存、配送、结算和售后均为模拟业务。没有真实支付、退款到账、补送或履约，也没有新增活动提醒或跨回合自主消息调度。

## 2. 已实现能力与关键修改

| 能力 | 本地实现及主要文件 |
| --- | --- |
| 代表性数据 | 8 道菜、71 个 SKU/Offer、18 种食材、11 条模拟政策，覆盖八个政策域。只新增 `demo:shrimp-200g`；纠正鸡蛋分类及两款薯片不能满足鲜土豆采购的关联。`data/fixtures/`、[来源记录](../data/fixtures/knowledge-provenance.json)、[静态导入脚本](../work/ceres2-optimization/import_demo_knowledge.py)。 |
| 政策/商品 hybrid | SQLite FTS5 中文单字/二元字组与 ASCII BM25、真实本地 BGE 512 维、精确向量排序及 RRF（k=60）。两路候选与融合证据保留；相关性门槛来自开发集。`backend/app/knowledge/{bge,corpus,hybrid}.py`、`catalog_service.py`、`mercury/policy.py`。商品身份、价格和库存从当前 Catalog/Offer 重读，检索分数不决定资格或授权。 |
| 官方 GraphRAG | GraphRAG 3.2.0 BYOG：规范 Recipe/Ingredient/SKU 与关系输入，实际运行社区发现、LLM 报告、三个 embedding index；官方 Local/Global 查询。44 实体、61 关系、26 text units、11 社区/报告。`knowledge/{graph,providers,cli,worker}.py`、`services/knowledge_service.py`、`dish_service.py`。不是仅有 SQL 关系查询，也没有对已有结构化事实重新做 LLM 实体抽取。 |
| 同次请求多条回复 | 主 Pi 工具调用迭代可同时生成普通过程文本；独立同模型审校后持久化为独立消息并 SSE 发布。`runtime/pi/src/{worker,general-claim,prompt-modules}.ts`、`pi_product_runtime.py`、`pi_product_turn_service.py`、`frontend/src/{App.tsx,lib/saleGuide.ts}`。稳定 ID、停止/恢复/去重、过程在最终回复前显示。审校增加 provider 调用与时延，分别计量；不是零额外调用或固定多气泡。 |
| 原生完成与菜谱事实 | `finish_response` 在已登记 `guide_request` 后单独结束同一 Pi loop，Python 校验本轮引用并渲染结果；主请求 `tool_choice=auto`，不使用 JSON mode 约束过程正文。`recipe_facts` 显示基准人数/用量、调料未知数量和共用必需食材；指定食材的商品证据重读当前 Offer，不自动准备清单或加购。事实查询不再触发额外购前结果介绍。 |
| 最小购物/售后闭环 | 新 `ProductDetail.tsx`；模拟订单按版本从 submitted→shipped→delivered；质量/履约申请按明确问题包装数、可关联照片，明确确认后原子写申请/回执/人工工单；`HumanPhotos.tsx` 及人工视图读取。`checkout_service.py`、`mercury/{aftersales,aftersales_models,router,tools}.py`、`human/{router,service}.py` 和对应前端。订单商品/金额快照保留。 |
| 评测与数据回流 | 18 条检索开发查询、5 条待人工复核的失败登记、按明确 owner 导出运行/消息/检索/usage/版本、显式人工标注 JSONL、指定回归入口。`backend/app/evaluation/`、`evals/`。不从加购确认推导正向质量标签，不自动训练或改政策。 |

关键修复：BGE 首次并发初始化采用互斥；菜名/别名完全匹配先确定业务身份；单字“蛋”保留显式词面证据；事件时刻独立于业务 payload，保持 SSE 与缓存回执一致；旧开始时刻未知保持 null；已关闭人工工单排除后续责任代次的申请；重复 seed 只修两款薯片的食材关联，不重置可变 Offer。

Graph 查询以规范原始事实呈现关系、分类和用量，保留模型选择结果单独评分。图路径不证明配料、营养、过敏安全、跨食材替代或家庭已有数量；人数/包装/预算/确认仍由业务服务处理。

## 3. 接口与数据结构

### HTTP、SSE 和内部工具

| 入口 | 合同或变化 |
| --- | --- |
| `GET /api/v1/products?q=...` | 原路径不变，有 q 时走 hybrid；返回当前 Catalog/Offer，并可带 `retrieval`（source/ranks/scores/rrf_score/corpus_revision）。品类/审核范围仍有效；无 q 沿普通列表查询。 |
| `GET /api/v1/products/{sku_id}` | 沿用已有详情 API，新前端详情页实际调用并可直接加购；不是新增商品写入接口。 |
| `POST /api/v1/orders/{order_id}/demo-state` | 本地新增。请求 `{expected_version, status}`，status 仅 shipped/delivered，须按顺序、当前 owner/版本推进模拟状态。 |
| `POST /api/v1/guide/sessions/{session_id}/turns/stream`；`GET .../runs/{run_id}/stream` | 原流与恢复入口新增 `message.interim`，payload 为 `{message_id, content}`。事件 envelope 顶层带 `recorded_at_ms`/`elapsed_ms`，不混入业务 payload；历史未知时间保持 null。 |
| `POST /api/v1/mercury/sessions/{session_id}/proposals` | `kind` 扩展为 refund/return/quality/fulfillment；问题申请需 `item_id`、明确 `problem_quantity`、`selection_version`、reason，可带最多 3 个 `photo_ids`。金额来自订单快照，是模拟预计金额。 |
| `POST /api/v1/mercury/sessions/{session_id}/photos` | 本地新增。`content_type` 为 JPEG/PNG/WebP，`data_base64`、`selection_version`；单张最多 4 MiB。owner/case/order/选单版本作用域校验；照片不自动证明质量。 |
| `GET /api/v1/mercury/sessions/{session_id}/photos/{photo_id}` | 本地新增，用户读取当前所属照片。 |
| `GET /api/v1/mercury/operator/tickets/{ticket_id}/photos/{photo_id}` | 本地新增，独立 `X-Internal-Token` 与工单/订单/owner 范围检查。 |
| `POST .../confirm`、`GET .../aftersales`、人工工单视图 | 沿用路径与确认/幂等合同。质量/履约提案和回执包含问题数量/照片；申请、回执、转人工同事务。人工视图增加 photos/applications，排除关闭后后续代次申请。 |
| Pi `search_after_sales_policy(query, category?)` | 10 个类别：price/stock/delivery/order/refund/fulfillment/quality/return/safety/human。本地返回 `{ok, data, retrieval}` 并建立本轮 `policy_ref`；不做云端预取或请求内结果复用。 |
| Pi `search_recipe_relations(query)` | 新增，走真实 GraphRAG Local，返回本轮菜谱 refs 与规范事实/关系；不是购买授权。 |
| Pi `finish_response(...)` | 新增 Node 内部结束工具，无 Python 业务写权。参数沿原最终引用 DTO；可用 `recipe_facts`＋本轮 `dish_refs`＋可选 `ingredient_ids`。该内部类型投影为 HTTP 业务事实结果，不是新增外部自由文本出口。 |
| Node→Python JSONL | 新增 `interim_message` 帧（message_id/text/approved）；Python 发布公开 `message.interim`。私有 reasoning、原始 token、工具参数不进入过程气泡。保留既有受控最终 JSON/显式 interim 对象的测试合同，非法正文不猜测修复。 |
| `python -m app.knowledge.cli` | build-hybrid/hybrid/build-graph/graph/serve。是本地构建/查询与 JSONL worker 入口，没有新增公开 RAG HTTP 服务。 |

### 持久化与版本

- `GuideMessage.kind='interim'`：本轮稳定消息身份 `${run_id}:interim:n`；历史事务只提交输入/过程消息和事件，不提前提交购物或记忆业务。
- `guide_run_events.recorded_at_ms: FLOAT NULL`：新增列，`elapsed_ms` 从已知 receipt.started_at 推导；未知历史不补造时间。`GuideRunEvent` 仍以 run_id/sequence 标识事件。
- 新表 `aftersales_photos`：photo_id、owner_id、case_id、order_id、selection_version、content_type、content（LargeBinary）。问题数量与 photo_ids 写在既有 proposal.preview_json/receipt.result_json 中，未给 application 表虚构新的数量/照片列；kind 增加值仍使用既有字符串列。
- 检索库：`data/indexes/hybrid.sqlite3` 保存 documents/FTS/真实 vectors/manifest；`data/indexes/graphrag/` 保存官方 Parquet/Lance/报告/manifest。语料与实现文件 hash、模型 revision、维度及查询版本保留。价格、库存不嵌入知识文档作可变事实源。
- 数据来源 `optimization-demo-v2`；政策 `2026-10-07-demo-v1`；tokenizer `zh-unigrams-bigrams-ascii-v2`；相关性 `retrieval-dev-v2-literal-or-dense`；图 `ceres-recipe-byog-v3`；图查询 `canonical-scope-overview-v3`；provider `ceres-graphrag-provider-v1`。
- 导出 `ceres-eval-capture-v1`；显式标签 `ceres-run-annotation-v1`。export_source_snapshot 是**导出时**源码 hash，不冒充运行时版本；运行/index 版本只取实际已存事件，缺失 usage/版本/费用保持未知。

## 4. 与云端重合及已发现的合同差异

2026-10-07 通过 `git ls-remote` 读取以下远端 tips，再仅 fetch/read 固定提交；没有改变当前实现。四者与本地起点的共同祖先均核对为 `4bed9c891261e382122d424825b649989ea92c92`。

| 云端分支 | 此次观察的完整 SHA |
| --- | --- |
| `ceres2/judge-prefetch-rebuild-20261007` | `37c98400e7152b89e4a58f02fff3bceaa73b0eac` |
| `ceres2/judge-prefetch-policy-wip-20261007` | `b4ab956a2c4ddf823c4d9f354436ae9fbf8ddd38` |
| `ceres2/judge-prefetch-reuse-wip-20261007` | `d8ac3ab627cf56560b13be6e2a7e436865bd02c5` |
| `ceres2/judge-prefetch-role-entry-wip-20261007` | `f323d15751c141e0ded4763a3881bbda6355eae3` |

比对范围：四个固定提交的变更文件清单；对 rebuild `37c984...` 进一步阅读 navigation/Kev、政策、Pi Python/Node、prompt modules、Thinking helpers 与其 `docs/JUDGE-PREFETCH-HANDOFF.md`。其他 WIP 仅作来源定位，不继承其状态或测试。**仅做静态比对，未组合运行、未测合并后代码，不能宣称兼容。** 远端后续变化须重新固定 SHA。

| 主题 | 本地与云端的关系 | 需要交接的具体边界 |
| --- | --- | --- |
| 角色判断 | 本地保留起点的联合角色/能力判断，未实现云端 Coco-only yes/no/uncertain 新入口。 | 云端改 `kev_provider.py`、`navigation_service.py`、公开 `schemas/navigation.py`，新 route 为 ready/switch、capability=null、entry_judgment。本地 `chatNavigation.ts` 仍接收 clarify/unavailable/navigation 等旧状态，真实 Firefox 用 unavailable→手动角色续接。不能把本地浏览器通过当云端新入口通过。 |
| 政策预取 | 政策问答能力重合，但本地新增的是 hybrid 知识源；云端新增的是 Kev 判断后、Pi 开始前预取。 | 云端 `prepare_policy`、policy_scope、start.policyEvidence 及 success/empty/error/coverage 合同在本地未接入。双方均改 `mercury/policy.py`、`pi_product_runtime.py`、`pi_product_turn_service.py`、experience.json、worker.ts。云端 `_query_policy` 导入 POLICY_SOURCE_VERSION/NAME；本地版本/来源来自 fixture，未保留这两个导出。直接混接文件有已确认的静态导入合同缺口，未执行组合验证。 |
| 检索复用 | 本地常驻 worker/encoder 复用与云端请求内政策结果复用层次不同；本地未实现云端范围/来源版本的结果缓存。 | 云端以相同 query/category/source_version/policy_scope 复用，并保留多范围 refs、失败尝试和计数。本地每次工具查询建立新 policy_ref，只支持原单 policy_ref 完成字段，finish_response schema 没有云端 policy_refs。云端源版本 2026-10-06 与本地 demo-v1 不同，不能沿用缓存身份；SKU 当前 Offer 重读也须保留。 |
| Thinking 关闭 | **本地继承起点 b118 的已有能力，不是本轮 RAG 新增。** 云端也独立实现了官方 hostname 下的关闭。 | 两侧均仅对 api.deepseek.com 加 thinking disabled，但 Python helper 为 urlparse/urlsplit 差异，Node helper 注释不同，调用路径也被各自改动。云端 worker 对官方主请求仍加 JSON mode；本地为原生 interim/finish_response 移除主 JSON mode 并设 auto。不能只保留 Thinking 字段而覆盖本地主循环，或把两侧 wire 测试视为同合同。新 GraphRAG provider 是本地新增调用路径，另行关闭 Thinking 并独立校验结构化响应。 |
| Pi 上下文与完成 | 同一 Pi/Python 接缝有实质重合。 | 云端按 guide_request kind 缩小上下文；本地仍沿起点 capability/shoppingContext 选择工具，并新增 finish_response、recipe_facts、interim 审校/发布。PiProductRuntime 本地需要 publish_interim，云端需要 policy_scope；构造器、start envelope、工具清单、最终引用和停止栅栏要一起比对。 |
| 计量/评测 | 双方有 runtime 观测，但不是同一统计口径。 | 云端 policy_judgment/policy_lookup/policy_reuse/runtime_summary 与本地 model_usage/retrieval/graph_retrieval、interim 时间字段不同。本地导出只明确提取其已知事件类型；不会自动完整计入云端判断/缓存指标。provider 调用、Pi turn、审校、预取与复用应分别记账，不能直接拼成绩。 |

**相对本地起点的新增**：真实 BGE/BM25/RRF、官方 GraphRAG、8 菜/71 SKU/18 食材/11 政策定义、knowledge worker、过程气泡与时刻、原生完成/菜谱事实、商品详情和模拟订单推进、问题数量/照片/人工视图、评测导出/标注/失败登记。四个已观察云端分支的对应生产变更清单中未出现本地 `backend/app/knowledge/`、`backend/app/evaluation/` 或这些前端/数据扩展；这仅陈述固定版本范围，不断言未来不会重合。

本交接没有为潜在冲突修改实现，也没有选定替换哪条线路。后续比对须同时保留 Python 权威、明确确认、当前 Offer、run/session/task/owner 栅栏、停止/恢复及复用来源范围，再对组合后的固定源码补相应验证；云端和本地各自通过不能替代该验证。

## 5. 实际测试及适用版本

全部执行由专职 Tester 完成；以下均是本地证据，不继承云端成绩。测试发生时 Git HEAD 为起点 b118，带本轮未提交源码，后来整理为功能提交 `142b6fbd1f5fe411d26d518255a583dc716315b5`。**不能把 b118 的裸源码称为 441 项通过的版本。** 本次文档提交不改被测产品源码，未重复全套产品测试。

| 层次 | 实际结果与版本 | 证据 |
| --- | --- | --- |
| 最终 backend 完整回归 | `current-prompt-v2`，`../.venv/bin/python -m pytest tests -q`（cwd backend）：441/441，exit 0，819.24s。66 个适用变更文件集合 SHA256 `4e87c6b746f70f3dd4ce3fa6066e143775e2df9274b5e584cd317b7193195525`。 | [运行记录](../work/ceres2-optimization/testing/backend-full-regression-current-prompt-v2-2026-10-07.json)、[文件清单](../work/ceres2-optimization/testing/backend-full-regression-source-manifest-current-prompt-v2-2026-10-07.json)。运行中仅 eval 失败登记元数据四例→五例；精确重建原 66 文件集合并核实 hash，方法在 [最终报告](../work/ceres2-optimization/testing/final-technical-gates-current-prompt-v2-2026-10-07.md)。 |
| 受控消息/Thinking | thinking transport＋native 6＋controlled 4，共 16 passed。Thinking/native 在完整套内有重叠，不加成 457 个独立测试。 | 同上最终报告；`backend/tests/test_official_deepseek_thinking.py`、`test_pi_interim_native.py`、任务 testing 的 controlled 文件。 |
| 类型检查/构建 | 当前 runtime `npm run typecheck`/`npm run build`；当前前端 `npx tsc --noEmit`/`npm run build` 均 exit 0。Vite 既有配置加载 warning 保留。 | [最终报告](../work/ceres2-optimization/testing/final-technical-gates-current-prompt-v2-2026-10-07.md)。当前编译 worker/prompt/前端资产 hash 另见 Firefox v6。 |
| 实际 hybrid | v4 literal-or-dense，真实固定 BGE，两路＋RRF；18 开发例中 13/13 正例目标 Top3、5/5 未收录负例无 hits；单字“蛋”召回 4 菜。门槛在此集调过，非独立评分。 | [开发采样](../work/ceres2-optimization/testing/retrieval-dev-run-v4-literal-or-dense-2026-10-07.json)、[hits](../work/ceres2-optimization/testing/relevance-hits-smoke-v4-literal-or-dense-2026-10-07.json)。 |
| 实际 GraphRAG | 图 v3/查询 canonical-scope-overview-v3 完成建库、官方 Local/Global 查询及未知负例。Global 模型仅选 2/4 鸡蛋菜，宿主规范关系视图呈现 4/4；这是来源保护，不是模型准确率提高。 | [构建](../work/ceres2-optimization/testing/graph-build-smoke-v3-2026-10-07.json)、[artifact](../work/ceres2-optimization/testing/graph-artifact-audit-v3-2026-10-07.json)、[Global](../work/ceres2-optimization/testing/graph-global-overview-v3-smoke-2026-10-07.json)。各有语料/实现/模型/索引版本。 |
| 真实模型审校 | deepseek-flash/api.deepseek.com，当前 compiled INTERIM prompt，13/13 预期判断相符；此前 8/9 的菜谱事实漏拦保留。是同模型开发语义 smoke。 | [v2](../work/ceres2-optimization/testing/interim-claim-semantic-audit-v2-2026-10-07.json)。 |
| 当前真实 Firefox/Pi | recipe-facts-visible-v6：真实当前 worker，interim seq3 在完成 seq17 前，整条过程气泡在 viewport 可见，最终事实可见，无事实查询 result-introduction。手动角色回退；SSE 代理帧间暂停用于 DOM 观察。 | [v6](../work/ceres2-optimization/testing/browser-interim-smoke-recipe-facts-visible-v6-2026-10-07.json)。不代表自动路由或无干预时延。 |
| 模拟业务/真实浏览器 | 商品详情→加购→模拟结算→同订单配送/签收→质量数量/照片→确认→人工看图通过。另有当前 Offer 重读、照片作用域、重放、真实 LangGraph 数量澄清、重复 seed 与标签 join 检查。 | [旅程](../work/ceres2-optimization/testing/browser-demo-journey-2026-10-07.json)、[HTTP](../work/ceres2-optimization/testing/catalog-hybrid-http-smoke-2026-10-07.json)、[数量/照片/状态](../work/ceres2-optimization/testing/demo-quality-photos-state-smoke-2026-10-07.json)、[标签技术检查](../work/ceres2-optimization/testing/annotation-contract-smoke-current-2026-10-07.json)。各为报告所记版本；前期旅程不冒充最终 prompt 的多气泡验证。 |
| 独立源码审查 | Standards/Spec 没有剩余确认偏离；一项审校构造重复的非阻断观察保留。审查者未执行测试。 | [两轴报告](../work/ceres2-optimization/review/combined.md)、[提交前源码 snapshot](../work/ceres2-optimization/review/review-snapshot.json)。 |

真实商品/政策与双菜事实 v4 采样使用生产 worker/provider，但有安全 Python 事件观测 wrapper；当前 v6 浏览器无该 wrapper/preload。v4 早于最后审校收紧，不能把不同提示的候选统计直接合并为最终成功率。完整分层证据见 [测试索引](../work/ceres2-optimization/testing/test-evidence-index-2026-10-07.md)。

## 6. 未完成、失败与剩余限制

- 未执行本地＋云端组合验证，也未验证云端新角色 schema、政策预取/复用与本地 RAG/interim 的组合。没有合并兼容结论。
- 用户本人验收、独立自然性盲评、Dots 的独立产品评分和 5 条失败登记的人工签核仍开放；18 检索开发例与 13 审校例不能冒充独立测试集。
- Global 自由摘要曾矛盾、模型选择漏 2 道菜；现依靠规范来源视图保护，仍须分开评估模型选择和宿主呈现。
- 早期 Pi JSON 握手/去 JSON mode/required 实验有空正文、非法最终内容或失败；改为 auto＋原生完成后有成功样本，过程条数仍可为零。每条候选还有审校费用/时延。
- 历史浏览器无终态/超时与商品空引用失败保留，尚未根治或说明全部原因。当前 v6 成功不删除这些失败；其路由使用手动续接，自动角色判断未获真实通过。
- 酸奶未收录是合法商品负例，其一般退货政策可以返回，但不能确认不存在 SKU 的具体订单资格。
- 后端历史 175/2→31 复测、431/3→45 复测、440/1（旧 JSON mode 测试断言）以及审校 8/9 均有保留；最终对应修复版 441/441、审校 13/13，不累加不同版本计数。
- 没有重验真实长期自动记忆/Dream、跨回合提醒、真实资金或履约；本地本轮不扩大这些范围。没有单独 lint script 通过结论。

## 7. 迁移、配置与接手要求

1. 在准确交付分支的隔离 worktree 安装依赖，不复用原项目/archive/reference 的 `.venv`、node_modules、SQLite、session、cart、order、checkpoint、索引或凭据。保留原工作树有效改动。
2. Python 3.11：业务 `.venv` 同步 `backend/requirements.lock`；知识 `.venv-graphrag` 同步 `backend/knowledge-requirements.lock`（GraphRAG 3.2.0、Transformers 5.19.0、Torch 2.14.1+cpu）。Node 22.19.0 / npm 10.9.3 是本次已用环境，Pi SDK 1.0.3；按 runtime 与 frontend 各自 package-lock 独立安装并生成 dist。知识 worker 硬编码使用仓库根 `.venv-graphrag/bin/python`，不能只沿云端 `backend/.venv` 的布局启动。安装/构建/测试交专职 Tester。
3. BGE `BAAI/bge-small-zh-v1.5` 固定 revision `7999e1d3359715c523056ef9478215996d62a620`，本地 `.cache/huggingface` 权重；normalized CLS/512/max512，两端不加 instruction。首次下载及真实权重证据见 [预检](../work/ceres2-optimization/testing/preflight-2026-10-07.md)；实际检索编码合同以当前 `bge.py` 为准，不把预检当最终检索效果。
4. 用当前静态 fixture 重复 seed 初始化 Catalog/Offer；已有 Offer 不重置。两款已知薯片的 ingredient_ids 会同步修正。菜谱/食材参考 Ceres `e24debf670db02a86cb79c40933b901827db8a55` 的静态定义，来源已记录，不读取旧运行库。API `init_db()` 调用 `initialize_schema()`：创建新增照片表，并加 `guide_run_events.recorded_at_ms FLOAT NULL`，迁移标记 `optimization_run_event_time_v1`；旧事件时间不回填。先备份需保留的本项目数据，不对 archive/reference 运行迁移。
5. 本地生成 hybrid 与 GraphRAG 索引；业务服务不会自动建库或下载模型。默认路径 `data/indexes/hybrid.sqlite3` 与 `data/indexes/graphrag/`，重建时停止本地服务。建库有 workflow error 则失败，不写完成 manifest。
6. 配置由本地 `.env` 或进程环境提供：`DATABASE_URL`、`MERCURY_CHECKPOINT_PATH` 指向本 worktree；`BUSINESS_DATA_MODE=demo`；`LLM_MODE` 与批准的 `OPENAI_BASE_URL`/`OPENAI_API_KEY`/`LLM_MODEL`；`KEV_BASE_URL` 仍按本地旧导航合同；`HUMAN_OPERATOR_TOKEN` 是独立人工凭据，不能等于 provider key。没有新增 RAG provider 配置开关；本次实际采样为 deepseek-flash/api.deepseek.com，不授权换模型或继承云端真实效果。
7. 后台记忆仍沿现有 `MEMORY_EXTRACTION_MODEL`/`MEMORY_DREAM_MODEL`；部分隔离 live smoke 关闭这两个模型以避免额外后台调用，该配置不是整套记忆的真实通过。启动 backend 会启动现有 MemoryWorker，接手者需核对隔离数据库/任务和批准的模型配置。

已实现 CLI 的示例（本文没有执行）：

```bash
cd backend
../.venv/bin/python -m app.services.seed_service
../.venv-graphrag/bin/python -m app.knowledge.cli build-hybrid
../.venv-graphrag/bin/python -m app.knowledge.cli build-graph
../.venv-graphrag/bin/python -m app.knowledge.cli graph --method local --query '番茄炒蛋需要哪些食材与商品'
../.venv/bin/python -m app.evaluation.export_runs --owner-id '<明确owner_id>' --output ../data/generated/evals/captured.jsonl
```

首次获取依赖/权重需要网络；build-graph、graph 查询和正常 live 对话使用真实聊天 provider。完整启动/配置/本人验收入口见 [本地运行指南](OPTIMIZATION-20261007.md) 与 [README](../README.md)。完整 lock 同步在新机器上的重新安装若未实际执行，不能称已在该机器验证。

## 8. Git 范围与本地保留文件

功能提交保留代码、静态数据定义、来源、构建/导入脚本、锁版本、开发评测与去敏 QA JSON/Markdown；交接提交仅新增本文。凭据、数据库、索引、模型、依赖与原始运行资料不上传。本次交接开始时 tracked/untracked 普通改动清单为空；最终提交后再次按 Git status 核实，并在交付回执列出任何剩余普通文件。

以下是此次实际观察到的 Git 忽略项清单（目录按组列出，目录内文件不逐项展开）：

| 本地保留路径 | 不提交原因 |
| --- | --- |
| `.venv/`、`.venv-graphrag/`、`frontend/node_modules/`、`runtime/pi/node_modules/` | 本机依赖环境，按锁文件重新安装。 |
| `.cache/` | BGE 权重和下载缓存，按固定 revision 获取。 |
| `data/runtime/` | 模拟业务 SQLite/checkpoint/session/cart/order 状态，不能当迁移数据上传。 |
| `data/indexes/` | hybrid SQLite、GraphRAG Parquet/Lance/生成报告与 worker 日志，本地可重复构建。 |
| `data/generated/` | 原始 owner 运行导出与人工标注资料，需保留本地作用域和审核。 |
| `frontend/dist/`、`runtime/pi/dist/` | 构建产物，按对应源码重新构建；适用资产 hash 保留在去敏报告。 |
| `.pytest_cache/`、`backend/.pytest_cache/`、各 `__pycache__/` | 测试/解释器缓存。 |
| `work/ceres2-optimization/testing/tmp/` | 原始 SSE、浏览器图片、临时 DB/index、候选文本和冻结源副本等临时证据，不能整体上传。 |
| `work/ceres2-optimization/testing/{backend-full-regression-2026-10-07,backend-full-regression-current-prompt-v2-2026-10-07,backend-regression-post-build,backend-regression}.log` | 完整原始日志留在本地；可提交 JSON 记录/摘要/hash 与复跑入口。 |

报告中链接到忽略的 `.log`、`tmp/`、截图或模型文件，只在本机可用，远端 checkout 不含这些内容；接手端按脚本重新生成，不能把链接存在当作远端已拥有原始证据。本 worktree 没有提交 `.env`，其他工作树的本地配置不属于本交付。

### 原主工作树的未提交保护快照

原主工作树 `/data/amax/Documents/projects/Agent/Agent产品/Ceres2`（main）另有 53 项普通未提交文件：修改 7、删除 13、未跟踪 33。这是交接时的只读 Git status 快照，未读取独立 holdout 内容，未改变、暂存或提交这些文件。它们不属于本交付分支的干净状态。

未纳入原因：`.agents/skills/` 和 `skills-lock.json` 是原工作树的技能配置变化，本次未核定其归属；`work/live-validation/` 与 `work/next-experience/live-acceptance/` 是另一验收线路的脚本、冻结、导出及独立评测资料，本次未核验其版本/发布范围，也没有把独立 holdout 当开发集。保留原地，不能由本次发布顺带提交或整体上传。

```text
 M .agents/skills/ask-matt/SKILL.md
 M .agents/skills/code-review/SKILL.md
 M .agents/skills/implement-spec/SKILL.md
 M .agents/skills/implement/SKILL.md
 M .agents/skills/retro/SKILL.md
 D .agents/skills/setup-matt-pocock-skills/SKILL.md
 D .agents/skills/setup-matt-pocock-skills/agents/openai.yaml
 D .agents/skills/setup-matt-pocock-skills/domain.md
 D .agents/skills/setup-matt-pocock-skills/issue-tracker-github.md
 D .agents/skills/setup-matt-pocock-skills/issue-tracker-gitlab.md
 D .agents/skills/setup-matt-pocock-skills/issue-tracker-local.md
 D .agents/skills/setup-matt-pocock-skills/triage-labels.md
 M .agents/skills/to-spec/SKILL.md
 M .agents/skills/to-tickets/SKILL.md
 D .agents/skills/triage/AGENT-BRIEF.md
 D .agents/skills/triage/OUT-OF-SCOPE.md
 D .agents/skills/triage/SKILL.md
 D .agents/skills/triage/agents/openai.yaml
 D .agents/skills/wayfinder/SKILL.md
 D .agents/skills/wayfinder/agents/openai.yaml
?? .agents/skills/chief-of-staff/SKILL.md
?? .agents/skills/chief-of-staff/agents/openai.yaml
?? .agents/skills/claude-handoff/SKILL.md
?? .agents/skills/claude-handoff/agents/openai.yaml
?? .agents/skills/grill-me/SKILL.md
?? .agents/skills/grill-me/agents/openai.yaml
?? .agents/skills/grilling/SKILL.md
?? .agents/skills/grilling/agents/openai.yaml
?? .agents/skills/handoff/SKILL.md
?? .agents/skills/handoff/agents/openai.yaml
?? .agents/skills/loop-me/SKILL.md
?? .agents/skills/loop-me/agents/openai.yaml
?? skills-lock.json
?? work/live-validation/run_live_batch_deepseek_once.py
?? work/next-experience/live-acceptance/README.md
?? work/next-experience/live-acceptance/baseline-provenance.md
?? work/next-experience/live-acceptance/cursor-handoff-snapshot.json
?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007.tar.gz
?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007/MANIFEST.md
?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007/acceptance/desensitized-regression-20261007.json
?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007/freeze/thinking-disable-source-freeze.json
?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007/patch/4bed9c8-to-worktree.patch
?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007/tests/test_official_deepseek_thinking.py
?? work/next-experience/live-acceptance/holdout/SHA256SUMS
?? work/next-experience/live-acceptance/holdout/cases.json
?? work/next-experience/live-acceptance/holdout/language-rubric.md
?? work/next-experience/live-acceptance/observers/memory_watch.py
?? work/next-experience/live-acceptance/observers/node_usage.mjs
?? work/next-experience/live-acceptance/observers/provider_usage.py
?? work/next-experience/live-acceptance/primary-path-language-review.md
?? work/next-experience/live-acceptance/spec-live-fix-review.md
?? work/next-experience/live-acceptance/standards-live-fix-review.md
?? work/next-experience/live-acceptance/thinking-disable-source-freeze.json
```
