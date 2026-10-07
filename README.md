# Ceres2 · 智能导购与受控售后

> 2026-10-07 当前阶段：[本地能力与云端入口九票集成](tasks/ceres2-local-cloud-integration.md)。以[本轮规格](docs/plans/ceres2-local-cloud-integration-spec.md)和[Ubuntu 交接准备稿](docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md)为准。T05 实际浏览器受环境阻塞，T08-B 与 T09 最终同版门槛仍开放，未完成整体验收。四票、十票及旧 main/live 成绩仅适用于历史候选。

Ceres2 是一个面向商超购物场景的 AI 应用原型：帮助用户把“想做什么、有什么要求”转化为可检查、可修改、可明确确认的购买清单，并将模拟订单衔接到独立的售后流程。

项目围绕两类核心问题展开：

- **购买任务规划**：例如为几个人准备一道或多道菜，根据人数、预算、排除条件和门店供给，计算需要购买的商品、整包数量与余量。
- **品类内选购**：例如比较不同饮料的品牌、容量、包装、件数和价格，缩小候选范围，再由用户选择并确认。

普通商品浏览与搜索仍然保留。AI 负责理解需求、必要追问和解释；价格、库存、数量、订单与写入结果由业务服务提供和校验。**当前商品供给、结算、支付、配送和售后均为模拟业务，不涉及真实交易、资金执行或履约。**

## 当前阶段：本地能力与云端入口九票集成

2026-10-07：以云端 `37c98400e7152b89e4a58f02fff3bceaa73b0eac` 为基线，选择性整合 incoming `6734c7fe79e670df2dae12b065dcc49c0b10a307`。当前独立分支为 `ceres2/local-cloud-integration-20261007`，不合并 main，不覆盖原本地工作树。

- 保留可可新文字一次角色判断、确认后切换、政策预取与请求内复用；墨墨独立处理售后，返回购物使用明确按钮。
- 加入 BM25/BGE/RRF 候选检索，仍由 Python 校验 canonical 条件与当前 Offer；同一 Pi 原生完成、混合引用和经审校的可选过程消息；显式 GraphRAG 与规范菜谱事实分开。
- 售后包含问题包装数量、受范围保护的照片及精确工单证据关联。商品、金额、库存、支付、退款、配送全部为模拟；检索或模型回答不构成写入授权。
- 本地 UI 适配与运行观测尚在完成，不能把 WIP 备份或已通过的技术分片视为最终交付。T01/02/03/04/06/07 技术门槛及 T08-A 已放行；T05、T08-B、T09 最终同版门槛见 TASK 最新状态。

最新已核实里程碑：local `a835bd411f96285f15d67a75dd0c0abfdb1d1640` 对应 remote `7eaeda0cc1e27b96baaf235a1fede1ad47261a79`，相同 tree `66387dff204483a016931cfbb75cbe42f00f4100`，见[发布回执](work/local-cloud-integration/t06b-t08a-integration-publication-receipt.json)。SHA 不同而 tree 相同只证明该快照源码内容一致，不证明后来提交、构建、配置或运行状态一致。


## 历史四票架构与证据（2026-10-07 早期）

以下保留历史阶段，不代表本轮已验收状态；其中“当前”指该历史候选。

