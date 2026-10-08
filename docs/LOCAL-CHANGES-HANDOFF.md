# 本地测试与评测交接

当前任务入口：[TASK](../tasks/ceres2-local-followup.md)，行为方案：[规格](plans/ceres2-local-followup-spec.md)，工具步骤：[评测使用说明](LOCAL-FOLLOWUP-EVALUATION.md)。本文件不代替任务状态或本人验收。

## 分支与来源

- 仓库：[2061623884/Ceres2](https://github.com/2061623884/Ceres2)。
- 本地分支：`codex/ceres2-local-followup-20261008`；工作树：`/data/amax/Documents/projects/Agent/Agent产品/Ceres2-integration-20261008`。
- 已知起点：`170fac0bc75fcc855897b073337ba218abeb5b7d`，tree `295499ee22cc30485d38eba82e96330a39d7d573`。
- 最终评测工具代码：`739f13ead0c53ce9d82519efc30f51263e29ab45`；初候选为`e855d691d0a446c9e5385196134b55f2ec609320`，第一轮修复为`4e021e46e8c16671ae1366ec09c11f39bad01bd6`。最终29项/15.73s证据对应739的实际源码；后继本地交付提交只补文档/独立复审和离线报告，不改变该源码。
- 参考评测：[Ceres1 72bb1b99bf040c8b0bae5d026888bc059bc9423d](ceres1-evaluation-reference.md)；借方法与公开样本组织，不继承其成绩、runtime 或旧状态。
- 原本地优化 `6734c7fe79e670df2dae12b065dcc49c0b10a307` 保留快照；后续在本工作树，原main与其他工作树保留。
- 本轮按最新用户要求不合并；用户本轮AGENTS另禁止推送或修改原项目。本轮仅协调本地提交，没有发布新远端分支；交付完整SHA以本地分支和最终回报为准。

## 本地目标与已实现能力

本轮将测试与评测变成可重复执行的工具：40条公开场景、独立Tester维护的20条新验收、固定任务计划、公共HTTP/SSE采集、确定性事实评分、人工标注、失败回归归档和版本对照。产品优化按实际失败证据安排，订单后端以维持模拟闭环为范围。

新增 `backend/app/evaluation/` 中六个CLI和一个共享capture读取模块：

| 入口 | 实际能力与边界 |
| --- | --- |
| `run_baseline` | 每次新owner/canonical session，公开角色判定/run/SSE/receipt；逐题故障继续；核心重复、pilot执行上限、checkpoint/resume；明确续问/确认/幂等重放 |
| `score_batch` | 当前Offer和金额、预声明硬条件、逐步授权、重复副作用；合法报价等待、未执行与缺证据保留unknown；绑定batch原字节SHA |
| `annotate_batch` | 人工v2标签绑定精确owner/run；覆盖多run及末轮alias，不凭completed推质量 |
| `failure_intake` | 只收公开regression中人工明确fail的实际run；保留期望/原因/严重度/来源，排除acceptance，不自动训练 |
| `compare_runs` | 按execution/trial对照，legacy单次按case；保留null capture、缺项与全run标签，输入不同时明示 |
| `report_batch` | 完整计划分母、业务/category/core结果、client时延、人工run标签及usage覆盖；原batch与score必须精确绑定，未知费用保持null |

公开集为 `ceres2-local-followup-dev-2026-10-08-v2`，SHA-256 `032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d`：39单轮和1个明确确认/重放闭环，20核心三次加20常规一次为80公开计划。另20条新验收加入后才为100；[验收清单](../work/local-followup/04/ACCEPTANCE-MANIFEST.md)保留版本/hash、分离局限及离线更正证据，不含题正文。

## 接口与数据结构

没有新增业务HTTP接口或数据库表。执行器使用现有 `/api/v1/bootstrap`、Guide session/run/stream/turn receipt/messages、navigation opening/routes、cart、orders、products及Guide plan confirm。确认只执行用例预声明动作，未支持的setup/step明确失败，不假称整案完成。

输入为 `ceres-local-followup-dev-cases-v1`；采集为 `ceres-local-followup-batch-v1`，包含case_set hash、plan的case_id/trial/execution_id、outcome、每步before/after、当前catalog_facts与实际capture-v2。capture=null表示没有run；多轮只采该request的消息。人工标签保持 `ceres-run-annotation-v2`。score绑定原batch_sha256，report/对照保留输入与源hash；旧未带新绑定字段的实验报告不能冒充当前报告。

时延采用client monotonic，从每次run POST开始，不含前置角色判断；首interim、首answer.delta、stream完成分别记录。多轮顶层指首轮，steps分别计时，不重复计样本。服务端recorded_at另留；时延不自动等于人工认定的首个有用结果。

## 已执行验证及版本

| 验证 | 实际结果 | 版本与证据 |
| --- | --- | --- |
| 本机产品backend完整回归 | 原始 **752 passed /4 failed**，不改称全绿 | 精确170fac0 tracked freeze；[完整报告](../work/local-followup/01/product-baseline-170-full.md) |
| 上述4项环境补验 | 嵌套隔离缺pytest改用业务环境1通过；BGE缓存补齐后该文件4通过（含3个原失败） | 同产品源码；不与原计数相加；完整报告列每个失败、补验日志/source/model/index hash |
| 新评测工具 | 最终金额delta后同一命令 **29通过/15.73s**；21 eval、7 runner、1 app smoke为其组成，不能再相加 | [最终共同冻结](../work/local-followup/01/tool-combined-final-delta.md)；739源码、213文件manifest `8d3724cba223fb46bc46eb198aaf3a378c2096e1e930b4648fda6f5ee1b6aa1a` 前后未变；原26项属于e855、前次29项属于4e021，均保留历史版本 |
| CLI→真实API受控集成 | 1通过，真实TCP FastAPI/Pi，模型为loopback fixture | [smoke](../work/local-followup/01/app-controlled-http-smoke.md)；不启动生产lifespan/Memory，不称真实provider |
| Pi/前端类型与构建 | 全部退出0，warning保留 | [Node/build](../work/local-followup/01/node-builds-final.md)；Node22.19与本树独立锁/依赖 |
| 官方GraphRAG | 5通过，官方库构建/local/global/wire | [组件](../work/local-followup/03/graph-official-library.md)；受控provider与deterministic encoder，非真实图LLM质量 |
| 真实BGE | 4通过，含18公开检索校准、冷/热15秒预算 | [BGE](../work/local-followup/03/real-bge.md)、[指标v2](../work/local-followup/03/retrieval-dev-metrics-v2.md)；BM25/dense/RRF、macro/micro分别列出 |
| 浏览器 | 先前本机170fac0 Firefox HTTPS run11通过 | [原本机报告](../work/local-cloud-integration/local-acceptance-20261008/LOCAL-ACCEPTANCE-RESULTS.md)；受控provider/检索，当前未新增浏览器执行 |
| 100任务计划 | planned100/attempted0/not_run100，业务unknown100 | [独立清单](../work/local-followup/04/ACCEPTANCE-MANIFEST.md)；仅离线计划/重评分，没有HTTP或模型调用 |

历史云端746/5、183及Ceres1成绩不进入本表计数。RED、修复前失败、首轮GREEN失败和评分夹具版本变更均保留 `work/local-followup/01/02/`。检索指标v1和v2来自同一原始18条结果，增加macro说明只是离线更正，不新增检索执行。

e855候选的[Standards](../work/local-followup/05/STANDARDS-REVIEW.md)未发现硬违规，提出重复校验/步骤分派两项判断性smell；[Spec](../work/local-followup/05/SPEC-REVIEW.md)指出指标缺失与不可比较值中断。单一修复owner补Guide终态、critical观察分母、逐轮15秒和核心业务/时延组合稳定性，首useful明确未知；不可比较TypeError保留原因后继续，未知operator配置错误仍传播。另补plan选中行合计与确认后cart单价/行额/总额核对；缺Offer仍能核对已知行额，缺金额不填零。四个实际caller共享标注校验；执行/判分分派保持独立，防止评分以执行器自身为期望。三个新增CLI负例与受影响整组均通过，修前报告未覆盖新source，delta复审另留证。

4e021的[Spec delta](../work/local-followup/05/SPEC-DELTA-REVIEW.md)另发现两个金额诊断漏项，739已修复：已知行额不依赖数量/单价是否齐全而参与合计；成功receipt商品不符仍独立核对cart金额。两个实际RED、中间RED、窄GREEN及最终共同29项均保留，见[修复依据](../work/local-followup/05/REVIEW-RESOLUTION.md)。缺数量/单价的合计相符仍保持unknown，不把局部可核对证据当完整通过。

739的[Standards最终](../work/local-followup/05/STANDARDS-FINAL-REVIEW.md)未发现硬违规或新增smell；[Spec最终](../work/local-followup/05/SPEC-FINAL-REVIEW.md)确认已发现代码问题修复，未发现此次差异仍有代码缺陷，仍明确整体规格未完成。独立Tester对原100未运行批次做最终v4离线复核，仍是unknown100/实际执行0；不同评分版本保留，不把重复离线处理计作模型执行。

## 未完成、失败与限制

真实主模型/Kev、真实GraphRAG构建与回答、Memory extraction/Dream、完整多轮售后评测及本人接受仍未完成。本工作树独立配置缺主provider URL/key/model、Kev、Memory/Dream模型及人工operator token；不复制原项目凭据，不从模板猜模型。生产15秒/5轮合同保留，没有提高预算或更换模型宣称改进。

完整回归4个原环境失败虽然已补验，原始全量仍是752/4；最初全量shell完整调用串未单独保存，报告如实列出该溯源缺口，不补造命令。没有当前真实模型质量/成本改善结论。新验收与公开集共享部分上位类型，Tester可见公开集，不能称严格盲测/泛化。工具支持小型采购多轮，未支持完整订单/售后/Memory setup driver；现有受控生命周期测试与这些真实评测缺口分开。

## 配置、数据与迁移

本轮没有业务schema迁移。原静态fixtures为73商品/73Offer、8菜谱、11政策；当前新业务库和索引按本工作树可重复seed/build，数据库/会话/订单/checkpoint不从旧库导入。业务库、索引、固定BGE缓存、独立venv/node_modules、`.env`及原始日志留Git外；tracked evidence保留内容hash和命令/版本入口。

[交付检查](../work/local-followup/05/FINAL-DELIVERY-CHECK.md)复核213文件源码与最终测试manifest一致，并对本树`.env`只核对字段是否非空：`OPENAI_BASE_URL`、`OPENAI_API_KEY`、`LLM_MODEL`、`MEMORY_EXTRACTION_MODEL`、`MEMORY_DREAM_MODEL`、`KEV_BASE_URL`、`HUMAN_OPERATOR_TOKEN`均未配置；不记录值、不挪用原配置。它是配置缺项和交付差异证据，不是实际模型测试。

真实采样在可信本机独立`.env`配置就绪后，由Tester先核对获准模型/provider及有限调用范围，执行20核心pilot检查判分，再在同source/data/index/model条件续跑剩余计划。GraphRAG build用独立有限正数timeout；Memory/Dream与浏览器单列。启动入口使用本机空闲规划的backend8015/frontend8446，保留其他listener；见[本机准备](../work/local-cloud-integration/local-acceptance-20261008/ACCEPTANCE-PLAN.md)。

## 云端重合与本地新增

角色判断、政策预取、请求内检索复用、精确官方DeepSeek Thinking关闭已存在于170起点。本轮使用这些公开合同，未改其实现，也未重新移植旧amax能力；不能据此宣称任意云端后继兼容。真实API smoke仅证明本次受控调用范围。

本地新增是上述评测CLI、40开发用例/rubric、20独立维护样本、来源/批次绑定、报告/失败反馈与本机测试证据。RAG/Pi/GraphRAG/订单/售后/前端产品源码及静态业务fixture没有本轮改动。审阅以170到本地分支实际diff为准，不提前为潜在冲突改实现。

未提交本机文件与原因见[清单](LOCAL-UNCOMMITTED-INVENTORY.md)：配置、独立依赖/缓存、DB/索引、构建及原始日志保留Git外；独立20题/60组合包/100计划和各版评分在Tester隔离目录持久保留，不删除或泄露正文。
