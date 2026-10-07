# Ceres2 本地能力与云端入口集成规格

日期：2026-10-07。用户已批准九票范围；本文件是本轮实现依据，不继承任一来源的验收成绩。状态只在总 TASK 和各票维护。

## Problem Statement

本地优化提供 hybrid、GraphRAG、原生完成、可选过程消息和模拟业务 UI；云端提供 Coco-only 入口、政策预取与请求内证据复用。两者从共同祖先分叉，共享 Pi/Python 接缝、政策版本和消息投影不兼容，不能整块覆盖功能提交。目标是在一个独立集成分支保留两侧已批准能力与安全边界。

## Solution

以云端固定版本为基线，按业务纵切逐票选择性移植本地能力。政策检索替换其证据来源而保留预取/复用；原生完成和可选经审校过程消息使用同一 Pi 请求；保留本地界面并适配新导航与完整混合结果；事实、权限、确认及事务仍由 Python 决定。

## User Stories

1. 作为可可用户，我希望新文字只做一次角色判断，并在 yes 时明确选择是否切换。
2. 作为可可用户，我希望 no、uncertain、timeout、error 都保留完整原文继续处理，且故障不伪装为 no。
3. 作为墨墨用户，我希望直接处理售后，回购物仅通过明确按钮，文字不触发 Kev 或隐式重放。
4. 作为混合请求用户，我希望购物、一般政策、职责边界与待澄清问题同时保留。
5. 作为政策询问者，我希望真实 hybrid 来源、范围、版本、空结果和错误有区别。
6. 作为同请求用户，我希望相同有效范围的成功或空证据复用，不重复查；不足、变更或失败可补查。
7. 作为购物用户，我希望召回后仍执行品类、审核与其他 canonical 条件，读取当前 Offer。
8. 作为用户，我希望同一 Pi 用 finish_response 结束，混合合法引用都经过 Python 校验。
9. 作为用户，我可以收到零条或多条经审校的过程消息，停止后不再发布，也不泄露推理或未证事实。
10. 作为刷新或重连用户，我希望稳定消息 ID、事件序号与终态避免重复气泡、重复写入。
11. 作为菜谱事实询问者，我希望人数、基准用量、必需/可选食材来自规范事实，不自动生成采购清单或加购。
12. 作为关系探索用户，我希望显式图查询可用官方 GraphRAG，模型选择与规范事实来源分别呈现和计量。
13. 作为模拟购物用户，我希望商品详情、明确加购、结算及订单顺序推进保留金额/商品快照。
14. 作为售后用户，我希望问题包装数量明确、照片受范围保护，确认后申请、回执和人工责任原子提交。
15. 作为人工处理者，我只能看到当前工单关联的申请和照片，不能获得同 case 后续代次或无关证据。
16. 作为评测者，我希望判断、检索、复用、主 Pi、审校、GraphRAG 与实际 provider usage 分开记录。
17. 作为评测者，我希望运行时版本与导出时源码区别明确，缺失时间、usage 和费用保持未知。
18. 作为项目维护者，我希望同版受控验证、两轴审查、真实验证和用户本人接受分别报告。

## Implementation Decisions