- **角色入口**：只有可可新自由文本进行一次是否转墨墨的入口判断；yes 等用户确认切换，no／uncertain／timeout／error 保留原文继续可可。墨墨文字和结构化按钮不新增角色或政策 Kev；返回购物只靠明确按钮，不自动续接旧购物授权。
- **同一 Pi 与政策证据**：留在可可的文字使用独立政策判断，yes 按完整原文预取现有静态规则并提供真实引用、来源、版本和状态。首次 Pi 理解保留相关任务、问题与引用，不再依赖四能力标签；后续由 guide_request 控制相关上下文。
- **事实与完整请求**：政策不是具体订单资格或提交授权；购物、澄清、普通解释、历史／记忆结果与政策及职责边界可同时保留。未匹配、部分和错误分别投影；Python 保留当前请求、取消、deadline 与事务保护。
- **请求内复用／多引用**：03 已完成精确 scope/query/category/版本复用、有效早期引用及多范围宿主输出，并通过 152 项专项（含重叠 34 复用／安全用例）和核心两轴复审；[03 TASK](tasks/ceres2-judge-prefetch-03-query-reuse.md)保留精确候选。固定 runtime_summary 独立于 256-event 诊断尾部；硬错误缺值仍为未知。04 的同版核心全量现已通过；核心文档／证据两轴审查无阻塞；独立 comparison 支持也已通过自身 22 项及两轴审阅。真实对照与前端／浏览器／本人验收未完成，不能称四票整体已验收。
- **当前受控核心**：冻结提交 `d6a40886926bf203b53c52db27d2177b1b3dcb80` 的 **558 backend** 全量通过，248 个源码 hash 与最终核心审查／专项一致；依赖、Pi typecheck/build 与 guard／isolation 同版通过，见[04 核心报告](work/judge-prefetch-rebuild/04-core-verification.md)。01 的 480、02 的 524、03 的 152 各保留适用版本，重叠数字不相加。已核实最终核心远端为 `88310f00836d29362e33384ffd959e9939e31a42`，详见[核心映射](work/judge-prefetch/publication-core-final.json)；比较支持作为后续独立受测／审阅产物加入，不回填为早先核心全量范围。真实 provider、前端／浏览器和用户本人验收仍开放。

- **手动比较支持**：[LIVE-COMPARE](work/judge-prefetch-rebuild/LIVE-COMPARE.md)默认 preview 惰性执行；独立 **22 项**通过，含重叠的两个真实当前 app／Pi SDK loopback case（假 key），见[支持报告](work/judge-prefetch-rebuild/04-comparison-support-verification.md)。真实用户执行须固定两源／build／模型和有限时间计划；MemoryWorker 与远端已受理请求可产生费用。未知 usage／成本／质量不填零，支持测试不是旧新真实效果比较。

## 历史体验更新（2026-10-06）

以下描述当时十票候选，不是当前角色／政策入口合同；它在原有模拟购物生命周期上改进选购、角色导航和结果呈现，保留 Python 业务权威与明确确认要求：

- **零食与饮品选购**：按实际模拟供给先选类、再筛选；问题和选项使用稳定身份，旧选项不能误用于新问题。支持预算、饮食限制、已知数量与跨货架明确搜索，选择商品不等于确认加购。
- **角色导航与政策**：一次 Kev 请求联合判断职责和能力；跨角色跳转由用户选择。可可、墨墨均可回答无订单的一般政策；购物＋政策复合请求保留两部分结果。
- **已有活动成品选购**：复用首页活动入口及限定商品关联；修改或退出时清理旧条件，不延续旧写入授权。当前静态数据共 **70 个模拟 SKU／Offer**。
- **结果先行与按需上下文**：业务结果先可用，再增量展示经校验的介绍；公共、角色和能力 Prompt 分模块按需组合。表达优化已有受控验证，但尚未证明真实语言品质、token、费用或时延改善。
- **售后回到购物**：保存售后回执或失败状态，再明确返回购物；保留原有幂等、记忆与人工负责期间的写入保护。售后申请提交不能表述为退款已完成。

最终审查发现的条件丢失、已知数量、跨品类搜索、复合结果与表达诊断问题已经修复，具体证据见 [Standards 审查](work/next-experience/10/standards-review.md)、[Spec 审查](work/next-experience/10/spec-review.md)及[修复记录](work/next-experience/10/review-fixes.md)。这表示具体实现问题闭合，不代表全部产品验收完成。

## 从哪里开始

- [九票总 TASK](tasks/ceres2-local-cloud-integration.md) → [集成规格](docs/plans/ceres2-local-cloud-integration-spec.md) → 各票固定证据与独立 Standards/Spec 审查。
- [本轮 Ubuntu 交接](docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md)：独立 worktree、锁依赖、BGE 模型与新索引、启动、迁移与剩余验收。
- [产品定义](prd.md)、[项目安排](PROJECT.md)、[参考项目与采用边界](docs/REFERENCES.md)。四票、十票和原 Ubuntu 指南是历史来源，其旧模型、分支、30 秒条件、商品数和 live 成绩不覆盖本轮。

## 系统如何分工

### 可可：售前导购

可可使用 **Node.js / TypeScript 和真实 Pi SDK** 执行模型与工具循环，支持需求探索、商品比较、方案调整、任务进度与停止。一个长期对话中最多保留一个活动购买任务，任务可跨多次有界运行。

