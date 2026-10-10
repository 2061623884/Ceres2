# Ceres2 重建：原项目与系列参考源码清单

核对日期：2026-10-07 UTC。此清单记录已经拉取并冻结的源码；不以星数、默认分支名或旧验收结论替代版本证据。

## 必须先读的边界

- 不能只拉取 Ceres2：本工作区同时保留原 Ceres 和下列系列参考。原项目位于 Ceres2 的相邻 `../reference/original/Ceres/`，外部项目位于 `../reference/vendor/`。目录是本地源码阅读材料，不随 Ceres2 发布。
- 先读当前 TASK、规格、ADR，再按票读取参考文件。Ceres 是业务／视觉来源，Ceres2 当前代码和已批准契约才是实现主线；上游规则不能覆盖本项目规则。
- 所有快照以 detached HEAD 固定，约定只读。禁止 runtime import、PYTHONPATH、配置、构建、符号链接或依赖借用指向 `../reference/`；不复制旧数据库、索引、session、cart、checkpoint、order、凭据或整套 backend/Mercury。
- 本轮只拉取公开源码、核对 Git 元数据与指定源码／许可文件；没有安装、执行或测试这些参考项目，没有访问其凭据／本地业务状态。仓内即使含配置、cookie、数据库样例，也不得读取或迁入以充当当前配置。
- 01 立即阅读 Mu、learn-claude-code 的列出接缝即可；其他参考按对应业务需要查阅，不要求先通读或移植全部仓库。
- 本清单中的目录均以 **Ceres2 仓库根** 为相对起点。SHA 是实际本地 HEAD；提交日期采用 Git committer ISO 日期并保留上游时区，不是本次拉取日期。

## 已拉取并冻结的清单

### 1. Ceres（原项目／Ceres1）

