# Ceres2 local-cloud integration

- 状态：进行中（T01/T02/T03/T07 已技术合入并发布；T04 与 T06 后端阶段进行中，最终验收开放）
- 主责任：主会话；集成分支唯一写入者为 Merger
- Spec：[规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- Workspace：[恢复说明](../CERES2-WORKSPACE.md)
- Baseline：`37c98400e7152b89e4a58f02fff3bceaa73b0eac`
- Incoming：`6734c7fe79e670df2dae12b065dcc49c0b10a307`，只读 frozen tag `ceres2-incoming-20261007-frozen`
- Local start：`b118dbea3852026c6a04c790b1e27df67c3c9c18`
- Common ancestor：`4bed9c891261e382122d424825b649989ea92c92`

## 九票任务图

- [T01 Hybrid 政策与有界预取复用](ceres2-local-cloud-integration-01-policy-hybrid-deadline.md)；阻塞：无
- [T02 Canonical 商品召回与当前 Offer](ceres2-local-cloud-integration-02-canonical-shopping.md)；阻塞：T01
- [T03 同 Pi 原生完成与混合引用](ceres2-local-cloud-integration-03-native-finish-mixed-refs.md)；阻塞：T01
- [T04 可选审校过程消息与 SSE](ceres2-local-cloud-integration-04-reviewed-interim-sse.md)；阻塞：T03
- [T05 本地界面适配新入口与协议](ceres2-local-cloud-integration-05-integrated-ui.md)；阻塞：T02, T04, T07
- [T06 显式 GraphRAG 与规范菜谱事实](ceres2-local-cloud-integration-06-explicit-graphrag.md)；阻塞：T02, T04
- [T07 售后数量照片与工单证据范围](ceres2-local-cloud-integration-07-aftersales-ticket-evidence.md)；阻塞：无
- [T08 统一评测事件与运行版本](ceres2-local-cloud-integration-08-evaluation-provenance.md)；阻塞：T05, T06, T07
- [T09 同版回归两轴审查与交接](ceres2-local-cloud-integration-09-integrated-verification.md)；阻塞：T08

初始 frontier 为 T01 和 T07：政策/知识与售后业务不互相依赖，共享模型/迁移由 T07 唯一持有。T01 后 T02 与 T03 可在不重叠文件的独立 worktree 并行；T03→T04 串行接管 runtime。T06 在 T02/T04 完成后接管图/runtime；T05 等 T02/T04/T07 后统一适配前端。T08 等全部功能来源就绪后统一观测；T09 做最终集成门槛。T04 所需事件时间迁移由 T07 owner 串行应用需求或以完成提交明确交接，不能自行抢写。未满足依赖的只读研究不等于开始实现。

## 唯一文件所有权与交接

- Merger：本 spec/TASK/各票/工作区恢复说明、集成分支及提交清单；不与 worker 同写产品文件。
- runtime/Prompt/公开 Guide schema：T01→T03→T04→T06→T08 串行交接。包括 pi_product_runtime、pi_product_turn_service、worker、prompt-modules、experience、Guide schema 与共享 fixture。T02/T07 若需其中接口，先交给当期 runtime owner，不能并发改 hunk。
- knowledge core/hybrid/policy/source version 与依赖锁：T01；T02 只读 core，负责 catalog/seed/静态商品菜谱 fixture；T06 继承 core 后加入 graph/provider。没有消费方的 graph 脚手架不提前引入。
- canonical shopping：T02；runtime 接线由当前 runtime owner 协调，在提交交接后串行整合。
- DB/model/migration：T07 owner 独占 backend/app/migrations/__init__.py、backend/app/models/__init__.py 及其售后模型；T04 的 guide event time/message 需求交 T07 owner 串行登记，或在其提交后明确逐文件转交。T08 亦同。不得并发改 model 导入或 migration registry。
- frontend 全目录：T05 一名 owner，保留 incoming UI 并统一接入；T07 不并行移植 UI，只交付后端合同。
- evaluation：T08；测试 fixture 由各票唯一实现 owner 写、Tester 执行，共享 conftest 先单独分配。
- Tester：全部 install/test/lint/typecheck/build/受控执行；Standards 与 Spec 各独立只读。Merger 不跑验证命令。

## 已核实来源与范围

读过 cloud `docs/JUDGE-PREFETCH-HANDOFF.md` 与 incoming `docs/LOCAL-CHANGES-HANDOFF.md`、当前 AGENTS/issue-tracker/domain/两份 ADR。incoming 旧 CURSOR 文档是历史，不扩大本轮授权。

Git 静态计数：baseline→incoming **340** 个变更路径；local-start→incoming **224** 个路径；后者限定 `backend/ runtime/ frontend/ data/fixtures/` 为 **63**；进一步仅 app/src/fixtures 为 **53**。因此 63 不是两个分支间全部差异，也不是原主工作树 53 dirty。

来源清单：[incoming 变更](../work/local-cloud-integration/incoming-changed-paths.txt)、[63 路径](../work/local-cloud-integration/incoming-code-and-fixture-paths.txt)、[baseline 对比](../work/local-cloud-integration/baseline-incoming-changed-paths.txt)。清单只记录文件名，不读取 holdout 内容。

## 当前证据与下一步

T01 与 T07 核心已按下文固定 pin 受控验证并合入；T02/T03 分片正在实施，T07 Mercury 已通过独立两轴复审并合入，postmerge 最小验证已通过。来源历史成绩不继承；完整九票同版回归、真实验证与用户验收未完成。发布由主会话协调授权工具，绝不合并 main 或修改原分支。

## 已绑定工作者

- Merger / 正式 TASK：prepare_merge_workspace_spec。
- T01：design_policy_retrieval_bridge，独占政策/知识和本票所需 Pi runtime、Prompt、source/reuse 接线，交付后转给 T03。
- T07：implement_aftersales_evidence_slice，独占 mercury 售后/路由/tools/orders、human 服务/路由、orders API、checkout、售后模型及共享 model/migration registry；不写前端、政策、Pi runtime。
- Tester：plan_merge_verification_gates，唯一验证执行者。
- T01 如需 Mercury 查询 deadline 接线，必须给 T07 owner 提交具体需求，由该 owner 写其文件；不得并发修改。

## Deadline 传递责任

T01：知识服务接口及 Pi 政策路径；T02（prepare_shopping_filter_slice）：catalog/comparison/explore 调用链；T03：其余 Pi 上下文/工具协议；T06：菜谱/GraphRAG 调用链。运行内每一检索必须传递原绝对 deadline 和取消检查，不允许因 optional 参数漏传而重置 15 秒。普通产品 HTTP 自身请求预算明确创建一次并贯穿检索。参数只为实际 callsite 提供；共享接口变更由当前唯一 owner 实施，调用方逐个核对。T07 接收 T01 给出的 Mercury deadline 补丁需求。

## 静态来源前置提交

T01 corpus 实际消费五份 incoming 静态来源，而 T02 原计划迁入这些文件会形成实现循环。经主会话授权，Merger 精确迁入 incoming 五文件，供 T01 的索引/版本合同使用；offers/seed/current Offer 仍属 T02。本次不运行导入、索引构建或模型，不等于检索已实测。T01 已确认未写这些 fixture；后续转给 T02 前由主会话通知，双方不能并行改来源。

## T07 核心合入与当前边界

售后核心 `0ff65a0` 经 Tester 75 affected GREEN、两轴修复复审后无冲突合入 `5f592575`；产品 pin `0a6e8fa` 与合并结果 backend/runtime/frontend/data 无差异。已实现 nullable application.human_ticket_id 精确关联、合法图片解码与受限格式/尺寸，历史记录不猜测关联。核心通过不是 T07 整体完成；T01 合入后由 T07 owner 独占补 Mercury deadline/categories，然后验证才释放 T05，避免互等循环。后端业务 requirements/lock 仅 T07 持有，独立知识 requirements/lock 仅 T01；锁生成/安装/验证仅 Tester。

T01 conftest 的 controlled_policy_source 只允许 policy namespace；T02 接管后独占增加 product 专用受控 fixture，不取消 namespace 断言，不用政策假数据冒充商品。T03 仅独立 fixture、不并改 conftest。

重要更正：实际基线 Guide API 30 秒，Mercury 15 秒；T01 独占 Guide API 入口落实用户确认 15 秒，不改模型 token。新旧 30→15 必须明确报告，旧 30 秒性能样本不得当同条件对照。

## T01 技术放行与 frontier

`6ba93b2` 经165受影响用例、runtime typecheck/build、guard2及两轴修复复审后合入 `3ecf15e8`；产品目录与受测 pin 相同。T01 为待验收，实际 BGE质量、最终集成/本人验收仍开放。当前 frontier：T02 与 T03 并行；T07 owner 同时只写 Mercury deadline/category 调用链。T02独占 conftest 和商品/fixture调用链；T03独占 Pi上下文/工具/Prompt及独立test，双方不得共享文件。T01的policy/knowledge已冻结供消费，需要接口变更先协调owner，不私改。

T07核心postmerge最小检查在15c0ad6冻结工作树13passed无漂移，证据已记录；这不解除其Mercury接线或T05阻塞。直接 Guide15秒涵盖同步授权，独立navigation预检不共用跨请求预算，重放/重连不重置。


## 2026-10-07 恢复核对

恢复时 canonical 为 `ccf272b752f096ce0d80f7d0a4f29b19c05b0a77`，工作树干净。独立固定工作树上的 T01 postmerge 最小检查为18 passed，另有 runtime build 和实际 Node guard 2 passed；三份 capture 均无源码/harness 漂移。此检查不替代九票最终回归。

T02 恢复 pin `911a7a0`，catalog API/service 有两份保留中的未提交改动；T03 恢复 pin `90d1ac3`，干净。不得把更早分片 GREEN 当作这两个完整候选通过。T07 Mercury 产品 pin `79a7eff`、交接 `24ee4d0` 已有63 affected passed，尚无该 delta 两轴报告，故尚未合入或释放 T05。

最后已核实远端映射仍是 local `15c0ad6` → remote `5564ff1d6fe1916c9042c5cffabdbfdbb8cae2e7`。T01 `ccf272b` 发布载荷已准备，实际发布由主会话核实；载荷存在不等于推送成功。


T07 Mercury 两轴均 clear 后，`24ee4d0` 无冲突合入 `4616798`，产品目录与受测 `79a7eff` 零差异。固定 postmerge 最小验证已交 Tester；完成后可解除 T05 的 T07 依赖，T02/T04 仍各自必须完成。详情以 T07 TASK 为准。

T07 Mercury 固定 `4616798` postmerge 11 passed / 7.25s，无源码/harness 漂移；T05 的 T07 依赖已解除，T02/T04 依赖保持。此结果不等于完整最终验收。


实际源码集成依赖：T03 已借入 T02 早期提交，因而 T03 的 canonical 合入现在等待 T02 最终技术门槛。T03 的50例/typecheck/build分片通过不释放 T02 或 T04；详见 T03 TASK。不能通过只摘取部分提交继承完整候选的验证结论。

发布已核实：T01 local `ccf272b` → remote `d9c1520e1d251f129d53f2682bd86d5856cb8116`，tree `e80311dcee43e5957007dc865898c6de697c0e03`；T07 Mercury local `a465dcf` → remote `bbaadd3b7e4302d87a0365f8b891260dd03e2403`，tree `368c7f40cf2b8ca65bd7655b9505de1e174aa36d`。回执在 work/local-cloud-integration；不是 main merge 或最终验收。


T02/T03 组合 `8950b08` 已122例+Pi typecheck/build稳定通过并无冲突合入 `4fd13b3`；两轴无阻断，T02 留一个非阻断 helper 命名 P3待最终集中修复。与该组合相比仅已验过的 Mercury 三文件增量不同，固定 postmerge 已交 Tester。通过即释放 T04，不需等待发布。详细候选、来源等价及证据在各票。

固定 `4fd13b3` postmerge 独立锁离线安装/build与37例/45.43s通过，无源码/harness漂移。T04 的 T03依赖已解除并交接 runtime owner；T05/T06仍等待T04。所有受控与最终/真实/本人验收分开。

T06 工程依赖细化已批准：T02 放行后 backend-only knowledge/graph/provider/CLI/DishService 阶段可与 T04 并行；Pi 注册/refs/Prompt阶段仍严格等 T04 转交，T06整票/T08依赖不提前完成。唯一文件所有权、禁写范围与门槛见 T06 TASK。

T02/T03 已发布核实：local `d9cbb180380515d5d10d0b76fc1bbba299db7385` → remote `beb83658e991c7fc641828c94149ceb7fe18880a`，tree `2f83ca49ada9984ad6998a060b4b43ddfac397f3`。回执已保存，后续发布以此为基。当前 docs-only `333e0bd` 的 T06 阶段细化尚未单独发布，将随下一实际变更。

T06-A后端合入 `3069728`，固定postmerge47例/6.63s通过、源码/harness无漂移。A技术门槛关闭，T06-B仍等T04 runtime交接；真实BGE公开开发检索不替代真实图LLM与最终质量验收。
