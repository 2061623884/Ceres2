# Ceres2：检索、GraphRAG 与同次请求多条回复

状态：待验收。技术门槛已通过；用户本人验收与独立自然性评分仍开放。

负责人：本优化主会话；本 worktree 的共享 fixture、索引合同、入口适配由本会话统一维护。专职 Tester 执行安装及测试；Standards 与 Spec 分别只读审查。dots 云端负责评测方法/用例/评分，与本地的采集和实现合同对齐，不维护本任务的竞争状态。

## 当前授权与版本

- 2026-10-07 用户已确认独立 worktree，暂不合并。
- 已确认政策/商品混合检索＋RRF、同一次 Pi 请求内可选多条助手发言、统一现有 Grok Bot UI、最小商品/订单/售后闭环和数据评测。
- 用户随后批准参考 Ceres1 静态数据与代码，自行补充 demo 量级菜谱/商品、完整搭建 RAG，方案与 smoke 门槛通过后进入完整 GraphRAG；最新补充明确只需适当补齐代表性数据，不全量搬入原 105 道菜谱或旧索引。
- 数据库/生成索引不需要 Git 跟踪；提交范围保留数据定义、可重复导入与构建脚本、来源/版本、评测与去敏证据。凭据和旧运行状态不导入。
- 源码基线：`b118dbea3852026c6a04c790b1e27df67c3c9c18`；工作树 `Ceres2-optimization-20261007`；分支 `codex/ceres2-optimization-20261007`。

规格：[优化规格](../docs/plans/ceres2-optimization-spec.md)；讨论来源：[访谈](../docs/plans/ceres2-optimization-interview.md)。历史 TASK05—07 与 TASK10 只作相关合同/缺陷依据，其通过不继承给本任务。

## 本轮执行顺序

1. 参考 Ceres1 的可重复导入、候选/来源及 RRF 组织，选取少量有代表性的菜谱；仅补所需 SKU/模拟 Offer，保留现有事实和页面。冻结数据内容与来源。
2. 实现真实本地 embedding、中文稀疏召回、RRF 和菜谱关系证据；通过数据导入/构建及公开查询 smoke。
3. 使用真实 GraphRAG 实现索引及查询闭环，验证文档/文本块、实体/关系、社区/报告和真实向量等所选流程产物；不得把仅有 SQL 关系查询或 mock 输出称为完整 GraphRAG。
4. Pi/墨墨接入权威检索证据；落地同次请求中途消息和统一 UI，业务仅补完整测试所需闭环。
5. 对受影响范围执行完整必要测试，固定同候选做检索对照、真实模型/页面证据和最终两轴审查；用户本人验收另记。

## 可观察验收

- 数据生成可重复，关系与用量有来源/版本；正常、缺项、单位/数量、约束及未知关系的代表性场景可运行。
- 政策与商品实际分别有 sparse/dense 候选和 RRF 证据；所有向量来自真实模型。
- GraphRAG 能从当前小型语料构建所需索引并完成有出处的查询；关系证据仍映射到真实菜谱/食材/SKU，价格库存读取权威业务数据。
- 同次请求处理未结束时出现可选真实助手发言；工具进度、最终结果及停止/恢复语义保持清楚。
- 商品/购物车/结算/同订单售后所需闭环可操作，UI 统一；无真实资金或履约承诺。
- 安装、smoke、回归、真实采样、浏览器和本人验收分层记证据；未通过项不得写“已验收”。

## 当前状态与下一步

已完成设计访谈、代码审计、官方来源核验与 8 菜 / 71 SKU / 18 食材静态定义，补 11 条覆盖八域的模拟政策。独立 backend / GraphRAG 环境安装及依赖检查通过；固定 revision 的真实 CPU BGE 512 维编码 smoke 通过。

真实 hybrid 构建、18 例三路采样及正负相关性门槛验证完成；固定开发集 13/13 正例目标 Top3、5/5 未收录负例无 hits，不是独立验收或泛化效果结论。官方 GraphRAG v3 已构建 44 实体、61 关系、26 文本块、11 社区/报告与 3 个 512 维 Lance 索引；全部实体覆盖社区。并发 BGE 初始化失败已真实复现、修复并重测。

自由 Global 摘要曾反复把原始已知分类说成未知；失败样本及源码/数据版本保留。`canonical-scope-overview-v3` 已通过真实 Global smoke：11 份检索社区报告映射 44 个规范实体，鸡蛋关联的 4 道菜与基准用量完整呈现；Local 番茄/鸡蛋用量与未知查询亦通过。Global 模型自身只选出 2/4 鸡蛋菜，完整关系由宿主基于检索社区原始事实呈现；不能把接缝保护当作模型品质改善。

Pi→审校→独立历史事务→message.interim→UI 已实现。旧 JSON 正文握手、去 JSON mode 和 required 工具选择的真实失败均保留；当前采用真实 native tools、auto 与单独 `finish_response` 完成工具。生产版三条固定查询均完成并出现一条通过审校的过程消息；新只读 `recipe_facts` 采样已显示原始用量、共用鸡蛋与当前商品事实，不生成方案或加购。原 4 个受控消息测试与新增 6 个 native/菜谱事实测试各自已有通过证据，最新过程审校与 UI 顺序修订正在同版复测。过程语境提示区分核对对象与结果，普通聊天审校保持原合同；事实查询不额外触发购前介绍。

