# Ceres2：Cursor 本机接管文档

交接日期：2026-10-07，时区 Asia/Shanghai。只读进程／数据快照采集于北京时间 **00:30:19**，随后补齐了数据库／checkpoint 的有效路径。用户已明确要求停止所有工作，由 Cursor 继续执行；Codex 的实现、测试、安装和后续观察均已停止，服务、数据和未提交改动保留。本文是交接快照；后续当前状态只维护 [TASK10](../tasks/ceres2-next-10-candidate-evidence.md)。

## 1. 先看结论

**整体尚未验收通过。** 真实浏览器已经完成选品、明确加购、模拟结算、同订单退款提案及明确提交，返回可可也没有重放旧操作；返回后的新饮水目标触发 5 轮工具保护，没有得到候选。自然记忆试验也出现模型失败，**首次 Dream 和 24 小时冷却观察尚未开始**。

接管最高优先级是核对并修复 **DeepSeek 官方请求未显式关闭 thinking**。刚查明官方默认启用 thinking，当前 Pi 的本地 `thinkingLevel: 'off'` 不等于已向服务商发送关闭参数。这处修复**尚未实施**，不能写成已经解决，也不能把全部历史失败都归因于它。

保留本机未提交代码、现有 `.env`、业务数据和本批失败证据；从现状继续，不重新 clone 覆盖、不 reset、不重新准备整套环境。

## 2. 用户已授权的范围

- 拉取并接管 Ceres2，配置与修复必要问题、使用真实模型与浏览器验收。现有 `.env` 已由用户提供配置，继续使用，不将 key 写入交接、日志或 Git。
- 本批 **跳过 Kev 自动分类**，使用已经发布的手动角色续接。不要再把 Kev 当作验收前置条件，不要伪造 classifier 输出。
- 主模型改为官方 `deepseek-flash`；本轮已将自动提取和 Dream 的模型配置也对齐为 `deepseek-flash`。
- 真实购物 → 模拟结算 → 同订单售后 → 返回新购物；中文品质、实际调用与 token、分段时延；独立新用例、准确 V3 基线对比。
- 真实记忆／Dream 先观察 **24 小时**，包含冷却和重启状态。先真实触发首次 Dream，再从其完成时刻计时。
- 价格、库存、订单、支付和退款始终是模拟业务；真实的是 provider 调用、浏览器操作和 SQL 持久化。

此前用户授权过一次 Git push，已在历史阶段完成。当前四处产品 dirty **尚未提交或推送**，本次交接没有新增推送指令。不要把原 Ceres 仓库当作写入目标。

## 3. 仓库、环境和精确版本

| 项目 | 本机交接值 |
| --- | --- |
| 用户项目路径 | `/home/amax/Documents/projects/Agent/Agent产品/Ceres2` |
| 实际工作路径 | `/data/amax/Documents/projects/Agent/Agent产品/Ceres2`，与上述 home 路径映射到同一项目 |
| 本机 HEAD | `4bed9c891261e382122d424825b649989ea92c92` |
| remote | `https://github.com/2061623884/Ceres2.git` |
| Python 环境 | 仓库 `.venv`，此前安装记录为 Python 3.11.15 |
| Node / npm | 此前本机记录为 Node 22.19.0 / npm 10.9.3；锁文件未为绕过安装而改写 |
| 已安装项目 skills | `.agents/skills/`，Matt Pocock skills 已在历史提交 `64cf509` 安装，不需要重新安装 |
| 浏览器 | 专用 Playwright 1.55.0 + Chromium 140；依赖留在本批 `tmp/preflight-20261006/browser-deps/` |
| 新版业务供给 | 标准 fixture，70 个 CatalogProduct／Offer |

先读根 `AGENTS.md`、`frontend/AGENTS.md`、TASK10 和对应 TASK／规格。实现由一个作者协调；测试、build、typecheck、安装与服务验证依项目约定由专职 Tester 执行，Standards／Spec 独立只读审查。不要为了改动不大的 Prompt 或 UI 无故重跑无关的全量 suite。

`AGENTS.md` 里“无 remote／禁止 push”等历史重建描述不反映当前已配置的 Ceres2 remote；实际授权与上面范围为准。旧接手文档的“需另行获得真实调用授权”也不应让 Cursor 对本会话已授权的每个正常步骤重复询问。

