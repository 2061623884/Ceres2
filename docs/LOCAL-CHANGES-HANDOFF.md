# 本地测试与评测交接

当前任务入口：[TASK](../tasks/ceres2-local-followup.md)，行为方案：[规格](plans/ceres2-local-followup-spec.md)，工具步骤：[评测使用说明](LOCAL-FOLLOWUP-EVALUATION.md)。本文件不代替任务状态或本人验收。

本次用户进一步授权只读调用原amax模型配置、真实测评后常规推送。本次真实报告见[100次任务评测](../work/local-followup/04/real-model-20261008/REAL-TASK-EVALUATION.md)和[组件/Memory/Firefox](../work/local-followup/04/real-model-20261008/REAL-COMPONENT-VERIFICATION.md)：100次实际尝试，机器business66通过/30失败/4未知；不宣称整体通过。原0次离线计划是工具阶段历史，保留原版，不覆盖本次结果。

## 分支与来源

- 仓库：[2061623884/Ceres2](https://github.com/2061623884/Ceres2)。
- 本地分支：`codex/ceres2-local-followup-20261008`；工作树：`/data/amax/Documents/projects/Agent/Agent产品/Ceres2-integration-20261008`。
- 已知起点：`170fac0bc75fcc855897b073337ba218abeb5b7d`，tree `295499ee22cc30485d38eba82e96330a39d7d573`。
- 真实100执行使用工具源码`739f13ead0c53ce9d82519efc30f51263e29ab45`、执行HEAD `00b397443bd7258d2166c6445ac4ac066cefd21d`；原29项/15.73s验证属于739。初候选为`e855d691d0a446c9e5385196134b55f2ec609320`，第一轮修复为`4e021e46e8c16671ae1366ec09c11f39bad01bd6`。
- 本次真实报告候选为`fbb44854a412da8d77a7ec30426d240756a9d261`；实测后的评测driver/harness修复为`4008faacae169d18de80f6a444f59c47a93915b7`，最终两处必填签名清理为`cbca5d15bd40bd200f542d0eeaa1bc8192af9424`。后续交接提交不改变该源码；未重新真实采样或重评分，产品非evaluation路径始终与170起点一致。
- 参考评测：[Ceres1 72bb1b99bf040c8b0bae5d026888bc059bc9423d](ceres1-evaluation-reference.md)；借方法与公开样本组织，不继承其成绩、runtime 或旧状态。
- 原本地优化 `6734c7fe79e670df2dae12b065dcc49c0b10a307` 保留快照；后续在本工作树，原main与其他工作树保留。
- 不合并。本次源码/报告候选`3cc8d804bb3fbd7f405bfb73f4f44c65b3550205`已普通push并读回远端SHA一致，见[发布回执](../work/local-followup/05/REAL-PUBLICATION-RECEIPT.md)。其后仅补发布状态/回执，最终完整交付SHA以分支与主会话再次读回回报为准。原工程配置/运行数据不修改，未执行rebase/cherry-pick/force push；旧00b397工具交付阶段只在本地。

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
| 原准备阶段浏览器 | 先前本机170fac0 Firefox HTTPS run11通过 | [原本机报告](../work/local-cloud-integration/local-acceptance-20261008/LOCAL-ACCEPTANCE-RESULTS.md)；受控provider/检索。本次独立商品订单浏览器另列下节 |
| 原工具阶段100任务计划 | planned100/attempted0/not_run100，业务unknown100 | [独立清单](../work/local-followup/04/ACCEPTANCE-MANIFEST.md)保留旧离线v1-v4；仅描述旧批次，不覆盖本次真实运行 |

历史云端746/5、183及Ceres1成绩不进入本表计数。RED、修复前失败、首轮GREEN失败和评分夹具版本变更均保留 `work/local-followup/01/02/`。检索指标v1和v2来自同一原始18条结果，增加macro说明只是离线更正，不新增检索执行。

e855候选的[Standards](../work/local-followup/05/STANDARDS-REVIEW.md)未发现硬违规，提出重复校验/步骤分派两项判断性smell；[Spec](../work/local-followup/05/SPEC-REVIEW.md)指出指标缺失与不可比较值中断。单一修复owner补Guide终态、critical观察分母、逐轮15秒和核心业务/时延组合稳定性，首useful明确未知；不可比较TypeError保留原因后继续，未知operator配置错误仍传播。另补plan选中行合计与确认后cart单价/行额/总额核对；缺Offer仍能核对已知行额，缺金额不填零。四个实际caller共享标注校验；执行/判分分派保持独立，防止评分以执行器自身为期望。三个新增CLI负例与受影响整组均通过，修前报告未覆盖新source，delta复审另留证。

4e021的[Spec delta](../work/local-followup/05/SPEC-DELTA-REVIEW.md)另发现两个金额诊断漏项，739已修复：已知行额不依赖数量/单价是否齐全而参与合计；成功receipt商品不符仍独立核对cart金额。两个实际RED、中间RED、窄GREEN及最终共同29项均保留，见[修复依据](../work/local-followup/05/REVIEW-RESOLUTION.md)。缺数量/单价的合计相符仍保持unknown，不把局部可核对证据当完整通过。

739的[Standards最终](../work/local-followup/05/STANDARDS-FINAL-REVIEW.md)未发现硬违规或新增smell；[Spec最终](../work/local-followup/05/SPEC-FINAL-REVIEW.md)确认已发现代码问题修复，未发现此次差异仍有代码缺陷，仍明确整体规格未完成。独立Tester对原100未运行批次做最终v4离线复核，仍是unknown100/实际执行0；不同评分版本保留，不把重复离线处理计作模型执行。

## 本次真实执行与实际缺口

执行HEAD `00b397443bd7258d2166c6445ac4ac066cefd21d`，业务/评测工具源码仍为739。原amax配置仅限定字段注入隔离进程，主/提取/Dream模型均`deepseek-flash`，provider host为`api.deepseek.com`；密钥未复制到Git或输出。原库/索引/session/checkpoint未导入。

| 本次范围 | 实际结果与口径 |
| --- | --- |
| 真实100次任务 | 100 attempted/0 not_run；机器business66 pass/30 fail/4 unknown。Guide终态另为66 completed/24 waiting_confirmation/9 failed/1 protected，数值不可互相替代 |
| 核心稳定性 | 20核心各三次，60试次44 pass/13 fail/3 unknown；三次均business pass11/20 |
| 15秒与多消息 | 100/100运行时样本达15秒；39/100 run有43条message.interim，首次interim P50/P95约2.06/3.36秒；首useful/自然度无人标注，仍未知 |
| 真实RAG组件 | 固定BGE新hybrid、官方GraphRAG3.2 build成功；44 entities/61 relationships。Local/Global约18.0/18.7秒，用180秒独立组件预算；正式100中Graph工具调用0，不证明Guide15秒图检索或图收益 |
| Memory | 正式90 extraction jobs completed，usage不持久化；正式owner未达门槛，自然Dream0。另独立10合成自动记忆触发1次真实Dream；内容质量未人工验收 |
| 实际Firefox | 当前built UI→独立真实API/SQLite，商品详情/加购/模拟结算/发货/签收通过，1 delivered模拟订单；Guide0/无新模型调用，本人UI与完整Guide浏览器仍待验收 |
| 实际usage | 409条provider SSE观测记录：primary340/interim审校68/general审校1，已观测totalTokens2,229,367为下界；4/100 call-summary不完整，cacheWrite/cost均未知，不推费用；Graph与Memory单列 |

唯一公开`dev-01:trial:3`首轮completed但未生成plan，声明confirm_plan时driver解引用null导致TypeError；保存完整已有capture/before/after，确认HTTP未发，原outcome为runner_failed/质量unknown，不重跑伪造成功。公开场景还暴露在库精确SKU被答无匹配、规格未澄清、预算内商品无plan等失败。Kev配置缺失，实际判断0/100，9条routing业务失败；critical观察0/eligible99不能签为系统安全。新报告保留失败/脚本问题和原始hash；100个run均未因64-record tail上限截断，不等于4个缺失的call summary完整。

## 实测后的工具修复与验证

独立审查后仅修改评测driver与本轮执行harness，不改变Pi/检索/订单等产品行为。声明confirm_plan却没有当前plan时，driver现在给出明确ValueError，继续保留原runner_failed、capture和前后状态；这不解决模型未给plan的业务失败。Graph未观测证据保留null/not_evaluated，成功证据按必需字段读取，实际0/空集仍保留。配置入口统一窄reader，清除继承环境中当前Settings的大小写别名后注入获准值；保留HOME/TLS/proxy。两个没有当前调用方的参数默认值已移除，调用方明确传值。

- 四模块受控回归：**35 passed/14.03s**，对应4008的源码快照，见[组合验证](../work/local-followup/01/tool-combined-after-real-harness-casefold-fix.md)。
- 最后两处签名清理：仅harness模块 **5 passed/0.48s**，执行时HEAD为4008、工作树包含后来提交到cbca的签名；见[最终5项](../work/local-followup/05/real-harness-final-signature-cleanup-green.md)。这5项与前35项重叠，不加总，也不声称cbca重跑了35项。
- 最终受影响源码11项见[新清单](../work/local-followup/04/real-model-20261008/REAL-HARNESS-FINAL-SOURCE-HASHES.sha256)。真实执行的旧41项SOURCE-HASHES和6项dist清单保留原样，只用于旧实测溯源。

[Standards最终复审](../work/local-followup/05/REAL-STANDARDS-FINAL-REVIEW.md)确认本轮已发现违规及默认参数问题关闭；[Spec最终复审](../work/local-followup/05/REAL-SPEC-FINAL-REVIEW.md)确认窄修符合当前调用契约，整体规格仍开放。修复依据及各轮RED/GREEN见[记录](../work/local-followup/05/REAL-REVIEW-RESOLUTION.md)。这些修复之后没有新增真实模型、服务或浏览器运行，原66/30/4保持不变。

## 未完成、失败与限制

本次真实主模型、Graph组件、提取、合成Dream和独立商品订单浏览器已执行。仍未完成真实Kev、正式Guide里的Graph调用/15秒门槛、自然Dream、完整多轮售后/Memory driver、完整Guide浏览器及本人接受。生产15秒/5轮合同未改；本次模型来自用户明确“使用原配置”指令，不能拿历史qwen结果直接对照宣称改善。

完整回归4个原环境失败虽然已补验，原始全量仍是752/4；最初全量shell完整调用串未单独保存，报告如实列出该溯源缺口，不补造命令。没有当前真实模型质量/成本改善结论。新验收与公开集共享部分上位类型，Tester可见公开集，不能称严格盲测/泛化。工具支持小型采购多轮，未支持完整订单/售后/Memory setup driver；现有受控生命周期测试与这些真实评测缺口分开。

## 配置、数据与迁移

本轮没有业务schema迁移。原静态fixtures为73商品/73Offer、8菜谱、11政策；当前新业务库和索引按本工作树可重复seed/build，数据库/会话/订单/checkpoint不从旧库导入。业务库、索引、固定BGE缓存、独立venv/node_modules、`.env`及原始日志留Git外；tracked evidence保留内容hash和命令/版本入口。

[旧交付检查](../work/local-followup/05/FINAL-DELIVERY-CHECK.md)记录00b397时新树空白.env，不作为本次进程配置结论。本次`provider_job.py`通过dotenv只读原amax获准字段并注入进程，禁读本树blank.env、设置新DB/checkpoint；没有复制全文件或密钥。本次Kev仍缺、operator访问未配置，不能复用旧数据弥补。启动入口见[工具说明](LOCAL-FOLLOWUP-EVALUATION.md#按本次授权复用amax配置)，原配置模型变更后必须另建新批次。

本次先完成Graph/hybrid冻结再20核心pilot、同条件续80，没有中途改模型/索引/源码或重跑失败。服务均已优雅停止，8015/8446无listener，原listener保留。后续新增优化必须保留本批作为基线；更正脚本/评分另留版本，不能把重评分计作新增模型执行。Graph build预算900秒、组件query180秒，与生产Guide15秒分开。

## 云端重合与本地新增

角色判断、政策预取、请求内检索复用、精确官方DeepSeek Thinking关闭已存在于170起点。本轮使用这些公开合同，未改其实现，也未重新移植旧amax能力；不能据此宣称任意云端后继兼容。真实API smoke仅证明本次受控调用范围。

本地新增是上述评测CLI、40开发用例/rubric、20独立维护样本、来源/批次绑定、报告/失败反馈与本机测试证据。RAG/Pi/GraphRAG/订单/售后/前端产品源码及静态业务fixture没有本轮改动。审阅以170到本地分支实际diff为准，不提前为潜在冲突改实现。

未提交本机文件与原因见[清单](LOCAL-UNCOMMITTED-INVENTORY.md)：配置、独立依赖/缓存、DB/索引、构建及原始日志保留Git外；独立20题/60组合包/100计划和各版评分在Tester隔离目录持久保留，不删除或泄露正文。