商品详情、模拟订单状态推进、问题包装数质量/履约申请、照片和人工查看已实现。当前商品 HTTP smoke 验证真实 hybrid 与当前 Offer 重读，质量/照片/订单 smoke 验证实际持久申请、人工工单、作用域和重放；质量/履约数量澄清 2 项真实 LangGraph interrupt→续答→提案→确认回执用例通过。真实 Firefox 已走通商品详情→加购→模拟结算→配送/签收→质量数量与照片→确认→人工看图。Unicode 非法 Base64 返回 422，重复 seed 修正两款薯片采购映射而不重置 Offer，导出与显式标注技术 smoke 已通过。

后端首轮适用回归 175 通过、2 失败，修复后相关 31 项通过。随后完整 `backend/tests` 执行 431 通过、3 失败；计时混入回执、旧开始时刻未知、关闭工单混入后续申请已修复，受影响 45 项复测通过，包括原三项失败。计时独立存储并在 SSE 顶层呈现，未知历史时间不补写。检索最新 18 例开发采样通过，单字“蛋”完整召回 4 菜；最新前端/runtime typecheck 与 build、native/controlled 10 项通过。

v4 完整后端回归为 440 通过、1 失败：旧 thinking-profile 传输测试仍要求主循环 JSON mode，已按实际原生工具/auto 决策改为验证无 JSON mode、auto 和真实 tools，保留 thinking/max-token/审校/表达断言。真实过程审校 v1 的 9 例完成、8 例符合预期；一条具体菜谱鸡蛋数量被误放行，已明确过程语境下所有正向菜谱食材/用量/共用关系都属于待核验任务事实，普通聊天审校不变。

最终冻结源码 `current-prompt-v2` 的完整 `backend/tests` 已由专职 Tester 执行：441/441 通过，exit 0，819.24 秒；66 个适用变更文件的集合 SHA-256 为 `4e87c6b746f70f3dd4ce3fa6066e143775e2df9274b5e584cd317b7193195525`。文件清单与冻结副本的重建方法见[同版 manifest](../work/ceres2-optimization/testing/backend-full-regression-source-manifest-current-prompt-v2-2026-10-07.json)，集合哈希已精确重现；运行期间仅评测失败登记元数据从四例扩展五例，未改变生产代码或测试。同版 runtime typecheck/build、thinking/native/controlled 16 项通过；过程审校 v2 的原 9 例与额外 4 个变体共 13/13 判断符合预期，仍属于开发语义 smoke，不是盲评准确率。前端源码未再修改，其 typecheck/build 和当前 UI 构建版本证据保留。旧失败、分母、源码/Prompt 版本与原始日志均未覆盖。

Firefox 的 v4 样本已复验顺序修正：过程消息在最终结果前、每个稳定 ID 只增加一条气泡。截图曾早于滚动完成，不能单凭 DOM 数量称可见；随后 `recipe-facts-visible-v5` 检查了过程气泡与聊天 viewport 的真实交集、透明度和截图，完成前整条过程文字可见，滚动稳定后最终菜谱事实可见。最终当前审校提示的 v6 再次通过：interim seq3 在终态 seq17 前，过程气泡透明度 1、视口内完整可见，最终基准用量/鸡蛋 Offer 可见，且只读查询没有额外结果介绍请求。手动角色回退被实际使用，不能称自动路由通过。代理只在完整 SSE 帧之间短暂停顿，不修改内容，不能据此宣称无干预浏览器时延。历史浏览器无终态采样与实际商品引用为空的品质失败继续保留，不把之后一次成功当作已根治。

Standards 与 Spec 独立源码审查已完成，修复后的源码没有剩余确认偏离，保留 1 项非阻断审校构造重复观察。评测导出、显式标注与失败晋升/回归合同已建立；5 条真实技术失败回流记录保持人工待复核，云端 Dots 独立评分与盲评未冒充完成。

下一步：用户按[验收入口](../docs/OPTIMIZATION-20261007.md#本人验收入口)试用本分支；以当前候选、数据、索引、模型和 Prompt 版本对齐 Dots 独立评测，给出真实人工标注。本人验收与自然性评分完成前不写已验收，不合并。检索门槛泛化、Global 模型漏选及历史浏览器超时需要持续作为评测项，不因本轮技术通过而删除。
环境证据：[preflight](../work/ceres2-optimization/testing/preflight-2026-10-07.md)；完整流程合同：[GraphRAG](../work/ceres2-optimization/research/graphrag-implementation-contract.md)。

证据入口：[测试证据索引](../work/ceres2-optimization/testing/test-evidence-index-2026-10-07.md)；独立审查：[Standards](../work/ceres2-optimization/review/standards.md)与[Spec](../work/ceres2-optimization/review/spec.md)；研究目录：`work/ceres2-optimization/research/`。后续执行进度仅在本 TASK 维护。