- 优先级／用途：业务与视觉基线；与 Ceres2 当前实现主线分开。
- 实际 remote：`https://github.com/2061623884/Ceres.git`。
- 本地目录：`../reference/original/Ceres/`。
- 冻结 SHA：[`ee7ce104885f731bc48bc8c6338c00d802ba0619`](https://github.com/2061623884/Ceres/tree/ee7ce104885f731bc48bc8c6338c00d802ba0619)；提交日期：`2026-10-06T14:46:05+08:00`。
- 选取依据：本次 clone HEAD 与下一阶段规格既有视觉来源 ee7ce104 相同；更早 e24debf6 仍只是历史迁移来源，不混作同一快照。
- 许可核对：未发现仓库根或其他路径的 LICENSE/COPYING/NOTICE 文件；不据此推定第三方代码或素材的复用授权。
- 阅读目标与限制：原 PRD、角色入口、统一聊天浮层和页面行为的来源。只做按当前票据选择性适配；不得整体复制旧 backend/Mercury，旧测试结论不能继承。
- 优先源码：
  - [`prd.md`](https://github.com/2061623884/Ceres/blob/ee7ce104885f731bc48bc8c6338c00d802ba0619/prd.md)
  - [`PROJECT.md`](https://github.com/2061623884/Ceres/blob/ee7ce104885f731bc48bc8c6338c00d802ba0619/PROJECT.md)
  - [`frontend/src/App.tsx`](https://github.com/2061623884/Ceres/blob/ee7ce104885f731bc48bc8c6338c00d802ba0619/frontend/src/App.tsx)
  - [`frontend/src/MercuryChat.tsx`](https://github.com/2061623884/Ceres/blob/ee7ce104885f731bc48bc8c6338c00d802ba0619/frontend/src/MercuryChat.tsx)
  - [`frontend/src/lib/chatOpening.ts`](https://github.com/2061623884/Ceres/blob/ee7ce104885f731bc48bc8c6338c00d802ba0619/frontend/src/lib/chatOpening.ts)

### 2. Mu

- 优先级／用途：01 优先：小判断、宿主钩子与预上下文。
- 实际 remote：`https://github.com/qybaihe/mu.git`。
- 本地目录：`../reference/vendor/mu/`。
- 冻结 SHA：[`47c51b0c68f622e9953b7f501d165fe474eec588`](https://github.com/qybaihe/mu/tree/47c51b0c68f622e9953b7f501d165fe474eec588)；提交日期：`2026-10-06T13:29:00+08:00`。
- 选取依据：使用已批准 Kev 规划研究快照；本次 clone HEAD 正好相同。
- 许可核对：LICENSE 存在，MIT；子目录另有许可文件，逐文件复用时仍需核对。
- 阅读目标与限制：参考 bounded decisions、preflight 和上下文注入接缝。Mu 的多判定点、默认超时、概率阈值和 fallback 不是 Ceres2 已批准产品规则；不整套移植。
- 优先源码：
  - [`packages/kyrn-judge/src/decisions/input-preflight.ts`](https://github.com/qybaihe/mu/blob/47c51b0c68f622e9953b7f501d165fe474eec588/packages/kyrn-judge/src/decisions/input-preflight.ts)
  - [`packages/kyrn-judge/src/extension/features/preflight.ts`](https://github.com/qybaihe/mu/blob/47c51b0c68f622e9953b7f501d165fe474eec588/packages/kyrn-judge/src/extension/features/preflight.ts)
  - [`packages/kyrn-judge/src/decision.ts`](https://github.com/qybaihe/mu/blob/47c51b0c68f622e9953b7f501d165fe474eec588/packages/kyrn-judge/src/decision.ts)
  - [`packages/coding-agent/src/core/agent-session.ts`](https://github.com/qybaihe/mu/blob/47c51b0c68f622e9953b7f501d165fe474eec588/packages/coding-agent/src/core/agent-session.ts)

### 3. learn-claude-code

- 优先级／用途：01 优先：同一个 Agent、工具目录与执行守卫。
- 实际 remote：`https://github.com/shareAI-lab/learn-claude-code.git`。
- 本地目录：`../reference/vendor/learn-claude-code/`。
- 冻结 SHA：[`ce8f9f186058939da54c9d6fead78dfb5d0fd6c3`](https://github.com/shareAI-lab/learn-claude-code/tree/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3)；提交日期：`2026-09-28T21:49:16+08:00`。
- 选取依据：使用已批准 Kev 规划研究快照；本次 clone HEAD 正好相同。阅读 root s01–s17 主课程，不与旧 agents/docs 课程编号混用。
- 许可核对：LICENSE 存在，MIT。
- 阅读目标与限制：参考工具结果提供知识、每轮工具池和执行前守卫。它没有可直接启用的 Ceres 业务预检索去重；s07 的 context_inject_hook 名称不能当成已实现检索注入。
- 优先源码：
  - [`s02_tool_use/code.py`](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s02_tool_use/code.py)
  - [`s07_skill_loading/code.py`](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s07_skill_loading/code.py)
  - [`s14_mcp_plugin/code.py`](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s14_mcp_plugin/code.py)
  - [`s15_integrated_harness/code.py`](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s15_integrated_harness/code.py)

### 4. Pi 官方运行时

- 优先级／用途：实际 SDK 来源核对，优先级随当前调用接缝。
- 实际 remote：`https://github.com/earendil-works/pi.git`。
- 本地目录：`../reference/vendor/pi/`。
- 冻结 SHA：[`d78dc83d633229d12f8b79631384c4c2717c399f`](https://github.com/earendil-works/pi/tree/d78dc83d633229d12f8b79631384c4c2717c399f)；提交日期：`2026-10-05T10:21:10+02:00`。
- 选取依据：固定到既有 npm 发布来源 gitHead d78dc83d（Release v1.0.3）；本次初始上游 HEAD 为 eb326d265ae0b88489a6d10319307780df827cdf，已显式 fetch 后 detached checkout 发布 SHA，未自动升级 Ceres2。
- 许可核对：LICENSE 存在，MIT；已安装两个目标包元数据也标记 MIT。
- 阅读目标与限制：Ceres2 实际锁定并安装 @earendil-works/pi-agent-core@1.0.3 和 @earendil-works/pi-ai@1.0.3。两份已安装 package.json 的 repository 分别指向 earendil-works/pi 的 packages/agent、packages/ai；不得替换成旧同名包或 Mu fork。
- 优先源码：
  - [`packages/agent/package.json`](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/agent/package.json)
  - [`packages/agent/src/agent.ts`](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/agent/src/agent.ts)
  - [`packages/agent/src/types.ts`](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/agent/src/types.ts)
  - [`packages/ai/src/models.ts`](https://github.com/earendil-works/pi/blob/d78dc83d633229d12f8b79631384c4c2717c399f/packages/ai/src/models.ts)

### 5. Hermes Agent

- 优先级／用途：补充：运行循环、记忆钩子与工具注册。
- 实际 remote：`https://github.com/NousResearch/hermes-agent.git`。
- 本地目录：`../reference/vendor/hermes-agent/`。
- 冻结 SHA：[`0e37a439bda15ef3c28a4d20593964d7c6a527a6`](https://github.com/NousResearch/hermes-agent/tree/0e37a439bda15ef3c28a4d20593964d7c6a527a6)；提交日期：`2026-10-06T22:09:21-05:00`。
- 选取依据：Nous Research 官方站点 https://hermes-agent.nousresearch.com/ 与 NousResearch/hermes-agent 仓库相互链接；本次首次冻结该目录的 clone HEAD，没有把其他同名 Hermes 当成来源。
- 许可核对：LICENSE 存在，MIT；仓内还存在其他子项目许可，根许可不是所有素材的笼统授权。
- 阅读目标与限制：仅研究宿主运行循环、记忆 provider 边界和工具组织，不引入 Hermes 服务、外部记忆插件或其默认配置，不视为本票完成条件。
- 优先源码：
  - [`run_agent.py`](https://github.com/NousResearch/hermes-agent/blob/0e37a439bda15ef3c28a4d20593964d7c6a527a6/run_agent.py)
  - [`agent/memory_manager.py`](https://github.com/NousResearch/hermes-agent/blob/0e37a439bda15ef3c28a4d20593964d7c6a527a6/agent/memory_manager.py)
  - [`agent/memory_provider.py`](https://github.com/NousResearch/hermes-agent/blob/0e37a439bda15ef3c28a4d20593964d7c6a527a6/agent/memory_provider.py)
  - [`tools/registry.py`](https://github.com/NousResearch/hermes-agent/blob/0e37a439bda15ef3c28a4d20593964d7c6a527a6/tools/registry.py)

### 6. Wang 电商售后参考

- 优先级／用途：售后主流程参考。
- 实际 remote：`https://github.com/WangWeiqiang-UCAS/E-commerce-Smart-Agent.git`。
- 本地目录：`../reference/vendor/E-commerce-Smart-Agent-WangWeiqiang/`。
- 冻结 SHA：[`c894f44bceeb61c5488df20defe7f9fe4dbb68b7`](https://github.com/WangWeiqiang-UCAS/E-commerce-Smart-Agent/tree/c894f44bceeb61c5488df20defe7f9fe4dbb68b7)；提交日期：`2026-01-19T11:26:43+08:00`。
- 选取依据：恢复 docs/REFERENCES.md 已记录快照；本次 clone HEAD 相同。
- 许可核对：未发现仓库级 LICENSE/COPYING/NOTICE 文件；仅做架构与流程参考和独立实现，不复制上游代码。
- 阅读目标与限制：查单、政策检索、退款申请、资格审核及转人工分流的图阶段参考。不得直接采用其金额、时限、到账措辞或写入逻辑；Ceres2 Python 业务权威与明确确认契约优先。
- 优先源码：
  - [`app/graph/workflow.py`](https://github.com/WangWeiqiang-UCAS/E-commerce-Smart-Agent/blob/c894f44bceeb61c5488df20defe7f9fe4dbb68b7/app/graph/workflow.py)
  - [`app/graph/nodes.py`](https://github.com/WangWeiqiang-UCAS/E-commerce-Smart-Agent/blob/c894f44bceeb61c5488df20defe7f9fe4dbb68b7/app/graph/nodes.py)
  - [`app/graph/state.py`](https://github.com/WangWeiqiang-UCAS/E-commerce-Smart-Agent/blob/c894f44bceeb61c5488df20defe7f9fe4dbb68b7/app/graph/state.py)
  - [`app/services/refund_service.py`](https://github.com/WangWeiqiang-UCAS/E-commerce-Smart-Agent/blob/c894f44bceeb61c5488df20defe7f9fe4dbb68b7/app/services/refund_service.py)

### 7. NanGe LangGraphChatBot

- 优先级／用途：售后主会话／持久化参考。
- 实际 remote：`https://github.com/NanGePlus/LangGraphChatBot.git`。
- 本地目录：`../reference/vendor/langgraph-chatbot-nange/`。
- 冻结 SHA：[`30621c9243ef2e15f25eff1be94f5c7491090f1b`](https://github.com/NanGePlus/LangGraphChatBot/tree/30621c9243ef2e15f25eff1be94f5c7491090f1b)；提交日期：`2025-04-14T11:46:16+08:00`。
- 选取依据：恢复 docs/REFERENCES.md 已记录快照；本次 clone HEAD 相同。
- 许可核对：未发现仓库级 LICENSE/COPYING/NOTICE 文件；仅做架构与流程参考和独立实现，不复制上游代码。
- 阅读目标与限制：多轮客服、线程内 checkpoint、跨线程 Store、RAG 路由的学习参考。不能把该项目运行能力、数据库或退款授权视为 Ceres2 已拥有。
- 优先源码：
  - [`README.md`](https://github.com/NanGePlus/LangGraphChatBot/blob/30621c9243ef2e15f25eff1be94f5c7491090f1b/README.md)
  - [`02_ChatBot/demoWithMemory.py`](https://github.com/NanGePlus/LangGraphChatBot/blob/30621c9243ef2e15f25eff1be94f5c7491090f1b/02_ChatBot/demoWithMemory.py)
  - [`03_ChatBotWithPostgres/demoWithMemory.py`](https://github.com/NanGePlus/LangGraphChatBot/blob/30621c9243ef2e15f25eff1be94f5c7491090f1b/03_ChatBotWithPostgres/demoWithMemory.py)
  - [`04_RagAgent/demoRagAgent.py`](https://github.com/NanGePlus/LangGraphChatBot/blob/30621c9243ef2e15f25eff1be94f5c7491090f1b/04_RagAgent/demoRagAgent.py)

### 8. Mem0

- 优先级／用途：可选：记忆提取／更新／去重边界。
- 实际 remote：`https://github.com/mem0ai/mem0.git`。
- 本地目录：`../reference/vendor/mem0/`。
- 冻结 SHA：[`abb81c88e1f738a8117d8293530fbc31a5ef8fd9`](https://github.com/mem0ai/mem0/tree/abb81c88e1f738a8117d8293530fbc31a5ef8fd9)；提交日期：`2026-10-01T21:46:18+05:30`。
- 选取依据：恢复 docs/REFERENCES.md 已记录的研究 SHA；没有追随新默认分支。
- 许可核对：LICENSE 存在，Apache-2.0。
- 阅读目标与限制：当前仅作记忆能力参考，不是当前 01 依赖；Ceres2 未采用 Mem0 引擎。
- 优先源码：
  - [`README.md`](https://github.com/mem0ai/mem0/blob/abb81c88e1f738a8117d8293530fbc31a5ef8fd9/README.md)
  - [`mem0/memory/main.py`](https://github.com/mem0ai/mem0/blob/abb81c88e1f738a8117d8293530fbc31a5ef8fd9/mem0/memory/main.py)
  - [`mem0/configs/prompts.py`](https://github.com/mem0ai/mem0/blob/abb81c88e1f738a8117d8293530fbc31a5ef8fd9/mem0/configs/prompts.py)

### 9. Graphiti

- 优先级／用途：可选：时态与记忆来源表达。
- 实际 remote：`https://github.com/getzep/graphiti.git`。
- 本地目录：`../reference/vendor/graphiti/`。
- 冻结 SHA：[`b7fc30f2a1e288266760640164a37bdb7d1d0f28`](https://github.com/getzep/graphiti/tree/b7fc30f2a1e288266760640164a37bdb7d1d0f28)；提交日期：`2026-10-04T17:43:26Z`。
- 选取依据：恢复 docs/REFERENCES.md 已记录的研究 SHA；没有追随新默认分支。
- 许可核对：LICENSE 存在，Apache-2.0。
- 阅读目标与限制：参考 episode、entity、edge 与时间关系；不引入图数据库或其检索运行时，不阻塞当前 01。
- 优先源码：
  - [`README.md`](https://github.com/getzep/graphiti/blob/b7fc30f2a1e288266760640164a37bdb7d1d0f28/README.md)
  - [`graphiti_core/graphiti.py`](https://github.com/getzep/graphiti/blob/b7fc30f2a1e288266760640164a37bdb7d1d0f28/graphiti_core/graphiti.py)
  - [`graphiti_core/nodes.py`](https://github.com/getzep/graphiti/blob/b7fc30f2a1e288266760640164a37bdb7d1d0f28/graphiti_core/nodes.py)
  - [`graphiti_core/edges.py`](https://github.com/getzep/graphiti/blob/b7fc30f2a1e288266760640164a37bdb7d1d0f28/graphiti_core/edges.py)

### 10. Supermemory

- 优先级／用途：可选：公开 SDK／MCP 接缝。
- 实际 remote：`https://github.com/supermemoryai/supermemory.git`。
- 本地目录：`../reference/vendor/supermemory/`。
- 冻结 SHA：[`ac2180498223cce078eb263b9d240fdc2f5c3548`](https://github.com/supermemoryai/supermemory/tree/ac2180498223cce078eb263b9d240fdc2f5c3548)；提交日期：`2026-10-05T00:27:04Z`。
- 选取依据：恢复 docs/REFERENCES.md 已记录的研究 SHA；没有追随新默认分支。
- 许可核对：LICENSE 存在，MIT。
- 阅读目标与限制：研究公开接口和上下文工具；公开仓不是完整核心服务的证明，不接入外部服务，不阻塞当前 01。
- 优先源码：
  - [`README.md`](https://github.com/supermemoryai/supermemory/blob/ac2180498223cce078eb263b9d240fdc2f5c3548/README.md)
  - [`apps/mcp/src/server/server.ts`](https://github.com/supermemoryai/supermemory/blob/ac2180498223cce078eb263b9d240fdc2f5c3548/apps/mcp/src/server/server.ts)
  - [`apps/mcp/src/server/tools/add-memory.ts`](https://github.com/supermemoryai/supermemory/blob/ac2180498223cce078eb263b9d240fdc2f5c3548/apps/mcp/src/server/tools/add-memory.ts)
  - [`apps/mcp/src/server/prompts/context.ts`](https://github.com/supermemoryai/supermemory/blob/ac2180498223cce078eb263b9d240fdc2f5c3548/apps/mcp/src/server/prompts/context.ts)

### 11. Letta 入口

- 优先级／用途：可选：官方当前源码身份。
- 实际 remote：`https://github.com/letta-ai/letta.git`。
- 本地目录：`../reference/vendor/letta/`。
- 冻结 SHA：[`5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a`](https://github.com/letta-ai/letta/tree/5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a)；提交日期：`2026-09-10T10:59:06-07:00`。
- 选取依据：恢复 docs/REFERENCES.md 已记录快照；本次 clone HEAD 相同。
- 许可核对：LICENSE 存在，Apache-2.0。
- 阅读目标与限制：该冻结快照是当前项目入口，README 指向 letta-code；旧 V1 API server 在 archive 分支，不得以旧架构冒充当前实现。
- 优先源码：
  - [`README.md`](https://github.com/letta-ai/letta/blob/5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a/README.md)
  - [`LICENSE`](https://github.com/letta-ai/letta/blob/5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a/LICENSE)

### 12. Letta Code

- 优先级／用途：可选：Agent／记忆／工具边界。
- 实际 remote：`https://github.com/letta-ai/letta-code.git`。
- 本地目录：`../reference/vendor/letta-code/`。
- 冻结 SHA：[`f898fda60932b34ddbcfd389ea414515b0a5d272`](https://github.com/letta-ai/letta-code/tree/f898fda60932b34ddbcfd389ea414515b0a5d272)；提交日期：`2026-10-04T16:38:39-07:00`。
- 选取依据：恢复 docs/REFERENCES.md 已记录的研究 SHA；没有追随新默认分支。
- 许可核对：LICENSE 存在，Apache-2.0。
- 阅读目标与限制：按 Letta 入口追溯实际当前源码，参考上下文、技能与工具审批接缝；不引入 Letta 服务或 runtime，不阻塞当前 01。
- 优先源码：
  - [`README.md`](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/README.md)
  - [`src/agent/context.ts`](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/agent/context.ts)
  - [`src/agent/client-skills.ts`](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/agent/client-skills.ts)
  - [`src/agent/check-approval.ts`](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/agent/check-approval.ts)

## 版本选择与恢复规则

1. Mu 与 learn-claude-code 对应本轮 Kev 规划固定版本。它们提供可参考接缝，不提供可直接启用的业务预检索去重，也不继承其延迟或安全结论。
2. Pi 的依据是 Ceres2 的 [package.json](../../runtime/pi/package.json)、[package-lock.json](../../runtime/pi/package-lock.json) 和此次已安装包身份核对；发布 gitHead 的已有证据见 [运行时选型记录](../plans/ceres2-runtime-options.md)。源码阅读固定发布 SHA，并不把整个 monorepo 变成运行依赖。
3. Wang、NanGe 与四组记忆项目沿用 [既有参考注册表](../REFERENCES.md) 的研究 SHA；Letta 入口与 letta-code 分别保留。Hermes 是此次明确核对的官方来源。
4. 新工作区按每项实际 remote 克隆到相邻目录，再取得对应完整 SHA 并 detached checkout；只有核对该目录的 `remote get-url origin`、`rev-parse HEAD` 和工作树后，才能声称恢复成功。若历史 SHA 无法取得，记录阻塞，不用当前 main 静默替代。
5. 参考快照不要自动 `pull`。确需更新时先记录新 SHA、读取差异、说明对当前票据的影响，并更新此清单；不能借更新扩展实施范围。
6. 可发布内容只有本清单与主仓库中获准的实现／文档。不要添加 reference 子模块、把源码 vendor 到主仓库或推送这些镜像。

## 核对结果与未验证范围

12 个参考仓库均已拉取；实际 remote、完整 HEAD、committer 日期、根许可存在情况和上列源码路径已逐项核对。所有 checkout 为 detached HEAD，工作树未改动；无引用仓库的依赖安装或测试执行。此记录证明源码可阅读和来源可追溯，不证明任何上游可启动、兼容、合规、稳定或在 Ceres2 集成验收通过。

许可证只是固定快照的来源记录。将来确需复制代码时须逐文件确认适用许可并保留版权、LICENSE、NOTICE 等要求；没有建立复用许可的 Wang／NanGe 继续只做独立实现。图片、数据和嵌套项目不能仅凭根许可视为已授权。
