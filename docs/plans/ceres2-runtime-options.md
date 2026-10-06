# Ceres2：真实 Pi + LangGraph 的集成选项

核查：2026-10-05 UTC。状态：研究提案，等待架构取舍；不是实现规格或验收结果。

## 结论与决策边界

最新方向是**售前实际使用 Pi Agent Runtime，售后实际使用 LangGraph；不限定 Python，保留业务能力和语义，不要求保留代码**。因此旧研究中“先仅借鉴 Pi、仍以原 LangGraph 售前为主”的建议不再是本方案。Pi 的包必须进入真实售前运行链路，不能复制其循环后仍称采用 Pi。

两个主选项均可行：

- **A：FastAPI 业务主机 + Node Pi worker + Python LangGraph 售后。** 现有业务代码复用最多，但新增一个必须认真设计的进程边界。建议作为当前最小交付候选，理由是已经存在的价格、数量、版本与事务行为迁移成本，不是 Python 优先。
- **B：统一 TS 业务后端 + Pi + LangGraphJS。** 避免运行时跨语言 RPC，JS 的 interrupt/SQLite/Postgres saver 都真实存在；代价是重写并重新证明业务账本、检索、确认和迁移行为。若未来部署明确只接受 Node，或团队愿意承担这次业务迁移，B 完全成立。
- **C：TS Pi + LangGraphJS，暂留 Python 业务主机。** 也是技术上可行的过渡，但售后提交也跨 RPC，语言和运维仍有两套；除非 LangGraphJS 与统一 TS orchestration 本身是目标，否则比 A 多一处风险而未消除 Python。

本次未安装/运行上游代码，未启动服务或测试，未读取密钥和活动数据库。只阅读本地源码、官方源码和包元数据，新增本文。执行性能、目标 provider 的真实兼容性、native SQLite 安装、端到端恢复均未验证。

## 1. Pi：包、源码与真正可调用的接口

### 1.1 固定源码与发布版本不能混为一谈

