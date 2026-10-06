# 参考项目：真正采用了什么，哪些只做研究

阅读路线：[README](../README.md) → [Ubuntu 接力](HANDOFF-UBUNTU.md) → 本文 → [TASK16](../tasks/ceres2-runtime-upgrade-16-integrated-verification.md)。

这是一份重点清单，不分发整套 reference/vendor 源码。链接与固定快照来自 2026-10-05 的源码研究记录；运行时身份来自当前锁文件、已安装包元数据和 Ceres2 imports。上游默认分支可能变化，应以列出的版本／SHA 为准。源码研究不等于上游已被运行、测试或接入。

## 1. 已采用的真实运行框架

### Pi：售前真实 SDK，不是仅借概念

- 仓库：[earendil-works/pi](https://github.com/earendil-works/pi)。当前实际依赖是 `@earendil-works/pi-agent-core@1.0.3` 和 `@earendil-works/pi-ai@1.0.3`；包元数据均指向此仓的 `packages/agent`、`packages/ai`，MIT。不要把别的同名 Pi 仓库当作锁定依赖。
- Ceres2 对应：[runtime/pi/package.json](../runtime/pi/package.json)、[worker.ts](../runtime/pi/src/worker.ts)、[Python adapter](../backend/app/services/pi_product_runtime.py)。真实 Node/Pi 负责售前模型／工具循环，Python 校验工具调用并承担业务事实与写入。
- 边界：SDK 在运行不等于指定 provider 已验证。当前一次 live 调用在比较阶段失败，诊断补丁未 live 重跑；见 [接力文档](HANDOFF-UBUNTU.md)。版本以 package-lock 为准；[运行时选型记录](plans/ceres2-runtime-options.md)记载 npm 发布 gitHead 为 `d78dc83d633229d12f8b79631384c4c2717c399f`，不要与更早研究快照混用；本次未重新查询 npm 元数据。

### LangGraph：售后真实图与 SQLite checkpoint

- 官方源码：[langchain-ai/langgraph](https://github.com/langchain-ai/langgraph/tree/main/libs/langgraph)、[checkpoint-sqlite](https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-sqlite)。当前锁定 `langgraph==1.2.12`、`langgraph-checkpoint-sqlite==3.1.1`，包元数据为 MIT。
- Ceres2 对应：[backend/requirements.lock](../backend/requirements.lock)、`backend/app/mercury/` 的售后编排。图负责流程与恢复，Python 业务服务负责 owner、资格、金额、明确确认、幂等提交和回执；checkpoint 不取代业务事实库。
- 边界：采用 LangGraph 库，不是部署下面的参考项目。受控图执行通过也不等于真实 qwen 或用户售后体验通过。

## 2. 主架构参考：独立实现，不直接复制

### WangWeiqiang-UCAS/E-commerce-Smart-Agent

- [仓库及研究快照 c894f44b](https://github.com/WangWeiqiang-UCAS/E-commerce-Smart-Agent/tree/c894f44bceeb61c5488df20defe7f9fe4dbb68b7)。重点看中文电商查单 → 退货申请 → 风险分流的纵向业务阶段。
- 对应 Ceres2：墨墨的只读调查、确定性提案、独立确认、提交与回执阶段边界。采用的是架构参考，非其业务代码、数据库或服务。
- 研究未建立仓库级代码复用许可，当前规格明确只做模式研究和独立适配，不复制代码、不宣称兼容。

### NanGePlus/LangGraphChatBot

- [仓库及研究快照 30621c92](https://github.com/NanGePlus/LangGraphChatBot/tree/30621c9243ef2e15f25eff1be94f5c7491090f1b)。重点看多轮客服、持久化与 RAG 设计。
- 对应 Ceres2：售后会话／恢复的设计参考；不意味着接入其整套 RAG、数据库或客服产品。当前 catalog 是 SQL 检索，没有单独向量索引可宣称已构建。
- 同样未建立仓库级代码复用许可；仅独立适配。主参考选择与边界见 [规格](plans/ceres2-proactive-upgrade-spec.md)。

## 3. LangGraph 工程辅助参考

- [JoshuaC215/agent-service-toolkit @ 88ebfa1f](https://github.com/JoshuaC215/agent-service-toolkit/tree/88ebfa1fadd1a207aa92115635abf7ed20d66a88)：研究 FastAPI lifespan、saver 初始化、SSE 和 interrupt 测试组织，映射到 Ceres2 服务生命周期与恢复验证。未整仓引入。其默认 SQLite saver 持久化不代表 Store 也持久化；普通 resume 不能直接当退款确认。[MIT 许可](https://github.com/JoshuaC215/agent-service-toolkit/blob/88ebfa1fadd1a207aa92115635abf7ed20d66a88/LICENSE)。
- [langchain-ai/react-agent @ f5520937](https://github.com/langchain-ai/react-agent/tree/f5520937686b06d7139a165e71af1b86e291b866)：研究 model ↔ tools 的最小显式图循环；映射到 Mercury 只读调查循环。模板本身没有 Ceres2 的 owner 隔离、明确确认或业务回执，未作为完整产品接入。[MIT 许可](https://github.com/langchain-ai/react-agent/blob/f5520937686b06d7139a165e71af1b86e291b866/LICENSE)。
- [官方客服 handoffs 教程](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs-customer-support)：阶段限定工具的模式参考，动态文档无固定 Git SHA。它不提供 Ceres2 的退款授权，也不等于真实人工工单系统；仅链接与模式概述，不宣称复制实现或完成部署。

## 4. 记忆系统：研究过，没有接入外部记忆引擎

Ceres2 当前用自己的 Python/SQLite 记忆记录、后台 job、模型提取、Dream、删除／更正及恢复逻辑。对应 [memory_service.py](../backend/app/services/memory_service.py)、[memory_background.py](../backend/app/services/memory_background.py)、[memory_model.py](../backend/app/services/memory_model.py)。当前 manifest/import 没有采用以下引擎；研究结论不能写成“已集成 Mem0／Graphiti／Letta”。

- [Mem0 @ abb81c88](https://github.com/mem0ai/mem0/tree/abb81c88e1f738a8117d8293530fbc31a5ef8fd9)：研究记忆提取、更新／去重和 API 边界；Ceres2 没有安装或运行 Mem0 引擎。[Apache-2.0](https://github.com/mem0ai/mem0/blob/abb81c88e1f738a8117d8293530fbc31a5ef8fd9/LICENSE)。
- [Graphiti @ b7fc30f2](https://github.com/getzep/graphiti/tree/b7fc30f2a1e288266760640164a37bdb7d1d0f28)：研究时态知识图谱／来源表达；Ceres2 没有采用其图数据库或检索运行时。[Apache-2.0](https://github.com/getzep/graphiti/blob/b7fc30f2a1e288266760640164a37bdb7d1d0f28/LICENSE)。
- [Supermemory @ ac218049](https://github.com/supermemoryai/supermemory/tree/ac2180498223cce078eb263b9d240fdc2f5c3548)：研究公开 SDK／UI／MCP 和接入边界。公开仓不等于完整核心服务源码，也未接入 Ceres2。[公开仓 MIT](https://github.com/supermemoryai/supermemory/blob/ac2180498223cce078eb263b9d240fdc2f5c3548/LICENSE)。
- [Letta 入口 @ 5bcdd177](https://github.com/letta-ai/letta/tree/5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a) 及其指向的 [letta-code @ f898fda6](https://github.com/letta-ai/letta-code/tree/f898fda60932b34ddbcfd389ea414515b0a5d272)：研究 agent runtime／记忆管理边界；两者身份分别核对，不能拿旧 Letta 架构冒充当前实现。Ceres2 未引入 Letta 服务或 runtime。[入口许可](https://github.com/letta-ai/letta/blob/5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a/LICENSE)、[letta-code Apache-2.0](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/LICENSE)。

## 5. 其他已研究候选与本项目迁移边界

以下只作辅助对照，不重新开放主参考选型，也不代表存在运行时依赖：

- [Mr-ZeLong/E-commerce-Smart-Agent @ c822b892](https://github.com/Mr-ZeLong/E-commerce-Smart-Agent/tree/c822b8924ca35da65f40a708dd42524f9c7a7479)：同源扩展版，多专员／审核队列／管理端参考；不能和 WangWeiqiang 版本算两套独立架构。未建立仓库级代码复用许可。
- [langgraph_fly_base @ c670d6fb](https://github.com/liuyanqun0815/langgraph_fly_base/tree/c670d6fb76b2fc8880cc739f74c12bd00c872bcf)：槽位采集、摘要确认和跨回合阶段控制参考。[Apache-2.0，另含 NOTICE](https://github.com/liuyanqun0815/langgraph_fly_base/blob/c670d6fb76b2fc8880cc739f74c12bd00c872bcf/LICENSE)。
- [agentic-customer-service-platform @ d2523b02](https://github.com/negativexq/agentic-customer-service-platform/tree/d2523b027f8280319ba22ec2e0ae1e981c5f79a2)：pending action、确认后重校验、幂等执行的辅助参考。[MIT](https://github.com/negativexq/agentic-customer-service-platform/blob/d2523b027f8280319ba22ec2e0ae1e981c5f79a2/LICENSE)。
- [GustoBot @ 09fadecd](https://github.com/skygazer42/GustoBot/tree/09fadecd87d7d0ddc80a78452b328ef57ec549a6)：行业客服研究候选，没有接入 Ceres2。[Apache-2.0](https://github.com/skygazer42/GustoBot/blob/09fadecd87d7d0ddc80a78452b328ef57ec549a6/LICENSE)；示例知识数据须另核对来源授权。

[原 Ceres @ e24debf6](https://github.com/2061623884/Ceres/tree/e24debf670db02a86cb79c40933b901827db8a55) 的 React 页面和必要接口契约是本项目选择性迁移来源，不能把旧工程测试、数据库或凭据继承为 Ceres2 验收。静态 catalog／Offer／图片来源与恢复哈希见 [migration ledger](../work/clean-rebuild/migration-ledger.md)。未将完整旧 backend/Mercury 或任何外部 reference 目录作为运行依赖。来源与图片哈希是可追溯记录，不构成第三方素材的笼统复用授权。

许可证信息是已核对快照的来源记录，不是对未来复制、分发或商业使用的笼统授权。若后续确需复用上游代码，必须逐文件核对适用许可并保留要求的版权／许可／NOTICE；无明确复用许可的主参考继续只做独立实现。
