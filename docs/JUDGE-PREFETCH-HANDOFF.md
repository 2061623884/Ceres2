# Cursor 接手：角色判断与政策预检索重建

本文交接本轮服务端/runtime、用户负责的前端适配和剩余真实验收。当前状态只看[四票总 TASK](../tasks/ceres2-judge-prefetch.md)；实现与安全约定看[执行决定](REBUILD-DECISIONS.md)和[规格](plans/ceres2-judge-prefetch-spec.md)。本文不是验收签字，也不继承[上一阶段交接](NEXT-EXPERIENCE-HANDOFF.md)的通过成绩。

## 1. 先确认版本，再接手

**最终四票候选尚未冻结；不要把目前可下载的 WIP 当作可直接验收的成品。** 本段为 2026-10-07 交接准备快照，后续以总 TASK 的精确候选和发布映射更新。

- 新实现起点：公开 `main` 的 `4bed9c891261e382122d424825b649989ea92c92`。不需要等待不可得的历史 `f45c4ff92f96f535d156a2f88053ae10e8486fa1` 才开始本次重建；也没有恢复、合并或验收该旧候选。
- 集成分支：`ceres2/judge-prefetch-rebuild-20261007`。**01 技术交付发布已核实**：远端 `19822b146637fbf9cbba75dcf499984d393a4605` 对应本地文档后继 `4b576321317d6755cb2ef5845ceca6f89ba3e2b5`，完整 tree 均为 `cfb1028c1330537bc703bfff27591e109e61ea13`；见[发布映射](../work/judge-prefetch/publication-role-entry-final.json)。这仅是 01 里程碑，不是四票最终候选。
- 01 修复 `9f2eff1265c373736cc5f8683c8ccaa680959c30` 已合入 `46f3fcf47d544e0c0ecead0abc13cb23d63a38b8`。480/480 backend、其中重叠的 149 项 focused、Pi typecheck/build 和依赖检查对应同一 244 文件冻结源码，两轴复审关闭原问题；01 状态仍为“待验收”。见[Tester 报告](../work/judge-prefetch-rebuild/01-role-entry-verification.md)、[源文件等价记录](../work/judge-prefetch-rebuild/01-role-entry-final-source.json)及[01 TASK](../tasks/ceres2-judge-prefetch-01-role-entry.md)。
- 旧独立 WIP `f323d15751c141e0ded4763a3881bbda6355eae3` 仅供源码保全，不能代替已审查修复。02 云端技术门槛现已完成，产品提交 `0aaffb39549db2704c6c0c414e3819277023e7a6` 已合入 `7ea06a343f95043cc5c1948ef74fc139e0de2280`，已核实发布为远端 `e434e1b5419dfadec9db65dea13b63974a9d701e`，对应本地交付 `0559d9ed17e65cb4f6f8dfab80b83152e6fe280e`，完整 tree 均为 `18b51049c0d847eed04fac3ec26ba36c4afe16fa`；[02 发布映射](../work/judge-prefetch/publication-policy-evidence-final.json)。03 核心已完成并通过专项／两轴复审：产品提交 `35a30fab775764cfcbc01ee84599fb450b6411bd` 已合入 `d6a40886926bf203b53c52db27d2177b1b3dcb80`，其准确远端发布待登记；04 冻结核心全量及支持／文档门槛进行中。四票最终候选仍未交付。
- 最终交接须由集成者登记：准确远端分支／完整 commit、对应本地受测源码或完整 diff、tree 等价证明、各层报告及用户前端 commit。缺少最终冻结信息时，不开始四票整体验收；可以按已交付的 01 合同准备本地前端适配。

用户现有本地 Ceres2 保留了 **24 文件未提交补丁**，以及本地 `.env`、数据库与前端改动，必须原地保护。最终发布核实后，从用户已配置并核实的 Ceres2 remote fetch 最终分支，按确认的完整 SHA **另建独立本地 worktree** 验收；不要在脏工作树上 reset／checkout 覆盖、强制 stash、清理或整包套用补丁。新 worktree 使用独立安装与新隔离数据库；不要复制在用数据库、索引、session、订单或凭据。凭据仍由用户在本地管理，不要求上传或迁入云端。