前轮 Pi 源码固定在 [`1cbc7a0e8ea66e751e84c2b91183f06bd3fb5069`](https://github.com/earendil-works/pi/commit/1cbc7a0e8ea66e751e84c2b91183f06bd3fb5069)。该快照 manifest：

| 实际依赖 | manifest 版本 | 重要条件 |
|---|---:|---|
| `@earendil-works/pi-agent-core` | 1.0.3 | ESM；公开根入口 `dist/index.js`；Node >=22.19.0；依赖 pi-ai ^1.0.3、typebox 1.3.27 |
| `@earendil-works/pi-ai` | 1.0.3 | 根入口、`./models`、`./api/*`、`./providers/*` 等公开 exports；根入口不自动注册 provider |

本次直接读取 npm 官方 registry 的 [agent-core 1.0.3 元数据](https://registry.npmjs.org/@earendil-works/pi-agent-core/1.0.3) 与 [pi-ai 1.0.3 元数据](https://registry.npmjs.org/@earendil-works/pi-ai/1.0.3)：两包均存在，registry `gitHead` 是 **`d78dc83d633229d12f8b79631384c4c2717c399f`**，不等于前轮 main SHA。逐字节比较两个 SHA 的 agent types/agent/index 与 ai models/index/OpenAI completions transport，一致。下列实现接口以这个发布来源 SHA 为引用。

这证明发布元数据与核心源码接口可对应，**没有下载或运行 npm tarball、没有证明安装成功**。实现时固定两包 exact 1.0.3 和 lockfile integrity，不让 core 的 `^1.0.3` 自动决定 ai 版本；不是安装旧教程里的 `@mariozechner/pi-agent-core`，也不从 monorepo 根执行未知 build。

源码：[agent manifest](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/agent/package.json)、[ai manifest](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/ai/package.json)、[agent exports](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/agent/src/index.ts)。

### 1.2 真实集成形状

- `import { Agent } from '@earendil-works/pi-agent-core'`；构造参数 `initialState` 加 **`streamFn`**。当前公开类型要求 streamFn，不能套旧版只 `new Agent()` 的示例。
- `createModels()`、`createProvider()` 来自 `@earendil-works/pi-ai`；`models.setProvider(...)` 注册 provider，`models.getModel(providerId, modelId)` 取配置模型；`streamFn: models.streamSimple.bind(models)` 交给 Agent。
- `Agent.prompt(...)` 执行真实 Pi 循环；`subscribe(...)` 消费事件；`abort()` 请求取消。自建适配器只做领域工具、上下文、事件和传输映射，不重新写 Pi 的模型工具循环。
- `AgentTool` 是有 `name/description/parameters/label` 的声明；参数 schema 是 `typebox` 的 TSchema。执行接口为 `execute(toolCallId, params, signal?, onUpdate?) -> Promise<AgentToolResult>`；result 有模型可见 `content`、宿主 `details`，可有 `structuredContent/isError`。失败必须抛错或 `isError:true`，不能只在文本中说失败。
- **没有 owner、session 或数据库事务的 execute 参数。** 每次运行创建工具闭包，捕获宿主授予的不可变 run handle。模型参数只包含商品/查询/建议参数，不包含可信 owner、授权签名、lease 或确认状态。`beforeToolCall` 的 `context` 是对话和工具上下文，不是身份系统。
- 默认 `toolExecution` 是 **parallel**。首个可验证切片显式使用 `toolExecution:'sequential'`；工具可通过 `executionMode:'sequential'` 强制整批顺序。串行只减少同一 Agent 一批工具的交错，不能替代跨请求 CAS、数据库事务或幂等。
- `beforeToolCall` 在参数校验后可返回 block；它适合预算/取消闸门，但不能成为唯一业务授权。宿主执行工具及最终提交仍要验证。同一批中其他工具可能继续，因此不能依赖一条 blocked tool 自动阻止所有后续动作。

源码：[Agent/AgentOptions](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/agent/src/agent.ts)、[AgentTool、ToolExecutionMode、AgentEvent](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/agent/src/types.ts)、[Models/createProvider](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/ai/src/models.ts)。

### 1.3 模型配置与 OpenAI-compatible base URL

当前 `openaiProvider()` 默认选择 **Responses**，不应把现有 Chat Completions-compatible 地址塞进去并假定兼容。明确方案是：

1. 导入 `openAICompletionsApi` 自公开子路径 `@earendil-works/pi-ai/api/openai-completions.lazy`。
2. 使用 `createProvider({id, baseUrl, auth, models, api: openAICompletionsApi()})`。静态 model 完整提供 id/name/api/provider/baseUrl、输入类型、reasoning、cost、contextWindow、maxTokens 等必需字段，数值由实际配置决定，不伪造模型能力。
3. `auth.apiKey` 可用根入口导出的 `envApiKeyAuth` 接入该 worker 被显式授予的服务端 key；或使用宿主明确配置的 AuthContext。Pi provider 的 auth 是 **模型供应商凭证**，不是商城用户身份。
4. OpenAI completions 实现实际使用 `new OpenAI({apiKey, baseURL:model.baseUrl,...})` 并传递 abort signal；模型的 `compat` 决定 max_tokens、流式 usage、reasoning 等差异。用现有 provider 做 contract smoke 后才宣称兼容。URL/key/model 由部署配置选择，模型不能改地址或 headers。

源码：[lazy API](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/ai/src/api/openai-completions.lazy.ts)、[transport](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/ai/src/api/openai-completions.ts)、[auth helper](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/ai/src/auth/helpers.ts)、[默认 OpenAI provider](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/ai/src/providers/openai.ts)。

### 1.4 事件与终态

Pi `message_update` 中的 `assistantMessageEvent.type === 'text_delta'` 可映射现有文本增量；tool start/update/end 可映射安全的业务进度。不得把原始 args、完整私有 details、内部 prompt 或凭证透传 UI。Pi 的 `turn_end` 是一次模型响应及其工具结果，不是 Ceres HTTP 回合提交；`agent_end` 也不是业务提交凭据。Ceres `turn.completed` 只能由已落库的宿主回执生成。

`abort()` 是合作式取消，工具必须传播 `signal`，IPC 必须独立传 cancel。它不能撤销已提交事务，worker exit 也不能证明业务失败。Pi Agent 状态为运行时上下文；不把它当可恢复业务账本，不为此引入 experimental Pi durable。

## 2. LangGraphJS 不是 Python API 的同义翻译

本次通过公开 git HEAD 固定 JS 源码 [`1cee82d0c48fbaeb2d71433211b03113992cc114`](https://github.com/langchain-ai/langgraphjs/commit/1cee82d0c48fbaeb2d71433211b03113992cc114)，再按 SHA 读取文件。

| 功能 | JS 实際公开接口 | Python 对照 |
|---|---|---|
| 图与恢复 | `StateGraph`、`interrupt`、`Command` 来自 `@langchain/langgraph`；`graph.invoke(new Command({resume: value}), config)` | `langgraph.graph.StateGraph`、`langgraph.types.interrupt/Command`；`Command(resume=value)` |
| 编译与线程 | `.compile({checkpointer})`；`{configurable:{thread_id}}` | `.compile(checkpointer=...)`；config dict |
| SQLite | `@langchain/langgraph-checkpoint-sqlite`；`SqliteSaver.fromConnString(path)`，使用 better-sqlite3；内部按需 setup/WAL | `langgraph-checkpoint-sqlite`；`SqliteSaver.from_conn_string(...)`；另有 AsyncSqliteSaver/aiosqlite 路线 |
| Postgres | `@langchain/langgraph-checkpoint-postgres`；`PostgresSaver.fromConnString(...)`；首次显式 `await saver.setup()`；pg Pool | `langgraph-checkpoint-postgres`；PostgresSaver/AsyncPostgresSaver，psycopg 路线 |
| 生产权限 | 两端都必须由应用验证 owner→case→thread 映射 | thread_id 不是凭据，也不是 approval |

固定源码 manifest：真正的发布主包位于 `libs/langgraph-core/package.json`，名称 `@langchain/langgraph`，版本 **1.4.19**；`libs/langgraph/package.json` 是 private 转发包，不能错把其中 1.0.47 当主依赖版本。SQLite saver manifest 1.0.4，better-sqlite3 ^12.10.0；Postgres saver 1.0.5，pg ^8.12.0。两 saver peer 要求 `@langchain/core ^1.1.44` 和 checkpoint ^1.1.4。上述三个版本也已通过 npm 官方 registry 逐个读取元数据确认发布存在（[主包](https://registry.npmjs.org/@langchain/langgraph/1.4.19)、[SQLite saver](https://registry.npmjs.org/@langchain/langgraph-checkpoint-sqlite/1.0.4)、[Postgres saver](https://registry.npmjs.org/@langchain/langgraph-checkpoint-postgres/1.0.5)）；这些元数据没有 gitHead，故不宣称 tarball 与所读 SHA 逐字一致。不能以“有包”声称本平台 native addon 已能安装。Pi 的 Node >=22.19.0 已比主包引擎下限更高，仍须核对部署架构与 native binding。

JS interrupt 源码依赖 graph execution context/checkpointer；未提供恢复值时抛 GraphInterrupt。恢复会重跑节点开头，**interrupt 以前不得放不可幂等提交**。JS 的 `responseSchema` 使用 Zod，不能照搬 Python `response_schema`/Pydantic；本方案不依赖新的 schema 扩展，宿主照常验证确认载荷。checkpoint 表、序列化和语言类型不能假定跨语言可互换，若由 Python 转 JS，应显式迁移/终结旧 case，不能直接让新 saver 读取旧格式。

本项目当前售前 Python 图每 HTTP 请求新建一轮，没有 checkpoint；Mercury 当前也没有成熟持久图。因此采用 LangGraphPython 不等于已有售后 checkpoint 可直接复用，A/B 都要新增 case、approval 和业务 receipt；B 只是再加上现有服务的端口迁移。

来源：[JS interrupt 官方文档](https://docs.langchain.com/oss/javascript/langgraph/interrupts)、[JS interrupt 源码](https://github.com/langchain-ai/langgraphjs/blob/1cee82d0c48fbaeb2d71433211b03113992cc114/libs/langgraph-core/src/interrupt.ts)、[JS 主包](https://github.com/langchain-ai/langgraphjs/blob/1cee82d0c48fbaeb2d71433211b03113992cc114/libs/langgraph-core/package.json)、[SQLite](https://github.com/langchain-ai/langgraphjs/blob/1cee82d0c48fbaeb2d71433211b03113992cc114/libs/checkpoint-sqlite/src/index.ts)、[Postgres](https://github.com/langchain-ai/langgraphjs/blob/1cee82d0c48fbaeb2d71433211b03113992cc114/libs/checkpoint-postgres/src/index.ts)、[Python interrupt](https://docs.langchain.com/oss/python/langgraph/interrupts)、[Python persistence](https://docs.langchain.com/oss/python/langgraph/persistence)。

## 3. A 与 B 的真实成本

| 维度 | A：Python 业务主机 + Node Pi | B：TS 后端 + Pi + LangGraphJS |
|---|---|---|
| 售前自主循环 | 换为真正 Pi；Python 旧语义编排不再在外层预先决定所有工具 | 同样真正 Pi；工具本地调用 TS 服务 |
| 现有交易语义 | 保留 Confirmation/Cart/Receipt/CAS，并抽离旧 graph 偶合 | 重写同语义事务与唯一约束，重新证明所有竞争和恢复场景 |
| 商品/菜谱检索 | 可继续读取已有 index、过滤、来源证据与计量逻辑 | 移植 embedding/index/readiness/缓存契约，或临时再保留 Python 检索服务 |
| 运行边界 | Node 与 Python JSON 协议，worker 生命周期、取消、backpressure、错误转换 | 同进程调用简单；异步 JS 并发仍需数据库串行化/事务，不自动更安全 |
| 售后 | Python LangGraph 就地调用调整后的 Mercury 服务；仍需审批账本 | LangGraphJS 就地调用新 TS 售后；需迁移 Python sqlite3 资格/金额/事务 |
| 数据迁移 | 以新增表/授权改造为主；不换 ORM，不双写 | 选择 TS DB adapter、schema/金额/时区规范、迁移和回滚；旧数据不能 reseed |
| 运维 | 两语言、两依赖集、一个外部 API 主机；单机 stdio 最小 | 一套 Node 部署；native SQLite/checkpoint 包仍有自身运维；不能直接复用 Python 测试 |
| 未来纯 TS | 可按领域替换 Python，不必同时重写业务 | 起步成本高，但满足纯 Node 部署且避免长期 bridge |

**为何 A 当前领先：** 本次最难保护的是约束和数量换算、计划版本、旧回合隔离、确认加购、receipt 与副作用同事务；这些在当前 Python 有具体实现。维护一个窄只读/提案桥，比同时搬迁全部业务具有更小的行为变化面。若完整服务审查发现大部分旧实现本就需要替换，或部署不能运行 Python，这个理由会减弱，应选择 B，不能把复用当成不可修改的原则。未做基准，不能声称 A 更快/更便宜，也不能声称 IPC 是主要延迟。

### 应复用/改造而非照搬的服务

- 保留 `CatalogService/OfferService/DeliveryService` 的权威查询；SKU、金额分、库存和配送来自服务，LLM 只选择查询。
- 保留 `RetrievalService` 的过滤/索引版本/证据以及 plan 的计量和验证服务：`ShoppingPlanService`、`PlanValidator`、`PlanCommitService`、`PlanRevisionService`、`PlanRefreshService`。它们承载业务，不因为改 Agent 就重写。
- 保留 `ConfirmationService`、`CartService`、`TurnReceiptService`、`TaskLifecycleService` 的事务和并发语义；抽离 `commit_graph_turn` 内必要领域提交能力，使其不要求旧 LangGraph state。**不**把现有整个 `decide_turn`/goal_router 包成一个 Pi tool，这会让 Pi 成装饰。
- 保留 `MemoryService/ShoppingMemory` 的 owner、来源与 explicit 优先约束；回合提案可进入确定性更新边界，不把模型抽取结果自动当长期授权。后台 extraction 的持久性是否升级另定，不能借 Pi 声称恢复已实现。
- Mercury `services.py` 的资格和金额逻辑有复用价值，但必须调整内部自行 connect/commit，使 business write 与新 operation receipt 处于同事务；修复入口 demo owner fallback、case ownership，不能原样封装旧 create 工具。原无确认自动 write tool 不暴露给 Pi 或售后模型。

本地证据：`work/ceres2-upgrade/research/presales-audit.md`、`mercury-data-audit.md`；并复读 `agent/graph/coordinator.py`、`turn_receipt_service.py`、`task_lifecycle_service.py`、`confirmation_service.py`。工作树存在其他进行中变更，本报告不将它们计作本次修改/通过。

## 4. A 的最小可实施进程边界

### 4.1 默认单机 stdio，不新增匿名内部 HTTP

FastAPI/Python 是唯一外部 API 和业务 authority。它启动受控 Node child，继承专用 stdin/stdout pipe；Node 只做 Pi/模型传输，Python 响应工具请求。stdout 专用于有界 JSONL 帧，诊断走 stderr；无需开放端口或让浏览器访问 worker。固定协议版本，字段长度/帧界限、超时取既有请求预算，不能无限缓存输出。

首切片优先一个运行一个 child，天然隔离会话/闭包；代价是 Node 启动开销，须实测能否满足原延迟目标。若实测不行，再改预热 worker/pool：需要明确 run multiplex、清理 transcript/listener/credential、跨 owner 泄漏测试和任务分配上限，不预先搭复杂 worker 平台。

stdio 不是沙箱：child 继承多少环境、文件和网络权限由主机决定。仅提供本次模型配置/必要运行环境，不授予业务 DB 路径、管理凭证、通用 shell/file tools；OS 层隔离如需强保证另行配置，不能靠 tool allowlist 声称已沙箱。

如果确定部署需跨机器或独立扩容，才选择 HTTP/RPC：仅绑定私网/Unix socket，加服务身份认证（例如部署密钥或 mTLS）、请求大小/超时和连接生命周期；worker 与 host 的身份是部署注入，不能由 LLM 创建签名。**localhost 本身不是认证**；禁止新增无鉴权 `/internal/tools/execute` 并以“内部使用”为由放行。

### 4.2 有限协议，可信字段不出现在模型 schema

以下为待实现的业务协议，不是 Pi 自带 RPC：

| 消息 | 方向 | 核心内容和责任 |
|---|---|---|
| `run.start` | host→worker | protocol_version、opaque run_id、用户文本、已裁剪上下文、工具白名单、相对剩余 deadline/预算；host 私有保存 owner/session/request/digest/reservation/原始 anchor |
| `tool.call` | worker→host | run_id、call_id、tool_name、validated args；host 从 active-run registry 查可信上下文；模型不能改 run_id，服务不信 worker 传的 owner/version |
| `tool.result` | host→worker | call_id、ok/error code、模型可见 evidence/provenance 与必要结构化结果；不发送 lease、审批 token 或 DB 对象 |
| `run.event` | worker→host | run_id、单调 seq、已过滤的 Pi 事件；仅显示进度，不证明写入 |
| `run.result` | worker→host | 只读回答/候选、领域 proposal、引用到本次真实 tool evidence 的 IDs；host schema/授权/版本验证并自行生成业务事实 |
| `run.cancel` | host→worker | run_id、原因；worker `Agent.abort()`，host 自身同时阻止新工具和提交 |
| `run.error` | worker→host | 可分类 provider/tool/protocol/abort 错误，保留可审计原因，用户文案不泄露内部数据 |

只暴露真实需要的领域能力：查询商品/菜谱/报价/当前购物状态/允许的记忆；必要的“准备计划”是无副作用计算或返回待提交 proposal。worker 不能自行 `add_cart/create_refund/create_return/confirm`。即使有领域草稿需要持久化，也由 host 在本回合确定性提交阶段写，不能工具每调用一次就 commit 一次。

### 4.3 一次请求和 anchor 的保全

1. host 在运行 Pi **之前**验证 owner/session 和 client expected versions，检查 completed receipt，reserve `(owner,session,request_id,digest)`，捕获原始 task/session/state anchor。
2. host 保持该 anchor；之后查数据库可以更新展示事实，不能把新查到的当前版本当作原回合授权版本。另一请求的编辑/换任务/确认使旧 run 提交失败；只有本回合已获准的自身提交可按现有语义推进 anchor。
3. 不把跨进程运行当持锁长事务；工具只读用按请求/调用管理的 session，SQLAlchemy Session 不跨线程共享。最终进入短事务重验原 anchor/CAS、预算/取消、有效 business references 与纯业务 authorization。
4. 提案、计划/context/messages/snapshot 和 TurnReceipt 的完成在同一业务 commit 边界；模型输出不是完成证明。确认加购继续经 `ConfirmationService`：owner+task+plan/version+selected quantities+价格/库存/配送再验，与 cart operation receipt 保持原子性。
5. 即使 run.result 携带“用户同意”也不能据此生成 approval。直接复用现确认端点；若产品要自然语言确认，host 还须有精确版本/选择绑定的可信确认入口，其语义需产品决定。

### 4.4 取消、重试、故障与串行的真实限制

- HTTP disconnect/deadline/用户停止：host 立即标记 run 不再可提交，发 cancel；工具/模型合作停止。Node 挂死可由 supervisor 终止，但不能将进程结束解释为业务 rollback。
- 同 call_id 的只读工具若允许重试，绑定同一 run、原参数和 evidence；不使用框架自动 retry 来重放副作用。主机对 late event/result 丢弃或记录，不能让已取消 run 的晚到文本触发写入。
- worker 在结果返回前退出：不盲目重启同一请求并跑一次；按现 TurnReceipt 失败/unknown 契约处理。现服务明确未完成未知结果不接管重跑，Pi 引入不能静默改变它。
- host commit 后、worker/UI 收到结果前掉线：读 committed receipt 返回同一结果，不再调用模型或业务写入。
- 不把一个“串行 Pi”当作全局锁；两个浏览器请求、确认请求、后台工作仍可竞争，最终 CAS/unique keys/ledger 为准。

## 5. 售后 LangGraph 与业务批准的边界（A/B 共用语义）

图负责阶段：查单/解释/收集信息→准备 proposal→等待批准 interrupt→资格重验→确定性业务提交→按 receipt 答复。外部确认入口先做 owner/case/thread/proposal version 校验，再以内部 decision reference 恢复图；不能让浏览器任意 `Command(resume:true)` 或让模型 tool 假造确认。

proposal 固定 order/item/整行数量/金额/原因/规则版本，approval 绑定其不可变版本。节点恢复会重放节点开头，所以提交节点读 operation receipt 后再决定是否写；refund/return 和 operation receipt 必须同事务。graph checkpoint 写入与业务 commit 分别发生，不能声称二者天然原子；“业务已提交、checkpoint 未记”靠 receipt 恢复。

人工接管要在业务 case 持有 bot/human owner 或 generation fence；仅暂停图不够，已在途 bot 提交仍需检查最新 ownership/version。确认、人工接管、改订单、新 proposal 都要让不适用旧授权失效。既有退款/退货是模拟申请 pending/requested，不是真实打款或履约。

## 6. 哪些决定真正阻塞，哪些不应再问用户

### 产品/部署必须明确

1. **部署约束：** 允许单机 Python+Node 两进程吗？如果必须纯 Node/单 runtime，直接 B；否则 A 是最小行为变更候选。多 worker/跨机器要求会影响 IPC 和 DB，但不能无依据预建平台。
2. **售前主动性：** 首次交付只需对话内多步查找/主动建议，还是离线持续任务？后者必须明确一个触发器、持久 job、授权/取消和通知目的地；Pi core 不提供这些业务语义。
3. **确认与人工：** 售前是否保留按钮精确确认；售后是否必须展示 proposal 再确认、人工接管是否需要真实工作台及角色权限？旧 Mercury 自动 create prompt 与新批准目标冲突，不能两个都保留。
4. **订单桥：** 本次是否包含 Ceres checkout→服务器模拟订单→Mercury 可查？若包含，必须决定权威订单来源和 owner 映射；不以前端 local order 或双库普通 commit 充当可靠桥。

### 工程可以自行验证，不该丢给用户选 API

- Pi npm exports、tool.execute、serial flag 已核对；由工程锁定依赖和实现 adapter，不问用户选参数名。
- Node 子进程启动成本、native saver 安装、目标 provider 的 stream/tool_call/abort 兼容、预算和错误映射需隔离 spike/测试，不凭语言偏好投票。
- 安全回归按业务观察结果：伪造 owner/plan refs、跨 owner、旧 anchor、同 key 改参数、确认双击、cancel 后晚结果、commit 后断线、售后 checkpoint 前后 crash、human takeover fencing。保留已有可用测试，另补边界测试；旧固定拓扑断言不该阻止新 Pi，但安全断言不能随拓扑一起删。

**下一步仅是取舍：** 先审清服务目录，确认 A 或 B 与最小纵切片，再修订实现 Spec/任务。本文不启动实现、安装、测试或修改任务状态。