## 4. 必须保留的未提交改动

四处 production dirty，均未 commit：

| 文件 | 改动／真实依据 | 当前验证边界 |
| --- | --- | --- |
| `frontend/src/QuestionChoices.tsx` | 在 `onChange` 内立即保存 `event.currentTarget.checked`，不在 deferred state updater 里读取事件对象 | 仅这一处初修仍失败；和下一处一起才使真实 checkbox 保持选中 |
| `frontend/src/App.tsx` | `trackInteraction` 立即递增 epoch ref，父级 `interactionVersion` 更新推迟到 `setTimeout(..., 0)`；避免 capture render 在 native change 前重置 checkbox | 真实鼠标勾选、数量 6、清单／加购已发生；Space、多选、空数量与旧介绍取消尚需受影响回归 |
| `frontend/src/MercuryChat.tsx` | 同订单不重复 PUT；消费 order entry 清 prop 不重新初始化；ready generation 阻止初始化未完成时消费 handoff，并拒绝过期路由结果 | 修复后同一订单提案／明确提交已成功；需补延迟恢复、异单、关闭重开和无重放的受控回归 |
| `backend/app/prompts/experience.json` | 连接语不复述 host 下一步／确认／状态；另消除通用搜索与候选探索指引歧义，明确类别问题、商品数量、明确选定、比较分工 | 最新搜索指引尚未完成原公开饮水 case 回归；不证明语言或成本改善 |

当前审查时文件 SHA-256：

```text
frontend/src/App.tsx                  6c076c53b05190df53b279336a43568eba4382cc9bc490b48b8e6be2de17b3b6
frontend/src/QuestionChoices.tsx      3670b694d4e990896cdf6104c8d3b03a60d40a769f3d94c4d3299aab47b26b84
frontend/src/MercuryChat.tsx          b3f757445c34efdea62bb785a3ef395c2b5019635c224dc44610a885933e2896
backend/app/prompts/experience.json  b539cf35dd7fe98b58ae832a1c4e0ca5ad0afadab68146a1a5c60758a8ad5fa6
```

四文件 Merkle root：`b2fb596e64acb207ba288e5f578bac994f6d1e9fff6ee7b8b9776ff6504cdd7d`。算法、历史草案 P2 和纠正见 [Standards](../work/next-experience/live-acceptance/standards-live-fix-review.md)；[Spec](../work/next-experience/live-acceptance/spec-live-fix-review.md)亦无剩余静态阻断。**静态复核不等于受控测试或真实模型通过。**

另有 TASK01／03／05／07／09／10 文档修改、未跟踪的 `work/next-experience/live-acceptance/` 和历史 `work/live-validation/run_live_batch_deepseek_once.py`。先看 `git status --short` 与差异，不删除或把历史脚本当新版验收集。

## 5. 当前服务与数据隔离

最新只读服务／数据快照由 Tester 保存在 [cursor-handoff-snapshot.json](../work/next-experience/live-acceptance/cursor-handoff-snapshot.json)。**PID 是快照值，接管时先核对监听、cwd 和所属进程，不能按旧 PID 直接 kill。**

| 用途 | 后端 / 前端 | 最近已知 PID | 数据用途 |
| --- | --- | --- | --- |
| 用户日常应用 | `8012` / `8443` | backend `3366218`；Vite node `3366841` | 原有业务 DB，禁止拿它跑自动化验收 |
| 本批购物／售后 | `8013` / `8444` | backend `3552388`；frontend `3414992` | 独立合成用户、独立 DB／checkpoint／Chrome profile |
| 自然记忆 ownerB | `8014` / `8445` | backend `3589527`；frontend `3589534` | 另一套全新 DB／profile，专供自然提取与长期观察 |
| GPU1 Kev | `8009` | 早前发现 `2701504`，不要操作此进程 | 可达但普通购物分类有误；本批不接入 |

公开日常入口：`http://127.0.0.1:8443/`。聊天记录中的旧 `64396` 不是本次核实的常规入口。

购物运行目录：