- Python 唯一业务身份/事实/授权/确认/事务权威；Node Pi 负责售前工具循环，LangGraph 负责售后。所有价格、库存、支付、退款与履约仅模拟。
- 保留 cloud 导航 ready/switch、capability=null、entry_judgment 与明确按钮语义。纯按钮不携带旧 routing_request_id，handoff=null；接受建议才续接对应原文一次。
- 政策来源升级使用真实 fixture/语料版本，保留来源语义；按真实知识快照更新所有调用方，旧全局常量不是兼容目标；缓存身份必须绑定实际来源版本、query/category/policy_scope/current request。跨版本与跨 owner/session/task/run 不复用。
- 成功和空证据都可复用；error 不伪装成 empty，失败允许补查。每个合法早期引用继续有效；单 policy_ref 与非空 policy_refs 同时兼容并逐项校验。
- 预取证据直接送入同一 Pi start envelope，不伪装成模型已调用工具。完整 runtime_summary 独立于裁剪后的详细事件尾部。
- 本轮确认整次处理预算为 15 秒、工具轮次为 5。实际基线 Guide API 是 30 秒，Mercury 是 15 秒；T01 必须通过公开 RED/GREEN 将 Guide 30→15，并贯穿异步/直接请求、预检和恢复。不能把这项变更说成基线原有 15 秒，也不能继承旧 30 秒性能对照。知识 worker 排锁、启动、写入、等待与读取必须消耗同一个剩余 deadline；incoming 无界锁及额外 30 秒等待不可照搬。超时/取消后不得发布或提交暂存业务。
- BM25/BGE/RRF 是候选证据，不是商品资格。canonical 条件在检索候选空间/最终验证保持，避免全局截断造成合法候选漏召回；当前身份、Offer 与库存必须重读。
- 原生 finish_response 在 guide_request 登记后的同一 Pi loop 完成；保留 cloud 按 kind 缩小上下文及工具授权，不恢复旧 capability 分流。主调用 auto 与原生完成配套，validator 的结构化要求独立保留。
- 可选 interim 必须经审校，独立稳定 message ID 持久化并发 SSE；不给固定气泡数、不增加额外主 Agent、不跨回合调度。私有 reasoning、工具参数和未经证据支持的事实不能发布。
- GraphRAG 是显式可选关系查询路径，确定性 recipe_facts 保留。图边不证明过敏安全、营养、替代或家中数量，不授权购买；缺索引/失败不能伪称已执行图查询。官方 Local/Global 与模型选择结果分别记录。
- 售后 quantity/photo/selection version/order/owner/case/责任代次必须校验。人工视图和照片读取以该 ticket 的实际关联证据为范围；仅以同 case/order 或小于 generation 过滤不等于精确工单关联。
- DeepSeek 仅规范化后精确官方 hostname api.deepseek.com 发送 thinking disabled，所有已有调用及新增 GraphRAG 路径适用。非官方/伪装域名不添加字段，缺省与 null 不等价。模型、provider、temperature、输出额度、重试和既有配置不变。
- DB/migration、共享 schema/fixture、runtime/Prompt 分别指定唯一维护者；同文件即使不同 hunk 也不并行写。依赖完成后以提交和文件清单交接。

## Testing Decisions

独立 Tester 唯一执行安装、测试、lint、typecheck、build 和运行命令；实现者按 TDD 准备回归用例、让 Tester 证明 RED/GREEN。最高接缝优先：公开导航/Guide HTTP/SSE、真实 Node JSONL 在受控 provider 下、canonical 商品与售后业务 HTTP、typed UI/DOM。复用现有 judge public/safety/reuse fixtures 的身份、版本、取消与终态断言，并扩展至 native finish/interim、hybrid/GraphRAG、售后照片和导出。禁止实现者读取独立 holdout。

最终受控整合在同一源码 pin：backend full、Pi typecheck/build、frontend strict TypeScript/build、受影响 DOM/浏览器旅程及官方域名 wire 回归。Tester 的全离线 guard 必须覆盖实际子进程，不得凭配置声称隔离。依赖缺失可以记录 blocked；不能用 source 单元假装真实 BGE、GraphRAG 或浏览器已通过。真实模型/API、真实数据库、原 .env 均不在本轮自动执行范围。两轴独立只读审查固定云端基线到整个集成分支三点 diff，历史报告不算集成通过。

## Out of Scope

不合并 main、不覆盖原分支或本地主工作树；不读取/迁入原 53 项 dirty、holdout、凭据、运行数据库、索引或 session；不启动真实服务或收费调用；不部署、不新增自主消息/提醒、不换模型/配置、不抬预算、不以历史测试作当前验收。

## Further Notes

本轮授权覆盖九票以及 incoming UI 的适配，替代旧 AGENTS 中“仅16票”“无remote”及旧四票文档中的“用户独自改前端”等本轮冲突范围；其原文字保留历史，不改写。分支可追踪发布由主会话使用授权工具协调，工作者不 shell push。明确权限、Tester 独占执行与禁止覆盖原工程仍适用。来源固定值、路径、文件清单和所有权在总 TASK 与工作区恢复说明，不把易变路径作为产品契约。
