# Ceres2 local-cloud integration

- 状态：进行中（规划已形成，产品尚未实施/验收）
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

规划阶段只执行 Git clone/show/diff/status 和文档写入，没有产品修改、安装、测试、build、服务启动或真实 API。当前所有集成测试均 not run；来源 558/441 等不继承。规划提交后主会话分配 worktree，按 frontier 实施。发布由主会话协调授权工具，绝不合并 main 或修改原分支。

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