```text
/data/amax/Documents/projects/Agent/Agent产品/Ceres2/work/next-experience/live-acceptance/tmp/acceptance-20261006T134938Z/
```

其中 `isolated-backend-launcher-nodeobserver.py` 安装只读用量观测器并启动 8013；`vite-isolated.mjs` 复用项目真实 Vite 配置，仅将 `/api`、`/media` 代理到 8013，前端为 8444。**backend launcher 本身没有设置隔离数据库环境变量**；重启时必须保留快照中的 `DATABASE_URL` 和 `MERCURY_CHECKPOINT_PATH`，不能仅照抄 Python 命令而落回日常数据库。

ownerB 专用运行目录：

```text
/data/amax/Documents/projects/Agent/Agent产品/Ceres2/work/next-experience/live-acceptance/tmp/memory-ownerb-20261006T160930Z/
```

其 backend launcher 为 `isolated-memory-launcher.py`，frontend 为 `vite-memory-isolated.mjs`，数据库 `db/business.sqlite3`，浏览器 profile `profile/chromium`，控制脚本 `memory-browser-session.js`。最后 browser harness PID `3591274`，Codex terminal session ID `53592`；Cursor 不应假设能复用 Codex 的 session 句柄，可读取控制脚本、保留 profile 后按需启动自己的驱动。现有 harness 没有在途动作，不要同时启动两个写同一 profile 的 browser 进程。

Tester 最后只读核对：8013 的两项 DB／checkpoint 环境字段均存在并落在该 run 的 `db/` 中。8014 的 `/proc` 初始环境里这两项缺省，但 `isolated-memory-launcher.py` 在应用导入前显式设置到 ownerB 的 `db/` 中；不能因 `/proc` 缺省就误用配置默认路径。确切路径与来源均在 snapshot 中，重启前按记录保留。

原 `.env` 模型配置已对齐三模型，但日常 8012 服务本轮没有完成配置重载确认，缓存中可能仍有旧记忆模型。由 Tester 在确认无活动 run、确属项目进程并保留 DB／checkpoint 后正常重载。`experience.py` 在启动时读取 JSON，**只改文件或前端 HMR 不会刷新已有后端的 MODULES**；8013 最后一次重载加载了此前介绍 Prompt，后续搜索指引的最新 b539… 仍须重载后确认适用版本。

`tmp/` 是 Git 忽略的本机私有执行目录。不要上传其中 DB、profile、cookie、原始未审核日志。停止测试不等于关闭应用服务；交接保留已启动服务与数据，由接手人按所属和静默状态处理。

## 6. 已实际发生的真实旅程

证据主目录为上述购物 run 的 `evidence/`，原始失败不覆盖：

1. 办公室 6 人、咸味零食、预算 ¥80、先看候选、不加购。先出现类型选择；选薯片后有真实模拟 35g／70g 卡片。一次性人数和预算没有被保存成自动长期偏好。
2. 真实 checkbox 被 capture 更新重置；初修失败和后续修复 GREEN 保留。选 70g 袋装、6 袋，¥5.90 × 6 = **¥35.40**；生成清单没有加购，独立点击确认后 cart 数量 6、purchase ledger 1。
3. 独立 checkout preview 和明确“确认模拟结算”均 HTTP 200。新订单 `sim-f837f1ee388540b3b72cd54a1d5cf368`，6 袋、3540 分，打开详情并联系墨墨。
4. 首次手动同角色续接并发重复 PUT order 409，前端显示没有订单；服务器 case 实际仍选中同单且资格查询完成。无 proposal／application／receipt。失败见 `primary-journey-final-summary.json`、step45/46。
5. 修复后正常重载、同 profile 恢复，没有重放查询。新请求说明会议临时取消、未发货、**先准备整单提案，不提交**；得到同单、6 袋、¥35.40、`P-REF-01` 的待确认提案。
6. Tester 后续独立点击“确认提交此模拟申请”，confirm HTTP 200；申请 `requested`、整单 refund 3540 分、回执 1 条，未审批／未到账。step51–53。确认 CTA 本身没有完整独立截图，只保留真实按钮定位点击／200／前后帧；将来 fresh 旅程补证，不重发旧申请补图。
7. 售后介绍失败，页面明确“介绍未完成，申请回执已保留”；业务没有重复提交。安全 diagnostic 的具体 code 尚需从既有去敏日志补齐，不推测。
8. 明确返回可可后无重放。新请求原句：