开始前只需核对实际 checkout、未提交改动、Prompt、依赖和构建产物适用版本。候选未变且已有同版证据时，不要求重跑未受影响的整套 unit suite；产品修复后重验受影响项，并完成原规格要求的最终集成门槛，不能拼接不同版本成绩。

## 2. 本轮范围与验收边界

四票顺序仍是 **01 → 02 → 03 → 04**：

1. **角色入口**：只有可可新文字调用角色 Kev；yes 等用户确认才转墨墨，no／uncertain／timeout／error 留在可可处理完整原文。墨墨文字不调用角色或政策 Kev，返回购物只用明确按钮。可可首次输入保留相关任务、活动问题、待澄清和有效引用，不再依赖四能力分类。
2. **政策证据**：留在可可的文字做政策判断；yes 用完整原文预查已有政策，把实际证据、查询范围、版本和引用交给同一个 Pi。未知／空／部分／异常分开；购物与政策子请求都保留，不新增回答 Agent。
3. **请求内复用**：同请求、同有效来源版本、同范围复用真实证据；新问题、条件变化、不足、失效或此前失败可补查。多范围合法引用继续有效，不做跨请求缓存平台。
4. **同版证据**：集成和调用对照，不负责兜底补齐前三票业务。各票完成程度及证据见对应 TASK，以上是交付范围，不是完成宣告。

仅对规范化后精确 hostname `api.deepseek.com` 显式关闭 thinking；其他主机不新增 thinking／reasoning_effort 字段，不能用 null 冒充字段不存在。早期[五路径报告](../work/judge-prefetch-rebuild/thinking-transport-verification.md)是局部历史证据；[01 最终同源 focused／full](../work/judge-prefetch-rebuild/01-role-entry-verification.md)已重新覆盖主 Pi、主 validator、表达、表达 validator、Momo、提取及 Dream 七条实际请求路径，但没有访问真实 provider。模型、provider、temperature、输出额度、重试与 deadline 保持用户批准配置，不指定 `deepseek-flash` 或加大额度。

Python 继续独占业务事实、权限、确认和事务；导航、政策结果与选择商品都不是购买／退款授权。所有供给、结算、订单和售后均为模拟业务；提交售后申请不等于退款到账。

分别记录以下层级，不写笼统的“全绿”：

- **受控服务端/runtime 与 wire**：01 技术门槛见上述同源报告，[Standards](../work/judge-prefetch-rebuild/reviews/standards-01-rereview.md)／[Spec](../work/judge-prefetch-rebuild/reviews/spec-01-rereview.md)两轴复审均关闭原问题；02 同版 524 backend（含重叠专项 44）、guard proof、Pi build/typecheck、依赖与两轴复审已完成，见[02 报告](../work/judge-prefetch-rebuild/02-policy-evidence-verification.md)；03 修复后 152 项专项（含 34 复用／安全用例）及两轴复审已完成，见[03 报告](../work/judge-prefetch-rebuild/03-query-reuse-verification.md)；04 最终同版全量及独立支持／文档仍待完成。有限[基线烟测](../work/judge-prefetch-rebuild/baseline-verification.md)不替代功能验收。
- **测试隔离更正**：旧 Node guard 因生产子进程不继承 NODE_OPTIONS 而未在实际 Pi worker 强制加载。旧源码／测试成绩不改写；测试 harness 已修复并有四项真实子进程守卫证明，最终全阶段验证使用新 launcher。详见[更正与证据](../work/judge-prefetch-rebuild/node-guard-correction.md)。
- **真实模型／Kev／语言品质／usage／时延**：本交接未执行，须用户冻结配置、有限用例及整次额度后亲自运行。
- **typed DOM／真实浏览器**：前端由用户本地实现，本轮云端不修改 `frontend/` 文件；构建或 HTTP fixture 不能替代浏览器结果。
- **用户本人验收**：保持开放，不能由 agent 代签。旧 426 backend／37 DOM／41 live 及本地旧补丁的部分通过均不继承。

## 3. 用户本地前端适配

