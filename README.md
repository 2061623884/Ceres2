# Ceres2 · 智能导购与受控售后

> **2026-10-07 本机 Cursor 接管**：交接快照见 [本机交接文档](docs/CURSOR-HANDOFF-20261007.md)。工作区仍未提交。官方 DeepSeek 请求已关闭 thinking，受控传输通过；真实原句回归仍无候选，记忆未满 10 条，24 小时观察尚未开始。任务最新状态由 TASK10 维护。

> 2026-10-06 本轮：下一阶段体验更新（10 票）。受控技术验证通过，真实模型、浏览器与用户验收仍开放。先看下方更新摘要，再读[接手与剩余验收](docs/NEXT-EXPERIENCE-HANDOFF.md)和[当前十票总 TASK](tasks/ceres2-next-experience.md)。

Ceres2 是一个面向商超购物场景的 AI 应用原型：帮助用户把“想做什么、有什么要求”转化为可检查、可修改、可明确确认的购买清单，并将模拟订单衔接到独立的售后流程。

项目围绕两类核心问题展开：

- **购买任务规划**：例如为几个人准备一道或多道菜，根据人数、预算、排除条件和门店供给，计算需要购买的商品、整包数量与余量。
- **品类内选购**：例如比较不同饮料的品牌、容量、包装、件数和价格，缩小候选范围，再由用户选择并确认。

普通商品浏览与搜索仍然保留。AI 负责理解需求、必要追问和解释；价格、库存、数量、订单与写入结果由业务服务提供和校验。**当前商品供给、结算、支付、配送和售后均为模拟业务，不涉及真实交易、资金执行或履约。**

## 本轮更新：评审时先看这些

本轮在原有模拟购物生命周期上改进选购、角色导航和结果呈现，没有改变 Python 业务权威或明确确认要求：

- **零食与饮品选购**：按实际模拟供给先选类、再筛选；问题和选项使用稳定身份，旧选项不能误用于新问题。支持预算、饮食限制、已知数量与跨货架明确搜索，选择商品不等于确认加购。
- **角色导航与政策**：一次 Kev 请求联合判断职责和能力；跨角色跳转由用户选择。可可、墨墨均可回答无订单的一般政策；购物＋政策复合请求保留两部分结果。
- **已有活动成品选购**：复用首页活动入口及限定商品关联；修改或退出时清理旧条件，不延续旧写入授权。当前静态数据共 **70 个模拟 SKU／Offer**。
- **结果先行与按需上下文**：业务结果先可用，再增量展示经校验的介绍；公共、角色和能力 Prompt 分模块按需组合。表达优化已有受控验证，但尚未证明真实语言品质、token、费用或时延改善。
- **售后回到购物**：保存售后回执或失败状态，再明确返回购物；保留原有幂等、记忆与人工负责期间的写入保护。售后申请提交不能表述为退款已完成。

最终审查发现的条件丢失、已知数量、跨品类搜索、复合结果与表达诊断问题已经修复，具体证据见 [Standards 审查](work/next-experience/10/standards-review.md)、[Spec 审查](work/next-experience/10/spec-review.md)及[修复记录](work/next-experience/10/review-fixes.md)。这表示具体实现问题闭合，不代表全部产品验收完成。

## 从哪里开始

- **审查本轮**：[10 票总索引](tasks/ceres2-next-experience.md) → [规格](docs/plans/ceres2-next-experience-spec.md)／[决策](docs/plans/ceres2-next-experience-decisions.md) → 对应实现和证据；[TASK10](tasks/ceres2-next-10-candidate-evidence.md)集中列出验收边界。
- **核对验证**：[最终 Tester 报告](work/next-experience/10/final-controlled-verification.md)、[源码等价记录](work/next-experience/10/final-controlled-equality.json)、[覆盖清单](work/next-experience/10/coverage-manifest.json)。
- **本地运行或接手**：以[本轮接手指南](docs/NEXT-EXPERIENCE-HANDOFF.md)为当前入口；[旧 Ubuntu 指南](docs/HANDOFF-UBUNTU.md)仅补充安装背景，旧模型、65 商品与 41 项 live 记录不能套用本轮。
- **了解产品与来源**：[PROJECT](PROJECT.md)、[产品定义](prd.md)、[参考项目与采用边界](docs/REFERENCES.md)。[原 16 票索引](tasks/ceres2-upgrade.md)保留原阶段范围与历史证据。