选择商品、接受预算报价与确认加购是不同动作。商品或数量变化后，旧确认不能直接用于新方案；达到运行保护上限也不能被表述为任务成功。

### 墨墨 / Mercury：独立售后

墨墨使用 **Python LangGraph** 管理订单查询、资格核对、提案、明确确认、提交与恢复。用户从具体订单进入售后，先看到申请内容，再决定是否提交；重复确认应返回同一业务回执。

第一阶段包含精简的异步人工工单：人工可查看、回复和关闭事项，用户可查看进度。人工负责期间，Agent 不能独立提交同事项的业务写入；这不是实时人工聊天系统。

### Python：共享业务事实与执行

FastAPI 与 SQLAlchemy 统一管理可信匿名用户身份、商品与 Offer、购物车、订单、售后事项、记忆和业务回执。可可与墨墨共享必要业务数据，但保留各自入口和职责，不能跨用户访问，也不会自动向另一个角色开放全部记忆。

Pi 和 LangGraph 是采用的外部运行框架。Ceres2 的工程重点在于购物领域规则、工具接缝、确认与事务边界、持久化和恢复，而不是把框架能力包装成自研算法。LangGraph checkpoint 保存流程状态，不能替代业务数据库或成为写入授权依据。

前端沿用 React 页面，通过 HTTP/SSE 与后端交互。架构取舍见 [混合运行架构 ADR](docs/adr/0002-python-business-pi-langgraph-runtime.md) 和 [单一业务事实 ADR](docs/adr/0001-canonical-shopping-authority.md)。

## 项目规划

### 既有基础阶段：完整模拟购物生命周期

第一阶段按 16 个纵向任务组织，每项同时考虑必要的数据、业务服务、API、页面与验证，而不是先搭建一个通用 Agent 平台。

| 能力组 | 任务 | 交付目标 |
| --- | --- | --- |
| 运行与交互基础 | 01–04 | Pi 商品查询、LangGraph 售后查询、长期任务与可响应运行、明确加购确认 |
| 购买决策 | 05–08 | 单菜人数换算、多菜合并与来源展示、供给适配和部分采购、品类筛选比较 |
| 记忆与复购 | 09–11 | 聊天内记忆管理、回复后自动提取与低频 Dream、按当前条件重新采购历史方案 |
| 订单与售后 | 12–15 | 持久模拟订单、同用户订单贯通、具体确认与售后回执、异步人工工单 |
| 集成与验收 | 16 | 同版完整生命周期、恢复与异常验证、真实模型和页面体验、用户本人验收 |

原 16 票的依赖、负责人和证据保留在[基础阶段总 TASK](tasks/ceres2-upgrade.md)；当前四票实时状态以[角色／政策总 TASK](tasks/ceres2-judge-prefetch.md)为准，本页不另维护一套进度。

### 第二阶段与暂不纳入的范围

已明确留到第二阶段的是：**持续购物监测、后台定时提醒、跨应用／跨渠道通知，以及复杂多 Agent 通信与自动委派**。这些后续方向尚不代表已经实施或排定交付日期。

回复后自动记忆提取和低频 Dream 已属于第一阶段，不能与未来的后台购物监测混为一谈。独立记忆管理页面、任意购物车的自动任务识别与补齐等仍属延期或待讨论范围，并未全部承诺在第二阶段实现。

当前也不做真实支付／退款与履约、自动整餐或营养规划、实时人工接管、完整客服运营平台、分布式调度或全量 TypeScript 重写。长期产品范围以 [PROJECT](PROJECT.md) 和[基础阶段规格](docs/plans/ceres2-proactive-upgrade-spec.md)为准；当前四票实施边界另由[角色／政策规格](docs/plans/ceres2-judge-prefetch-spec.md)及[执行决定](docs/REBUILD-DECISIONS.md)固定。

## 历史进展与仍开放的体验限制（2026-10-06）