> 薯片采购已经结束，这是一个新的目标：请为下周办公室准备一箱饮用水，预算不超过100元。先给我两个真实可买选项和包装、价格、库存，不要加购。

此新请求实际 `guide_request` 成功，之后 `search_products` 连续四次成功，达到 5 轮保护；`protected / tool_budget / answer_status=failed / committed=false`，没有候选。step60。旧参数和每次 host result 未持久化，只知工具顺序，缺项记 unknown。

购物 run 最后已读回：cart 0、模拟订单 1、checkout receipt 1、售后 proposal／application／receipt 各 1；没有活动 run。角色返回成功，**新购物目标失败**。这条旅程跨修复与不同已加载 Prompt，不能称同一冻结版本的完整通过。

## 7. 刚发现、尚未实施的 DeepSeek 请求修复

官方文档确认 `deepseek-flash` 默认启用 thinking，默认 effort 为 high；Chat Completions 可用 `thinking: {type: 'disabled'}` 关闭，OpenAI Python SDK 经 `extra_body` 传入。[官方 Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)、[Chat Completions 参数](https://api-docs.deepseek.com/api/create-chat-completion/)。

本机 Pi SDK `runtime/pi/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js` 约 668 行，仅在 `compat.thinkingFormat === 'deepseek' && model.reasoning` 时自动发送 thinking 字段。当前 worker／expression 把 model 声明成 `reasoning: false`，所以 `thinkingLevel: 'off'` 没走这段关闭逻辑。SDK 后面 `resolveSamplingParams`／`Object.assign(params, samplingParams)` 支持将实际请求参数传下去；这是源码阅读结论，**尚未做 wire-payload 验证**。

须覆盖所有真实调用方，不只改主回复：

| 调用路径 | 入口 |
| --- | --- |
| 可可主循环 + 普通知识 claim validator | `runtime/pi/src/worker.ts`，两个 `streamSimple` 调用 |
| 结果介绍 generator + validator | `runtime/pi/src/result-expression.ts`，两个 `streamSimple` 调用 |
| 墨墨主模型 | `backend/app/mercury/provider.py` 的 `QueryChatClient.chat` |
| 自动提取 + Dream | `backend/app/services/memory_model.py` 的共同 `_call` |

建议做**官方 DeepSeek profile 的最小 transport 修正**：Node 实际 request sampling 参数发送 `thinking: {type: 'disabled'}`；Python 官方地址调用传 `extra_body={'thinking': {'type': 'disabled'}}`。保持非 DeepSeek provider 的当前兼容行为；不要盲目向所有 endpoint 塞专属字段，也不要修改已安装 node_modules 作为交付。可用现有官方 hostname 判断或经验证的 SDK compat 路径，选一个小实现，别加无调用方配置系统。

验收此修复应由 Tester 在 controlled transport 中核对实际安全字段 `thinking`／`reasoning_effort`／`max_tokens`，四类路径都发送了目标 profile；记录 `finish_reason`、reasoning token 数等纯元数据（服务商未给就 unknown），**不打印 key、headers 或隐藏思考正文**。再做少量真实同输入回归。不要用抬高 1536／512／256 输出额度、放宽 5 轮／30 秒或增加重试掩盖问题。

1536 恰好打满但尚无 finish_reason／reasoning_tokens 证据，因此“思考占尽输出导致截断”目前是有源码和官方默认行为支持的**待验证推断**，不是已测定全部失败的因果结论。

## 8. 真实记忆／24 小时观察的交接状态

ownerB 已有独立 8014／8445 环境。最新完整状态以 Tester 快照为准；截至已回报的前两轮：

| 轮次 | 真实结果 | 已报告用量 | 自然记忆 |
| --- | --- | --- | --- |
| 稳定偏好首轮 | `PI_ANSWER_INVALID`，应用 502，provider HTTP 200；只有 accepted／understanding／error | 一次 Pi main：input 3222、output 1536、total 4758 | 没有提交 Guide message／extract job／automatic memory |
| 不同稳定事实＋明确无糖茶查询 | `PI_ROUTE_INVALID`，应用 422；provider 三次 HTTP 200 | 三次 total 3304／5105／5396 | 没有自然 extract／automatic memory |

只读交接已确认未发送第三条；ownerB 共 **4 次 Pi provider 调用、18,563 tokens**，Guide messages／extract jobs／automatic memories／Dream 均为 0。三个数据库的活动 guide runs、pending/running memory jobs 都为 0，观测器无未终态 provider call。不要把这两轮失败计成有效记忆，不靠手动插入记录、改时钟或强制调用 Dream 凑阈值。

观测器 [memory_watch.py](../work/next-experience/live-acceptance/observers/memory_watch.py) 已写好、Tester 的 AST 验证通过，**尚未启动**。它仅 mode=ro 查询隔离 SQLite，记录无正文的 job／revision／expiry 元数据；从实际首次 completed Dream 的 `completed_at + 86400` 观察冷却，默认 300 秒采样、临界窗口 5 秒，并留 600 秒完成宽限。它不调用模型、不调度、不改 SQL、不替代应用的 MemoryWorker。

继续步骤：修 provider profile → 正常提交合成用户的自然持久偏好 → 等真实 extraction → 自然满足至少 **10 条有效、未被 explicit/tombstone 遮蔽的 automatic 记忆** → 等首次真实 Dream 完成 → 冻结 baseline job ID／完成时刻 → 启动 detached 只读观察器并记 PID／北京时间 deadline。正常重启专用服务，保留 DB、checkpoint、profile、job ID 和来源；验证冷却内不提前 Dream、没有自动重放。

明确更正／删除及来源权威另用 ownerA，避免改变连续观察 ownerB 的阈值；first Dream 无历史时可立即 eligible，24 小时是**距上次成功 Dream**的冷却，不是新用户先等待一天。30 天过期不属于本次选择的窗口。24 小时实际经过前，始终记进行中，不给提前通过结论。

## 9. 独立新用例与 V3 基线

### 独立新用例

- 已由独立验收 agent 编写、冻结 **5 个**新用例，尚未执行；主实现者没有读取正文或用它调 Prompt。
- 文件：`work/next-experience/live-acceptance/holdout/cases.json`；SHA-256 `526446632dc58c48fa80e88a5e27a0efad01c3eec7c0b37bccb60e10a4026ff8`。
- 中文 rubric：同目录 `language-rubric.md`；SHA-256 `478be0f49d0301e8c2632b2f00521d86a8319ad0f3be5a122c300089676317b9`。六维 1–5，目标平均 4.0。
- 先冻结修正候选，再交独立执行者解封；实现者继续不预读正文。首次结果失败也保留，修复后同集只算回归，不改称新 holdout。每个 case 用 fresh DB／fixture／profile，只有新 owner 不会重置库存。

### 用户已经确认的 V3

- 原仓库 `https://github.com/2061623884/Ceres`，**用户明确指定 `df2930d` 就是 V3**。不要重新要求用户证明版本，也不用浮动 main 代替。
- 完整 commit：`df2930d47e4ba999355f7049e8269166e5258006`，tree `aa453851204bcda47d0514b68e53098dd3d3f40b`。
- 只读 detached 源码：`work/next-experience/live-acceptance/tmp/v3-baseline-df2930d-20261006/`。
- 尚未安装该基线的新依赖或执行新的 V3 比较。基线中的历史 07 记录绑定另一 source ZIP／commit，不能借来算本次 df 已验证。
- 来源、fixture hash、API／模型环境、比较限制见 [baseline-provenance.md](../work/next-experience/live-acceptance/baseline-provenance.md)。独立临时 runner、新 venv、全新合成 DB、`seed_runtime.py --fixture-only`；不要在只读目录安装或复用原 `.venv`、旧 DB、订单、checkpoint、`.env`。
- 35g 薯片在该 V3 fixture 不存在，价格／数量相关项应 not comparable，不偷偷改成 70g。500ml 苏打水有同 SKU、450 分／库存 60，可作准确同供给比较。未知过敏证据始终未知。
- 两版固定同 provider／model／thinking profile 后比较，明确这不是重现 V3 历史 Qwen 配置；必要的 runner transport adapter 单列。V3 路由与本批跳过 Kev 不可直接比较。

## 10. 中文、用量与证据入口

[primary-path-language-review.md](../work/next-experience/live-acceptance/primary-path-language-review.md) 已保留独立可见样本评分：初始候选 3.8；清单 3.8；加购介绍 3.7；售后暂态错误屏 3.5；提案 4.0；确定性回执面板 4.5；新购物上限错误文案 3.0。这些是分段样本，不能平均拼成整体通过；确定性面板也不是生成语言效果。

模型连接语有生硬 filler，host receipt 与 intro host facts 也存在重复。先修 profile 并取得加载版本明确的真实新样本，再决定最小语言修改；不删政策来源、模拟／未知状态、确认边界或“申请提交≠到账”来调高分数。售后介绍失败还没有有效生成文字可评分。

本批用量观测器：`observers/provider_usage.py`、`observers/node_usage.mjs`；只记录实际返回的 numeric usage、调用类别、model 和时间，保留原请求／响应。worker 的 env 本来经过过滤，Python observer 仅对指定 Node worker 添加两项观察变量。最早主调用用量不可恢复，标 **unreported**；不同 observer 与现有 expression.metric 同一 call 去重，不把 cache hit 再加进 input，总量缺项不计零，SDK 零费用不是账单。

关键本机证据：

- 购物 run `evidence/primary-journey-final-summary.json`：首次部分旅程与原 409、计数／用量／版本限制，不覆盖。
- `backend-momo-fix-reload-record.json`、`source-model-freeze-momo-fix.json`：重载与此前实际适用 source/config。
- step31／32／34：勾选、数量、清单；step40／41／42：结算及新订单；step45／46：原售后失败；step47：只读恢复；step50–53：新提案／回执；step54–60：返回与新目标失败。
- ownerB 专用目录／失败帧／metrics：由交接 snapshot 给出准确路径。
- 旧云端 `0c752a2` 的 426 backend／37 DOM／build／restart 证据是历史精确候选的受控结果；旧 41/41 live 是旧阶段 API batch，均不能继承为当前 dirty 完整验收。

## 11. Cursor 按此顺序继续

1. 读取本文件、TASK10、AGENTS 和 Tester 交接 snapshot；核对 worktree dirty 与 owned 端口，保留现有状态。当前不会有 Codex 主动继续收费测试。
2. 先修／验证官方 DeepSeek **实际请求关闭 thinking**，覆盖 Pi 主／validator、intro 两路径、Mercury、提取／Dream；不改模型 ID，不抬保护额度追成功。新 source＋实际加载 Prompt＋模型参数重新 freeze。
3. 由 Tester 先做两个 ownerB 已失败路径和公开饮水原句的有界回归；收集真实 tool 顺序、必要安全参数和终态元数据。若仍失败按证据定位，不连续换同义句追 pass。
4. 能自然提取后优先启动 first Dream／24 小时观察，专用 8014 服务保持运行。其间在另一套隔离服务跑其余验收，不能切 DB 或停掉观察源。
5. 完成受影响检查：native pointer／Space、数量／多选、stale intro；Mercury 延迟恢复／同单／异单／entry消费／重开；Prompt 的探索／事实问答／明确选择／比较／复合政策／无或少供给；相应 frontend/runtime build／strict TypeScript 和公开协议回归。新增必要回归须有旧版 RED、新版 GREEN。
6. 同一冻结新候选 fresh 真实浏览器完整旅程，补确认 CTA 在视口中的截图；看到结果后才能确认，各阶段读回差分。退款整单必须省略 `item_id`，原因明确；回购物重新读取目标供给，申请／订单／加购无重放。
7. 解封独立 5-case、执行准确 df2930d V3 对比、独立中文复核与真实调用／token／浏览器延迟汇总；耗时准备不算模型 SLA，30／15 秒保护也不是 SLA。
8. 实际 24 小时经过后核冷却与重启状态、更正删除和来源权威；记录缺证据／失败，再提供用户本人可审阅的完整结果。TASK10 保持待验收，条件未满足不签已验收。

所有模型修复和新测试均从这个真实未完成状态继续；文档交接不代表验收完成。