部分 TASK 中的历史／中间执行证据链接指向仅保留在云端的未跟踪文件，未随公开仓库发布。最终候选的公开依据是上述最终报告、两轴审查，以及报告链接的四组 `fixture-final-*` 记录与日志；不将未发布的中间链接视为公开可访问证据。

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

### 第一阶段：建立完整、可验证的模拟购物生命周期

第一阶段按 16 个纵向任务组织，每项同时考虑必要的数据、业务服务、API、页面与验证，而不是先搭建一个通用 Agent 平台。

| 能力组 | 任务 | 交付目标 |
| --- | --- | --- |
| 运行与交互基础 | 01–04 | Pi 商品查询、LangGraph 售后查询、长期任务与可响应运行、明确加购确认 |
| 购买决策 | 05–08 | 单菜人数换算、多菜合并与来源展示、供给适配和部分采购、品类筛选比较 |
| 记忆与复购 | 09–11 | 聊天内记忆管理、回复后自动提取与低频 Dream、按当前条件重新采购历史方案 |
| 订单与售后 | 12–15 | 持久模拟订单、同用户订单贯通、具体确认与售后回执、异步人工工单 |
| 集成与验收 | 16 | 同版完整生命周期、恢复与异常验证、真实模型和页面体验、用户本人验收 |

任务依赖、负责人、验收条件和证据统一放在 [tasks/](tasks/ceres2-upgrade.md)，本页只提供规划概览。

### 第二阶段与暂不纳入的范围

已明确留到第二阶段的是：**持续购物监测、后台定时提醒、跨应用／跨渠道通知，以及复杂多 Agent 通信与自动委派**。这些后续方向尚不代表已经实施或排定交付日期。

回复后自动记忆提取和低频 Dream 已属于第一阶段，不能与未来的后台购物监测混为一谈。独立记忆管理页面、任意购物车的自动任务识别与补齐等仍属延期或待讨论范围，并未全部承诺在第二阶段实现。

当前也不做真实支付／退款与履约、自动整餐或营养规划、实时人工接管、完整客服运营平台、分布式调度或全量 TypeScript 重写。完整范围以 [PROJECT](PROJECT.md) 和 [实施规格](docs/plans/ceres2-proactive-upgrade-spec.md) 为准。

## 当前进展与已知限制

