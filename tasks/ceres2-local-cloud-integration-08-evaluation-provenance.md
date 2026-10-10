# T08：统一评测事件与运行版本

- 状态：待验收（技术实现与受控门槛完成；实际浏览器/真实provider/用户本人验收未完成）
- 负责人：evaluation/runtime owner (T06→T08 交接)；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T05 本地界面适配新入口与协议](ceres2-local-cloud-integration-05-integrated-ui.md)；[T06 显式 GraphRAG 与规范菜谱事实](ceres2-local-cloud-integration-06-explicit-graphrag.md)；[T07 售后数量照片与工单证据范围](ceres2-local-cloud-integration-07-aftersales-ticket-evidence.md)

## 最终当前结论（2026-10-07）

本票技术实现已进入最终产品 `f963017587b3eab30965ffcd3aab90fcc3852f3e`，受控验证/两轴修复闭环见[最终报告](../work/local-cloud-integration/t09/FINAL-VERIFICATION.md)。全量746通过/5跳过属于`81b02f9`；同版知识环境补齐跳过项，最终狭窄修复183例及合入4例另行绑定，不声称最终pin重新全量。实际浏览器BLOCKED、真实provider/用户本人验收NOT RUN，不能把技术完成等同于整体验收。

以下阶段记录按各自固定pin保留，旧“待实现/待交接”等描述属于历史过程，不推翻本节当前结论。

## What to build / 合同

policy judgment/lookup/reuse/summary、model usage、retrieval、graph retrieval、interim 审校独立计数；未知保持 null/unknown；真实 runtime version 在运行时记录，export source snapshot 只代表导出时；显式 owner 导出/人工标签，无自动质量正标签。

## 验收

- [x] 以上端到端业务合同完整实现，保留来源与安全边界。
- [x] 运行事件→导出→人工标签：usage 去重/缺失、事件尾裁剪计数、runtime/export 版本不同、owner join、失败登记不自动训练，安全输出无凭据。
- [x] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [x] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [x] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

主会话批准按下述A/B阶段细化工程依赖，A阶段先实施；整票依赖未提前解除。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。


## 同票工程依赖细化：A 导出/标注，B 运行时采集

T08-A 可在当前既有 runtime_summary/receipt/event/message 合同上独立实施，由 prepare_evaluation_integration 唯一维护新增 backend/app/evaluation/__init__.py、export_runs.py、annotate_runs.py，以及独立新增 tests/test_integration_evaluation_export.py、tests/test_integration_evaluation_annotations.py。这是已有 incoming CLI入口的选择性移植和修复，不新增生产HTTP路由/权限，也不改变已有业务数据。

A阶段覆盖显式owner过滤及精确run/request/session join、重复capture/annotation拒绝、人工标签null/显式赋值、读取持久化summary与独立详细tail、缺失时间/usage/runtime_version保持unknown、export_source_snapshot仅说明导出时源码。不得从tail补造完整计数，不从当前checkout倒填运行版本，不猜最近navigation关联；未具备运行采集证据的字段保持未知。只用合成测试库和固定JSONL验证；禁止读取真实运行库或导出用户原始数据。

禁止并写：runtime/、pi_product_runtime.py、pi_product_turn_service.py、Guide入口/schema、graph/knowledge、conftest.py、DB/model/migration、frontend。若A阶段确需共享接口调整，先协调唯一owner，不提前接管。仅新evaluation模块和独立测试，不能修改别人的冻结source。

T08-B仍严格等T06-B交回Pi/runtime，再补完整provider call identity/usage去重、完整summary与运行时版本采集，必要的Guide/DB变更需逐文件授权。T08整票仍依赖T05/T06/T07，A完成不解除T09、也不代替同版组合验证或两轴最终验收。

T06在canonical `b9138af` 固定postmerge12例及runtime build稳定通过，T08-B正式取得Pi/runtime/Prompt所有权；T06 owner停止写入。Guide入口/schema、shared conftest、DB/model/migration若需修改仍先逐文件确认。A候选`cb412db`独立审核，B以当前canonical为基继承A后同版验证。


## A 技术合入及 B 写入顺序

`cb412db` 11例GREEN无漂移、两轴clear后无冲突合入 `a60b6b5`；evaluation三模块及两份测试与受测pin相同。固定postmerge已交Tester；B的写入必须等该检查完成与Merger最终base交接，不能只因T06已交回runtime而提前写入。

A只接受当前policy/interim summary、owner过滤/精确join/显式人工标签/unknown及独立导出源码快照。B的新graph/provider summary schema投影和运行版本采集仍需独立实现/测试/复审。T05同版最终整合依赖保留。[验证](../work/local-cloud-integration/t08a/verification-summary.json)、[源码](../work/local-cloud-integration/t08a/source-equivalence.json)。

固定detached `a60b6b5` 导出/标注postmerge11例/3.73s通过、源码/harness无漂移。A技术门槛关闭，B正式接管runtime/Prompt及evaluation投影；此CLI-only检查未重新执行runtime，不替代B整合验证。[postmerge](../work/local-cloud-integration/t08a/postmerge-minimum.json)。

B所有权细化：guide_run_service.py转交用于已有receipt/event运行时证据，不新增schema/DB。navigation_service.py目前只读，须先说明确切调用需求再分配写入；frontend仍属T05。

最终B `c1a99cf`256例/321.10s受影响验证与build绑定稳定，两项观察范围/graph method P2均复审关闭。无冲突合入T05组合 `81b02f9`，backend/runtime与受测pin零差异；同版T09全量检查和全范围两轴已启动，不能将阶段256视作最终全量。[验证](../work/local-cloud-integration/t08b/verification-summary.json)、[build绑定](../work/local-cloud-integration/t08b/final-build-binding.json)。

- [ ] 剩余实际浏览器、获准的真实provider与用户本人验收按最终报告独立完成；不由受控结果自动勾选。
