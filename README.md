# Ceres2 · 智能导购与受控售后

Ceres2 是一个面向商超购物场景的 AI 应用原型：帮助用户把“想做什么、有什么要求”转化为可检查、可修改、可明确确认的购买清单，并将模拟订单衔接到独立的售后流程。

项目围绕两类核心问题展开：

- **购买任务规划**：例如为几个人准备一道或多道菜，根据人数、预算、排除条件和门店供给，计算需要购买的商品、整包数量与余量。
- **品类内选购**：例如比较不同饮料的品牌、容量、包装、件数和价格，缩小候选范围，再由用户选择并确认。

普通商品浏览与搜索仍然保留。AI 负责理解需求、必要追问和解释；价格、库存、数量、订单与写入结果由业务服务提供和校验。**当前商品供给、结算、支付、配送和售后均为模拟业务，不涉及真实交易、资金执行或履约。**

## 从哪里开始

- **想了解产品与规划**：先读本页，再看 [PROJECT](PROJECT.md) 与 [产品定义](prd.md)。
- **准备在 Ubuntu 运行或接手开发**：读 [本地接力指南](docs/HANDOFF-UBUNTU.md)，其中包含安装、配置、启动、体验步骤和剩余验收项。
- **想了解技术来源**：读 [参考项目与采用边界](docs/REFERENCES.md)，区分实际依赖、架构参考与仅做研究的项目。
- **准备处理具体工作**：从 [16 项任务总索引](tasks/ceres2-upgrade.md) 进入对应 TASK，再读它链接的规格、实现与证据。

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

**第一阶段已有实现和受控技术验证，整体仍待验收。** 01–15 的受控技术范围及 TASK16 的受控集成已有通过记录；它们不能代替真实模型、真实浏览器和用户本人体验。

2026-10-06 首次真实模型批次通过配置与隔离数据检查，但在 Pi 比较阶段返回 `PI_PROVIDER_ERROR`；记录中的 502 是应用状态，上游原因未知。随后诊断补丁补充了安全的传输诊断字段。

同日 03:42 UTC，在 commit `3283e28` 上执行的一次有界真实 API 批次通过配置、seed 和 live health 检查，但 Pi 比较在原 15 秒保护上限处以 `runtime_status=deadline` 结束；4 轮工具交互后第 5 轮模型调用尚未完成。没有观察到上游 HTTP 状态或传输原因，购买、结算与售后阶段未运行。[脱敏证据](work/live-validation/tmp/live-20261006T034233Z-d66f017a40aa/evidence)。

用户随后明确将导购保护上限调到 30 秒。04:40 UTC 的单次复测通过配置、隔离、seed 和 health gates，但约 9.87 秒时在 Pi 比较阶段失败：应用返回 `422 PI_UNKNOWN_REFERENCE`。它不是 30 秒截止；证据没有记录 provider 上游 HTTP 状态、传输原因、runtime status 或工具轮数。购买、结算和 Mercury 阶段未运行。[脱敏证据](work/live-validation/tmp/live-20261006T044045Z-ade5f6652231/evidence)。

本地安装／构建冒烟已完成：Python 3.11.15、Node 22.19.0/npm 10.9.3；后端依赖检查、Pi runtime 和前端构建通过。Python 3.12.14 未能通过 uv 获取；当前版本满足项目 `>=3.11` 要求。前端构建有 Vite 配置警告，npm 提示一项 high severity 依赖漏洞。

Pi runtime typecheck/build 通过。后端相关模块此前 **23/23 通过**；针对 Mercury prompt/tool 描述的最新定向测试 **31/31 通过**。2026-10-06 最新隔离真实 API batch 使用 `deepseek-flash` / `api.deepseek.com`，34.02 秒 exit 0，**41/41 checks 通过**，覆盖比较、选品、模拟加购/结算与重放、退款提案/确认与重放；记忆提取为 observed，Dream 因阈值未达到而跳过。[脱敏 evidence](work/live-validation/tmp/live-20261006T062210Z-0575eb5f534d/evidence)。先前 live 失败保留为历史，不追认为通过。真实浏览器、历史复购、供给修订、人工、停止/恢复、记忆修改/删除、独立第二次运行和用户本人验收仍未完成；TASK16 仍待验收。具体范围见 [Ubuntu 接力指南](docs/HANDOFF-UBUNTU.md)，整体验收以 [TASK16](tasks/ceres2-runtime-upgrade-16-integrated-verification.md) 为准。

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
|       `-- src/worker.ts             # 实际 Pi Agent、工具循环与进程协议
|-- frontend/
|   |-- AGENTS.md                     # 前端专属修改约定
|   |-- package.json                  # React/Vite 依赖与开发构建命令
|   |-- package-lock.json             # 固定前端依赖解析
|   |-- vite.config.ts                # 开发端口与后端 API/media 代理
|   `-- src/
|       |-- main.tsx                  # React 启动入口
|       |-- App.tsx                   # 购物页面与可可交互
|       |-- MercuryChat.tsx           # 墨墨售后聊天
|       |-- HumanOperatorPage.tsx     # 人工工单处理页面
|       |-- components/               # 可复用界面组件
|       `-- lib/                      # HTTP/SSE 客户端与业务接口适配
|-- data/
|   |-- fixtures/                     # products/offers/recipes 与图片映射 JSON
|   `-- images/                       # 已恢复并核验的静态商品图片
|-- docs/
|   |-- HANDOFF-UBUNTU.md              # Ubuntu 安装、运行、验证与接力步骤
|   |-- REFERENCES.md                  # 参考项目链接及采用边界，不携带整仓源码
|   |-- plans/                        # 实施规格、拆分方案与技术研究
|   |-- adr/                          # 架构决策及原因
|   `-- agents/                       # 本项目任务管理与领域文档约定
|-- tasks/
|   |-- ceres2-upgrade.md              # 16 项正式任务的总索引
|   `-- ceres2-runtime-upgrade-*.md    # 各项范围、依赖、状态、验收和证据
`-- work/
    |-- clean-rebuild/                # 按任务组织的交付说明、迁移来源与验证脚本
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

完整命令以 [Ubuntu 本地接力指南](docs/HANDOFF-UBUNTU.md) 为单一入口，避免多份启动说明互相漂移：

1. 克隆到全新目录，保留原项目；使用 Linux Python 与 Node，按锁文件独立安装依赖并构建 Pi／前端。
2. 用户从 `.env.example` 创建新的本地 `.env`，自行填写凭据。本次真实验证统一使用 `qwen3.8-27b`，不自动换模型或 provider。
3. 先由用户亲自启动有界 API 批次；页面体验再显式 seed，并启动后端 `127.0.0.1:8012` 与前端 `127.0.0.1:8443`。启动应用和页面交互都可能触发真实模型调用，应遵守接力指南的执行边界。
4. 记录真实结果与剩余问题，按变更影响面复验，再分别完成浏览器和用户验收。

当前实现依赖 Linux；原生 Windows 未适配。协作期间由专职 Tester 执行安装、构建和测试，实现与独立审查分别进行。受控 pytest 使用虚拟 provider 配置并隔离根 `.env`；这不代表任意脚本也被隔离，详见 [测试隔离说明](work/live-validation/TEST-ISOLATION-REVIEW.md)。

部分较早文档保留了当时“无 remote／不推送”等执行条件和旧进度。阅读时核对日期与适用版本；当前公开交付和本地接力以本页及接力指南为入口，不将历史限制或历史通过直接套用到新版本。