先读 `frontend/AGENTS.md`。以下已对照 01 接受的本地集成 `46f3fcf47d544e0c0ecead0abc13cb23d63a38b8` 的[公开 schema](../backend/app/schemas/navigation.py)、[导航 API](../backend/app/api/navigation.py)及[Guide 结果投影](../backend/app/services/pi_product_turn_service.py)；最终 02／03 合入后须再次核对，不据旧 WIP 实现。冻结语义见[执行决定第 3 节](REBUILD-DECISIONS.md#3-冻结的公开服务端兼容策略)。

已有明确语义需保留：

- wire 角色仍是 `keke`／`momo`；复用 `/api/v1/navigation/sessions/{session_id}` 下的 `/opening`、`/routes`、`/prompt-displayed`、`/switches`。
- `/routes` 发送 `request_id`、`opening_id`、`role`、完整 `message`，以及需要的 `selected_object`／`role_session_id`。`ready` 继续原角色，同一原文／request 身份不能换 ID 再提交；`switch` 只展示建议，用户接受前不切换、不执行业务。
- 接受切换建议时携带其 `routing_request_id`；拒绝使用 `accept: false`，留在原角色。只对确实展示过的建议发 `/prompt-displayed` ACK。错误或旧引用应显示服务端可恢复原因，不私自重建旧授权。
- 纯角色按钮发送 `/switches`，不带 `routing_request_id`（或为 null）；响应 `handoff: null`，不能从 pending／accepted 状态捞回旧文字。墨墨中“回可可”“回去买水”及引述、条件式返回均不自动导航或发起购物。
- 新请求不再靠 capability、旧 `navigation`／`clarify`／`unavailable` 分支决定首次模型上下文或阻断入口故障后的可可继续。保留旧回执读取不等于恢复旧行为。
- 保留现有 Guide HTTP/SSE、事件 envelope、版本／displayed refs 校验和结果先行顺序。购物结果、政策事实、职责边界及明确角色入口可能同时出现，不能只渲染单一结果分支。

### 01 实际类型差异与待接入动作

- `frontend/src/lib/chatNavigation.ts` 的新 `RouteDecision.status` 以服务端 `"ready" | "switch"` 为准；`continue_original` 固定为 `false`，`capability` 为 `null`。旧客户端额外枚举不能作为新请求分支继续使用。服务端还提供 `opening_id`、`source_role`、`authorized_role: "keke" | "momo" | null`、`criteria_version`、`anchor: [number, string | null, number]`、`legacy_replay: boolean`。
- 加法字段 `entry_judgment?: {outcome: "yes" | "no" | "uncertain" | "timeout" | "error" | "not_attempted"; elapsed_ms: number | null; reason: string | null} | null`。Momo 为 `not_attempted`／`reason: "momo_direct"`；入口故障保留实际 outcome／reason，不能把 ready 显示成判断成功或 no。`provider_output`、`provider_error`、`message` 可空，不展示未经脱敏的原始响应。
- `frontend/src/lib/saleGuide.ts` 的 `TurnResponse.answer_kind` 需接纳纯职责说明 `"role_boundary"`，并添加可选 `navigation_action: RoleSwitchAction`。混合购物／waiting 结果仍保留其原 `answer_kind`、`runtime_status`、问题与卡片；职责说明在 `messages` 中追加，不能用 `answer_kind === "role_boundary"` 作为展示按钮的唯一条件。模型内部的 `role_boundary: true` 不是要求前端读取的公开布尔字段。
- 服务端 `RoleSwitchAction` 准确形状如下。只在用户点击后，把 `request` 原样送到 `/api/v1/navigation/sessions/{action.session_id}/switches`，并消费实际响应；展示 action 本身不发请求：

```json
{
  "type": "switch_role",
  "session_id": "<服务端 session_id>",
  "request": {
    "opening_id": "<服务端 opening_id>",
    "target_role": "momo",
    "accept": true,
    "routing_request_id": null
  }
}
```

该 host action 是明确纯导航，响应 `handoff: null`，不能自动重放已由可可处理的原文。它与 yes 建议携带 `routing_request_id` 后接受并续接原文是两类动作。`show_prompt: false` 也不能成为隐式续接的许可。现有接入点是 `frontend/src/App.tsx` 的 `beforeText`／`switchChatRole`、`chatNavigation.ts` 的 `chooseRole` 及 Guide 结果处理器；云端没有修改这些文件。

公共行为依据：[01 HTTP/SSE/typed action fixtures](../backend/tests/test_judge_role_entry_public.py)、[旧导航回执 fixtures](../backend/tests/test_judge_legacy_navigation_public.py)。01 已覆盖 completed／waiting 主结果与职责边界并存；**waiting + policy + role boundary，以及 general/dish/history/memory 的政策组合已由 02 接续实现并同版验证**，不能把它记入 01 的旧范围。03 已按下节固定多引用与摘要合同；不存在另造的公共 SSE 事件。

浏览器门槛见第 5 节；旧 capability 按钮曾成功续接原文，不能替代新合同的验收。

### 02 已交付的政策与失败呈现

02 保持现有 Guide/SSE 事件和事实投影形状，没有要求前端消费新的预取专用事件。宿主 `messages` 可包含原购物／澄清／普通解释／明确记忆结果，再附真实政策及职责边界；须完整呈现消息单位和确认按钮，不能只取 `message` 第一条。政策与职责说明不写成 `general` 历史。

- `runtime_events` 中的 `policy_judgment` 记录 outcome、elapsed_ms、reason、rules_version 与未知 usage；`policy_lookup` 区分 origin 为 prefetch/tool、success/empty/error、source_version 和真实 policy_ref（失败没有 ref）。这些诊断不等于写入授权。
- 预取以完整原文和未指定 category 查询。成功／空保留真实来源、版本及范围；命中只表示部分可用规则，无匹配仍未知；检索异常是实际 attempt，不能显示成无条件允许。未恢复的真实失败由宿主在相关范围投影为暂时失败，不采用模型自行声称的失败／资格／到账事实。
- 纯政策结果与合法 completed/waiting 主结果可并存；补查失败不会强迫丢弃购物或澄清。最终发布前 request freshness、取消与原 deadline 均复查；`PI_DEADLINE_EXCEEDED` 表示待发布结果和事务内暂存 cart/memory 修改已回滚，页面不得显示已写入成功。
- 同请求去重、有效早期 ref 和多范围结果由后续 03 的独立证据覆盖，不能追溯归入 02 旧成绩。

依据：[02 fixture](../backend/tests/test_judge_policy_prefetch_public.py)、[安全 fixture](../backend/tests/test_judge_policy_safety_public.py)、[最终源码证据](../work/judge-prefetch-rebuild/02-policy-evidence-final-source.json)。公开 action 与 wire role 合同沿用 01。

### 03 已交付的多范围事实与有界计数

模型结果现在可使用单个 `policy_ref` 或非空 `policy_refs` 列表，也可同时提供两种形式；Python 会校验每个显式值的当前请求／来源版本。早期有效引用不会被后续查询淘汰，同范围成功或空结果复用完整证据，失败仍可补查。多个范围及各自来源／未知限制通过现有宿主 `message`／`messages` 展示；`policy_refs` 是模型／runtime 输入契约，不要求前端伪造引用或发送新导航请求。

标准 result 和持久回执增加 `runtime_summary`：

- `policy_lookups` 与 `policy_lookup_outcomes: {success, empty, error}`：实际检索及结果次数；复用不增加实际检索。
- `policy_tool_lookups`：所有实际工具来源检索，包括首次普通检索、补查或重试；不能一律标成“额外补查”。
- `policy_reuses`：执行侧命中复用次数。
- `tool_starts`／`primary_pi_turns`：主 Agent 观察到的 SDK 工具开始／轮次，不是成功工具数、HTTP 次数或 validator 调用。
- `policy_judgment`：实际一次判断诊断或 null；`events_truncated`：详细事件尾部是否被裁剪。

详细 `runtime_events` 仍最多保留 256 条，完整计数不能从尾部推算。硬错误可没有 summary，缺失字段一律 unknown，不填零；这些字段也不能推导 provider tokens、成本或真实性能收益。公开 rollover fixture 实测一查／48 复用／49 starts／5 primary turns 并核对回执；只是受控正确性证据，不是上线性能。依据：[03 公开 fixture](../backend/tests/test_judge_policy_reuse_public.py)、[安全 fixture](../backend/tests/test_judge_policy_reuse_safety_public.py)、[核心复审](../work/judge-prefetch-rebuild/reviews/spec-core-final-rereview.md)。

## 4. 本地配置与启动，只由用户操作

**启动 FastAPI 会启动 `MemoryWorker`，现存任务可能发送真实模型请求并产生费用。** 不把启动／健康检查当成无外部影响的探针；不要由 Cursor 自动启动 backend、live batch 或后台任务。以下命令仅供用户确认数据发送与费用后亲自执行，本次文档工作没有运行它们。

- `.env` 留在本地可信编辑器，凭据、headers、完整 provider 原文和数据库不提交、不上传、不粘贴到交接。配置读取根目录 `.env`，见[config.py](../backend/app/core/config.py)。
- `OPENAI_BASE_URL`／`OPENAI_API_KEY`／`LLM_MODEL`、独立 `MEMORY_EXTRACTION_MODEL`／`MEMORY_DREAM_MODEL` 均由用户保留实际批准值；两记忆模型不应擅自改为主模型。`KEV_BASE_URL` 指向已核实的服务，不猜地址。
- **旧 `.env.example` 和旧交接中“联合四能力／缺 Kev 阻断后手动续接”的说明不能当新角色契约。** 最终以 01 的公开合同核对：Kev 缺失或错误应保留真实原因并继续可可；墨墨和按钮零 Kev。仅配置完成不代表 Kev 服务兼容或自动判断通过。
- 新建明确的隔离 `DATABASE_URL` 与 `MERCURY_CHECKPOINT_PATH`，核对实际加载路径和已有后台 job。不同验收旅程不混用旧 owner／业务数据；Dream 长期观察单独保留环境，不能为其他测试反复重置。
- 当前云端独立 Python 环境是 `backend/.venv`，不同于旧交接中的仓库根 `.venv`。新机器依照[requirements.lock](../backend/requirements.lock)及两个 package-lock 安装；已有匹配依赖／dist 不必重复安装或构建。所有安装、测试、lint、typecheck、build 仍交专职 Tester。

从准确候选仓库根目录，用户在隔离配置就绪后执行已有模块：

```bash
(cd backend && .venv/bin/python -m app.services.seed_service)
(cd backend && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8012)
```

另一个终端：

```bash
(cd frontend && npm run dev -- --host 127.0.0.1 --port 8443)
```

浏览器入口 `http://127.0.0.1:8443`；Vite 将 `/api`／`/media` 代理到本地 8012。上述入口已对照[seed 模块](../backend/app/services/seed_service.py)、[启动生命周期](../backend/app/main.py)、[前端 scripts](../frontend/package.json)及[Vite 配置](../frontend/vite.config.ts)，仅核源码，未执行。Pi 构建命令 `npm run build` 来自[runtime scripts](../runtime/pi/package.json)，由 Tester 在 dist 不匹配时执行。仓库没有 lint script，不写 lint 通过。端口被占用先查原因，不杀未知进程或开放公网。

不要直接执行旧 `work/live-validation/run_live_batch.py` 作为新候选验收：其历史用例／模型／版本不能自动沿用。本交接不创建或运行新 live harness。

## 5. 尚未执行的验证计划：只补缺口

**执行前待用户冻结**：准确旧／新对照源码、数据与政策版本、Prompt、provider／模型和参数、以下最终用例文字、每例重复次数、执行顺序、整次时间或费用上限及中止条件。没有这些授权不开始真实采样；不擅自给出预算或用无限重试凑成功。

由同版 Tester 证据覆盖受控错误／权限 fixture，用户真实采样和浏览器补以下有限旅程；已通过且未受影响的受控项只链接，不重复大跑：

1. **可可纯政策与混合请求**：无订单问“退货条件”；再问“选低糖饮品并问退货条件”；普通“你好”作非政策对照。核对完整原文、购物条件、实际证据和来源，以及同一个 Pi 同时交付两部分。样本结果不预判为命中或成功。
2. **政策范围与失败边界**：同请求相同政策范围重复查询；新增“配送进度规则”；条件／类别变化、多子问题与旧有效引用。空结果示例“火星定制条款”。部分、异常、judge uncertain／timeout／error、取消／截止优先引用同版受控 fixture；真实未遇到的分支记 not run，不在真实账户故意制造权限或网络故障。
3. **角色与原文**：可可具体售后建议接受／拒绝；Kev 缺失或故障后的可可继续及职责说明；墨墨直达、纯／复合／引述返回文字不自动切页；明确按钮仅返回。检查同 request 重放、旧建议、不同 owner／opening／版本与“就第二个”的相关上下文，业务确认始终独立。
4. **真实浏览器连续动作**：切换建议／拒绝、host 角色 action、Momo 返回按钮；刷新、关闭重开、Back／Forward、连点、旧 SSE 晚到、停止和明确恢复。核对提示 quota／ACK、原文仅消费一次、旧授权／已确认加购与售后不重放；同时呈现购物、政策、未知／部分／失败与职责边界。
5. **完整模拟业务回归**：采购数量／约束／预算 → 明确加购 → 独立模拟结算 → 同一订单售后提案／明确提交／返回购物；保留人工负责期间写入保护、记忆／历史方案及结果先行。未触及或未获准的真实旅程保持 not run，不把空候选或申请提交当业务成功。
6. **中文与调用比较**：观察事实卡片与连接语是否简短、不重复、没有编造条件。逐例记录入口／政策判断、HTTP、实际检索／复用／补查、Pi 轮数、首次事实／可操作／首字／最终时刻、可得 tokens／费用和失败原因。端到端从首次可信接纳原请求起算，包含独立 `/routes` 耗时；政策预取与 Pi 不重置原运行阶段 deadline，分开记录直接 Guide 准入的实际起算边界。

没有 usage／价格就标 unknown，不填零；小样本不支持稳定 P95、降本或提速承诺。检索少一次不保证模型少一轮，额外 judge 和上下文开销必须计入，不能用速度抵销质量失败。上一阶段独立未见 holdout、冻结 V3 比较和用户体验仍按其原 TASK 保留，不能用上述公开开发样例代替。

## 6. 本地已知真实问题，只记录移交

来源为用户 2026-10-07 本地补充；这些是旧本地候选的真实失败／缺口，**没有由当前四票证明修复，也不自动扩大四票为商品或记忆重设计**。如后续授权诊断，保留原始失败并先固定同版最小复现；当前改动直接造成的回归交回所属票处理。

- **稳定偏好 422**：`PI_UNGROUNDED_BUSINESS_TEXT`，记录工具列表空、Guide message 未提交。用户的实际原句完整留在本地，分享仅用安全脱敏 verdict／拒绝原因码、call stage／工具阶段、消息提交和 extraction job 状态。输出缩短不等于记忆通过；不能放宽事实守卫、换模型或加额度来掩盖。
- **茶候选为 0**：已到 `guide_request → explore_products`。诊断时分开语义召回与权威糖属性筛选；名称含“茶”不能证明符合条件，`sugar-free` 与 `unsweetened` 不能无条件等同。
- **饮水候选为 0**：核对“饮用水”的 canonical type、包装 `bottle`、`pack_count=12` 与销售单位“箱”的映射，保留各筛选阶段数量／原因。合法无供给与误过滤分开，不放宽用户约束或预算。首次 Kev 未配置的旧失败按新 fallback 合同重新观察；旧按钮曾续接原文不是新合同通过。
- **自然记忆／Dream 未开始**：本地只报告 ownerB 一条 automatic。需在专用隔离环境正常对话与真实提取，达到至少 **10 条有效、未被 explicit／tombstone 遮蔽的 automatic 记忆**；不插记录、改时钟或强制调用。首次真实 Dream 成功后保存 job ID 和 `completed_at`，从该时刻开始实际 **24 小时只读观察**，核对正常重启、冷却和不重放。门槛满足即可开始观察，其他验收可在另一隔离环境继续；实际 24 小时没经过只记进行中。

原失败的 `finish_reason`／reasoning tokens 为 unknown，不断言都由 thinking 导致。本交接没有启动自然对话、Dream 或长期观察。

## 7. 回报格式与收尾

每次只提交必要的脱敏结果：准确 backend/runtime 与 frontend commit、适用配置／数据版本、用例及次数、passed／failed／not run、错误码和阶段、相关 receipt／job／request 身份、必要截图、时间与可得 usage，以及证据链接。原文和敏感运行日志保持本地，不附凭据或原始数据库。

实现修复、受控通过、真实模型通过、浏览器通过与本人接受分别写明。最终接受前继续保留失败和未测项；不自动合并 main、部署、推送用户前端或清理工作树。

本文件由源码与现有文档核对形成；此文档步骤未修改产品／前端，未执行安装、测试、构建、真实请求、服务启动或发布。