**同一云端冻结测试源码 `0c752a2b252d797297b4b073883571884ff6855a` 的受控技术验证通过，整体仍待验收。** 该 SHA 是云端测试来源标识，不保证可在 GitHub checkout。公开实现发布已推送至 main：[8d6d758](https://github.com/2061623884/Ceres2/commit/8d6d758228a5b9da50bf76ef7480e5cf517e6eed)，其文件树与经审查的本地发布候选 `358feb7589f5f8200c46a44de8365f2d88ae6c47` 完全一致。公开提交以原远程 `64ca7b6` 为父提交，保留公开历史；云端实施历史与公开集成历史有意不同。测试源码之后的变更为文档提交，不将这些提交冒称重新执行过产品验证。最终报告记录：

- 后端全量 **426/426** 通过，pytest 645.95 秒。
- **37 个受控 DOM/client 场景**通过；这是受控 React DOM／客户端验证，不是真实浏览器。
- Pi runtime typecheck/build、前端 production build／严格 TypeScript 通过；仓库未配置 lint 脚本，不记为 lint 通过。
- **1/1 隔离 OS 进程终止／重启探针**通过：已提交的结算回执保留、中断 Pi 不自动重放、用户可明确继续。它不证明任意断电、磁盘故障或多机恢复。
- 四次 capture 的源文件未变；等价记录确认 238 个 backend 源文件、280 个 build/UI 源与文档后继集成一致。两轴独立审查及 fixture 窄复核闭合。

**仍未完成**：真实配置的 provider／Kev 与浏览器旅程、自然中文品质、真实 usage／时延、独立未见 holdout、冻结 V3 业务比较、真实记忆／Dream 长周期观察及用户本人验收。Prompt 指令长度实际增加，不能宣称成本优化。非阻塞 Vite 配置警告和受控 `ShelfScreen` render 期间更新 `ShoppingApp` 的 React 警告仍有记录，真实页面验收需关注。

旧阶段曾完成 41/41 真实 API checks，也保留了更早 provider 错误、15 秒截止及未知引用失败；它们属于各自历史版本，**不构成本轮真实模型通过证据**。历史详情见[旧 Ubuntu 接力记录](docs/HANDOFF-UBUNTU.md)，本轮结论以[最终报告](work/next-experience/10/final-controlled-verification.md)与[当前接手指南](docs/NEXT-EXPERIENCE-HANDOFF.md)为准。

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

下面按当前公开文件清单列出主要入口，省略同类业务文件和测试文件；注释说明职责，不表示该目录下所有场景均已验收。

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
|   |   |   |-- kev_provider.py        # Kev /v1/systemone 联合职责／能力接缝
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
|           |-- prompt-modules.ts     # 公共、角色与能力的按需 Prompt
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
|   |-- NEXT-EXPERIENCE-HANDOFF.md     # 本轮运行、准确候选与剩余验收
|   |-- HANDOFF-UBUNTU.md              # 原阶段 Ubuntu 安装与历史 live 记录
|   |-- REFERENCES.md                  # 参考项目链接及采用边界，不携带整仓源码
|   |-- plans/                        # 实施规格、拆分方案与技术研究
|   |-- adr/                          # 架构决策及原因
|   `-- agents/                       # 本项目任务管理与领域文档约定
|-- tasks/
|   |-- ceres2-next-experience.md      # 本轮 10 票总索引
|   |-- ceres2-next-*.md               # 本轮任务、依赖、状态与证据
|   |-- ceres2-upgrade.md              # 原阶段 16 项正式任务的总索引
|   `-- ceres2-runtime-upgrade-*.md    # 各项范围、依赖、状态、验收和证据
`-- work/
    |-- next-experience/              # 本轮各票合同、脚本与评审证据
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
|-- .venv/                            # Python 虚拟环境
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

当前实现依赖 Linux；原生 Windows 未适配。Python 声明为 `>=3.11`，Pi SDK 要求 Node `>=22.19.0`；本轮受控环境为 **Python 3.12.14、Node 24.19.0、npm 11.9.0**。新环境按 `backend/requirements.lock` 与两份 `package-lock.json` 独立安装，不借用旧项目依赖或数据库。协作期间安装、构建和执行验证由专职 Tester 负责。

1. 从 [Ceres2 仓库](https://github.com/2061623884/Ceres2) 获取 main，核对下载版本；本轮完整代码与经审查文档已包含在[公开实现发布 8d6d758](https://github.com/2061623884/Ceres2/commit/8d6d758228a5b9da50bf76ef7480e5cf517e6eed)，之后可有仅文档更新。原 Ceres 保持不动。
2. 从 `.env.example` 创建新的本地 `.env`，在可信本地编辑器填写获准的模型配置与凭据。不要上传 `.env`，不要复制旧数据库或 checkpoint。本轮没有重新选择 provider／模型。
3. 自动新文字职责／能力判断另需 `KEV_BASE_URL`，服务必须支持当前 `/v1/systemone` 合同。空值或服务失败时会显示判断不可用，用户可明确手动选角色；手动继续不代表自动路由成功。人工入口另需 `HUMAN_OPERATOR_TOKEN`。
4. 按[本轮接手指南的启动步骤](docs/NEXT-EXPERIENCE-HANDOFF.md)构建 Pi、显式 seed，再启动后端 `127.0.0.1:8012` 和前端 `127.0.0.1:8443`。健康检查成功不证明 provider 可用。
5. 启动和对话可能调用真实模型、后台记忆任务并产生费用；由用户在同意数据发送与费用后亲自操作，或另行明确授权。按接手指南只补剩余真实旅程和本人验收，不拿旧 live runner 的固定模型／41 项成绩替代本轮验证。

公开仓库仅发布源码、静态模拟素材与经检查的必要证据；不发布凭据、私有状态、依赖／构建目录、大量原始执行日志或外部 reference 整仓副本。测试使用受控 provider／Kev 边界，不能据此推断任意启动脚本也已隔离。

部分历史文档记录当时“无 remote／不推送”的条件。本次已按用户授权发布到独立 Ceres2 仓库，并核对[公开实现发布](https://github.com/2061623884/Ceres2/commit/8d6d758228a5b9da50bf76ef7480e5cf517e6eed)的完整文件树；这些旧条件不再描述当前发布状态。GitHub 发布不代表已经部署，也不代表真实模型、浏览器或用户验收通过。