**以下仅适用于历史源码，不代表当前四票通过。同一云端冻结测试源码 `0c752a2b252d797297b4b073883571884ff6855a` 的受控技术验证通过，整体仍待验收。** 该 SHA 是云端测试来源标识，不保证可在 GitHub checkout。公开实现发布已推送至 main：[8d6d758](https://github.com/2061623884/Ceres2/commit/8d6d758228a5b9da50bf76ef7480e5cf517e6eed)，其文件树与经审查的本地发布候选 `358feb7589f5f8200c46a44de8365f2d88ae6c47` 完全一致。公开提交以原远程 `64ca7b6` 为父提交，保留公开历史；云端实施历史与公开集成历史有意不同。测试源码之后的变更为文档提交，不将这些提交冒称重新执行过产品验证。最终报告记录：

- 后端全量 **426/426** 通过，pytest 645.95 秒。
- **37 个受控 DOM/client 场景**通过；这是受控 React DOM／客户端验证，不是真实浏览器。
- Pi runtime typecheck/build、前端 production build／严格 TypeScript 通过；仓库未配置 lint 脚本，不记为 lint 通过。
- **1/1 隔离 OS 进程终止／重启探针**通过：已提交的结算回执保留、中断 Pi 不自动重放、用户可明确继续。它不证明任意断电、磁盘故障或多机恢复。
- 四次 capture 的源文件未变；等价记录确认 238 个 backend 源文件、280 个 build/UI 源与文档后继集成一致。两轴独立审查及 fixture 窄复核闭合。

**仍未完成**：真实配置的 provider／Kev 与浏览器旅程、自然中文品质、真实 usage／时延、独立未见 holdout、冻结 V3 业务比较、真实记忆／Dream 长周期观察及用户本人验收。Prompt 指令长度实际增加，不能宣称成本优化。非阻塞 Vite 配置警告和受控 `ShelfScreen` render 期间更新 `ShoppingApp` 的 React 警告仍有记录，真实页面验收需关注。

旧阶段曾完成 41/41 真实 API checks，也保留了更早 provider 错误、15 秒截止及未知引用失败；它们属于各自历史版本，**不构成本轮真实模型通过证据**。历史详情见[旧 Ubuntu 接力记录](docs/HANDOFF-UBUNTU.md)，该历史阶段结论以[当时最终报告](work/next-experience/10/final-controlled-verification.md)为准；当前阶段另查[四票接手指南](docs/JUDGE-PREFETCH-HANDOFF.md)。

## 文件与目录管理

### 产品、计划与证据各有一个主要位置

| 文件／目录 | 负责什么 | 如何维护 |
| --- | --- | --- |
| `README.md` | 项目介绍、架构与规划概览、运行和文档入口 | 保持简洁，不维护逐次执行日志 |
| `prd.md` | 产品问题、长期需求与业务边界 | 需求不等于已实现；当前阶段取舍另见 PROJECT |
| `PROJECT.md` | 当前阶段目标、已确认取舍与后续方向 | 保存项目决策，不替代单项任务状态 |
| `tasks/` | 正式任务、范围、依赖、状态、验收与证据入口 | 每项任务只维护一份当前状态，从总索引进入 |
| `docs/plans/`、`docs/adr/` | 实施规格、方案和架构决策 | 说明为什么这样设计；历史研究不自动成为当前指令 |
| `docs/HANDOFF-UBUNTU.md`、`docs/REFERENCES.md` | 本地接力与技术来源 | 提供可操作步骤，明确依赖、参考与验证边界 |
| `work/` | 按任务组织的脚本、交付说明和验证材料 | 保留适用源码版本与失败记录；不另建第二套任务状态 |
| `logs/`（按需建立） | 关键变化及原因 | 不维护第二套最新进度，不替代 TASK |
| `GLOSSARY.md`、`AGENTS.md` | 领域术语、协作与修改约定 | 实施前阅读；前端另有 `frontend/AGENTS.md` |

### 仓库目录结构

下列目录表保留早期基础工程入口，新增 knowledge/evaluation 与本轮结构见[当前交接项目树](docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md#2-项目树与职责)；目录存在不代表场景已验收。

```text
Ceres2/
|-- README.md                         # 项目介绍、规划与阅读入口
|-- PROJECT.md                        # 当前阶段目标与已确认的产品取舍
|-- prd.md                            # 长期产品需求与业务边界
|-- GLOSSARY.md                       # 领域术语
|-- AGENTS.md                         # 协作、修改与验证约定
|-- .env.example                      # 无凭据配置模板；用户自行创建 .env
|-- .gitignore                        # 排除凭据、依赖、运行状态与构建产物
|-- backend/
|   |-- pyproject.toml                # Python 项目与依赖声明
|   |-- requirements.lock             # 固定 Python 依赖版本
|   |-- app/
|   |   |-- main.py                   # FastAPI 入口、路由挂载与应用生命周期
|   |   |-- core/                     # 配置、可信身份、数据库与公共错误
|   |   |-- api/                      # 商品、导购、购物车和订单等 HTTP/SSE 接口
|   |   |-- models/                   # 共享业务数据模型
|   |   |-- schemas/                  # 历史与记忆等请求/响应结构
|   |   |-- migrations/               # 业务 schema 初始化与版本迁移
|   |   |-- services/                 # 购物、供给、确认、记忆等业务服务
|   |   |   |-- seed_service.py        # 显式、幂等导入静态商品/门店/Offer
|   |   |   |-- product_question_service.py # 稳定问题、候选选择与确认合同
|   |   |   |-- navigation_service.py  # 单次职责判断与用户选择的角色跳转
|   |   |   |-- kev_provider.py        # Kev /v1/systemone 角色／政策两种独立判断
|   |   |   |-- activity_service.py    # 已有活动与限定成品选购
|   |   |   |-- result_introduction_service.py # 结果先行与受校验的介绍
|   |   |   |-- pi_product_runtime.py  # Python 与 Node/Pi 的运行接缝
|   |   |   `-- memory_background.py   # 后台记忆提取与 Dream 作业
|   |   |-- mercury/                  # 墨墨售后；与可可保持独立入口
|   |   |   |-- router.py             # 售后 HTTP/SSE 接口
|   |   |   |-- graph.py              # LangGraph 查询编排
|   |   |   `-- aftersales_graph.py   # 售后确认与恢复流程
|   |   `-- human/                    # 异步人工工单的模型、路由和服务
|   `-- tests/                        # 受控 API、事务、runtime 与恢复测试
|       |-- conftest.py               # 测试 fixture 与真实配置隔离
|       `-- test_integrated_lifecycle.py # 跨模块完整生命周期受控验证
|-- runtime/
|   `-- pi/
|       |-- package.json              # Pi SDK 依赖及 build/typecheck 命令
|       |-- package-lock.json         # 固定 Node 依赖解析
|       |-- tsconfig.json             # TypeScript 编译配置
|       `-- src/
|           |-- worker.ts             # 实际 Pi Agent、工具循环与进程协议
|           |-- prompt-modules.ts     # 首次角色上下文与 guide_request 后续选择
|           `-- result-expression.ts  # 有界结果表达与事实保护
|-- frontend/
|   |-- AGENTS.md                     # 前端专属修改约定
|   |-- package.json                  # React/Vite 依赖与开发构建命令
|   |-- package-lock.json             # 固定前端依赖解析
|   |-- vite.config.ts                # 开发端口与后端 API/media 代理
|   `-- src/
|       |-- main.tsx                  # React 启动入口
|       |-- App.tsx                   # 购物页面与可可交互
|       |-- MercuryChat.tsx           # 墨墨售后聊天
|       |-- QuestionChoices.tsx        # 稳定问题与可选项呈现
|       |-- HumanOperatorPage.tsx     # 人工工单处理页面
|       |-- components/               # 可复用界面组件
|       `-- lib/                      # HTTP/SSE 客户端与业务接口适配
|-- data/
|   |-- fixtures/                     # products/offers/recipes 与图片映射 JSON
|   `-- images/                       # 已恢复并核验的静态商品图片
|-- docs/
|   |-- JUDGE-PREFETCH-HANDOFF.md      # 当前四票合同、启动与外部验收
|   |-- NEXT-EXPERIENCE-HANDOFF.md     # 历史十票候选与剩余验收
|   |-- HANDOFF-UBUNTU.md              # 原阶段 Ubuntu 安装与历史 live 记录
|   |-- REFERENCES.md                  # 参考项目链接及采用边界，不携带整仓源码
|   |-- plans/                        # 实施规格、拆分方案与技术研究
|   |-- adr/                          # 架构决策及原因
|   `-- agents/                       # 本项目任务管理与领域文档约定
|-- tasks/
|   |-- ceres2-judge-prefetch.md       # 当前四票总索引
|   |-- ceres2-judge-prefetch-*.md     # 当前依赖、状态、合同与证据
|   |-- ceres2-next-experience.md      # 历史 10 票总索引
|   |-- ceres2-next-*.md               # 历史任务与适用版本证据
|   |-- ceres2-upgrade.md              # 原阶段 16 项正式任务的总索引
|   `-- ceres2-runtime-upgrade-*.md    # 各项范围、依赖、状态、验收和证据
`-- work/
    |-- judge-prefetch-rebuild/       # 当前受控 harness、冻结证据与审查
    |-- judge-prefetch/               # 基线与可核对的发布映射
    |-- next-experience/              # 历史十票合同、脚本与评审证据
    |   `-- 10/                       # 同候选最终验证、等价记录与独立审查
    |-- clean-rebuild/                # 原阶段交付说明、迁移来源与验证脚本
    `-- live-validation/
        |-- USER-RUN.md               # 用户亲自启动 live 批次的范围与步骤
        |-- run_live_batch.py         # 有界真实模型 API 旅程；不等于浏览器测试
        |-- test_live_batch.py        # 不调用 provider 的 harness 验证
        |-- TEST-ISOLATION-REVIEW.md   # 受控测试隔离范围与复验结论
        `-- DIAGNOSTICS-20261006.md    # 首次 live 失败与诊断补丁说明
```

以下是安装或运行后生成的**本地内容，不属于公开源码树**，也不能从旧项目复制：

```text
Ceres2/
|-- .env                              # 用户本地凭据与配置
|-- backend/.venv/                    # 本轮 Python 虚拟环境
|-- data/runtime/                     # 业务数据库与 LangGraph checkpoint
|-- runtime/pi/node_modules/          # Pi 的本地依赖
|-- runtime/pi/dist/                  # 编译后的 Pi worker
|-- frontend/node_modules/            # 前端本地依赖
|-- frontend/dist/                    # 前端构建产物
`-- work/live-validation/tmp/         # 每次 live 批次的隔离状态与 evidence
```

`logs/`、`evals/`、`scripts/` 是按需要组织变更记录、评测和辅助脚本的约定位置；当前公开清单不包含这些目录，不将空目录列成已交付能力。任务专用脚本优先放在对应 `work/` 子目录。

新工程保留原前端，并选择性重建业务契约；静态输入通过显式 seed 导入。来源见 [迁移记录](work/clean-rebuild/migration-ledger.md)。公开仓库不携带整套外部 reference 源码：需要了解参考项目时使用 [来源清单](docs/REFERENCES.md)，运行和构建不得依赖相邻 `reference/` 或 `archive/`。

`.env`、凭据、数据库、checkpoint、会话、缓存、`.venv` 和 `node_modules` 都是本地内容，不随代码提交。公开证据只保留经过检查的必要摘要，不上传原始 provider 日志或私有运行状态。

## 在 Ubuntu 开始

按新交接逐步执行。业务环境放根目录 `.venv`，知识 worker 固定使用根目录 `.venv-graphrag/bin/python`；使用业务锁、知识锁及两个 npm lock 独立安装。BGE 从固定本地缓存加载，缺依赖、模型或索引不会自动下载或退化成“空结果”。原 `.env`、数据库、checkpoint、索引和主工作树 53 项 dirty 全部留原处。

Guide 本次处理预算由基线 30 秒改为 15 秒，最多 5 轮工具；直接请求含同步角色授权，独立导航预检与用户等待不合并成一个跨请求预算。独立 build-graph 必须另给有限正数 `--timeout-seconds`，不沿用 Guide 15 秒，也不承诺该时间足够完成图构建。

模型仍为用户当前批准配置；不因模板或旧文档而换 provider/model。只有规范化 hostname 精确为 `api.deepseek.com` 才发送 thinking disabled。启动后端会启动 MemoryWorker；图构建、图查询和页面操作可能调用真实 provider 并产生费用，须由用户亲自执行或另有明确授权。本轮未执行真实 provider 测试。

最终验收：待 T09 固定候选、backend full、Pi typecheck/build、frontend strict TypeScript/build 与两轴报告填入。实际 Chromium/CUA 浏览器当前因权限/跨执行环境连通性受阻，保留待验，DOM/HTTP 不能替代。真实模型、真实用户浏览器、Memory/Dream 与用户本人接受单独记录，不能继承历史通过。
