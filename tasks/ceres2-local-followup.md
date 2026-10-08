# Ceres2 本机后续开发

- 状态：进行中（本地受控实现/测试已完成，最终双轴审查准备；真实评测配置阻塞，尚未本人验收）
- 主责任：本机主会话，唯一协调分支、状态、文件责任和交付；专职 Tester 独占测试/构建/安装/运行验证，Standards/Spec 独立只读。
- 起点：`170fac0bc75fcc855897b073337ba218abeb5b7d`
- 分支：`codex/ceres2-local-followup-20261008`
- 工作树：`Ceres2-integration-20261008`
- 方案：[本机后续开发](../docs/plans/ceres2-local-followup-spec.md)
- 来源：[云端九票 TASK](ceres2-local-cloud-integration.md)、[Ubuntu 交接](../docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md)

## 当前状态与下一步

本机准备已完成，来源和实际验证见[冻结结果](../work/local-cloud-integration/local-acceptance-20261008/LOCAL-ACCEPTANCE-RESULTS.md)。该结果属于仍无新产品修改的 `170fac0`：真实 BGE/新 hybrid smoke、静态新库、受控 provider 的 Firefox HTTPS 旅程通过；并非真实模型质量或整体验收。

用户最新明确按implement-spec实施，完成后不合并先审阅；并要求参考Ceres1 `72bb1b99bf040c8b0bae5d026888bc059bc9423d`，以尽可能完整的测试/评测为主。分支已从170建立，旧amax/main现场保持独立。当前六个CLI与共享capture模块、三个测试模块及40公开用例已实现；专职Tester同一源码冻结执行26项全部通过，见[最终工具验证](../work/local-followup/01/tool-combined-final.md)。包含CLI→真实TCP FastAPI/Pi的受控模型smoke，不能视为真实provider质量通过。

参考适配见[Ceres1方法](../docs/ceres1-evaluation-reference.md)，分层验证见[覆盖计划](../work/local-followup/COVERAGE-PLAN.md)。40公开和20新验收已分别冻结，100次离线计划已生成：actual attempts0、not_run100、business unknown100，见[独立清单](../work/local-followup/04/ACCEPTANCE-MANIFEST.md)；原未执行误fail的报告与离线更正保留，不增加模型调用次数。下一步双轴审查，然后可信配置就绪时先核心pilot再续完整计划。产品优化按失败证据安排，订单后端只补阻碍闭环的问题。

现有产品与170非evaluation路径无差异；本机完整回归原始752 passed/4 failed。4个失败来自嵌套pytest/模型缓存环境，针对补验通过，原全量不改写全绿，见[产品回归](../work/local-followup/01/product-baseline-170-full.md)。Pi/frontend类型/构建、真实BGE18开发题、官方GraphRAG受控库另留版本，不加总。交接见[本地交接](../docs/LOCAL-CHANGES-HANDOFF.md)。

Tester已做新.env presence-only检查：主provider URL/key/model、Memory extraction/Dream及Kev均为空，真实采样/真实Graph/Memory执行缺条件；不读取原配置或泄漏值。用户已收到本机配置请求，其间继续离线实现。完成交付留独立分支供用户审阅，不执行合并。

## 实施票与依赖

- [01 Ceres1适配、用例与批次分析](ceres2-local-followup-01-evaluation-foundation.md)：待验收，受控实现/验证已冻结，最终审查待完成。
- [02 公共HTTP/SSE任务执行](ceres2-local-followup-02-public-baseline.md)：待验收，七条runner测试与受控真实API smoke完成。
- [03 完整回归与组件/浏览器覆盖](ceres2-local-followup-03-comprehensive-verification.md)：待验收，分层证据已留；全量环境失败和对应补验保持原记录。
- [04 真实评测与失败反馈](ceres2-local-followup-04-real-evaluation-feedback.md)：阻塞，真实配置缺失；100计划已生成但100未执行，更多售后/Memory driver未完成。
- [05 双轴审查与独立交付](ceres2-local-followup-05-review-handoff.md)：进行中，按01—04实际结果交付，未完成项不得冒充全实现。

## 验收

- [ ] Ceres1方法适配、公开任务/机器判分/自然度标签与独立验收职责明确；不读现有holdout。
- [ ] 同条件真实模型基线与必要 GraphRAG Local/Global 执行，保存版本/调用/错误证据。
- [ ] 有依据的产品修复/优化通过受影响回归与前后效果比较。
- [ ] 至少完成一次采集、人工标注、失败用例回归和版本对照的反馈闭环。
- [ ] 确认/重复提交/停止/SSE 恢复、Memory/Dream 剩余合同分别留证；未运行不写通过。
- [ ] 最终候选通过适用测试与两轴独立审查，用户本人接受 UI 和对话自然度。
- [ ] 提交独立可审阅分支，交接实际通过/失败/未执行及配置要求；不合并，等待用户审阅。

## 所有权与边界

主会话维护方案、TASK、分支与参考适配。followup_eval独占新evaluation compare/annotation/failure模块、公开用例/rubric与对应测试；followup_experience独占run_baseline与对应测试。test_optimization独占执行验证/组件与独立验收资料。共享schema/DB/migration/fixture/Pi/Prompt/前端未转交，无问题证据不得改动；新增实际缺陷先明确唯一owner。

新业务库、索引、模型缓存与凭据不入Git；所有交易/履约仍模拟。上一轮源码/受控证据保持版本，不继承为本轮验收。按用户最新要求不合并、不部署、不推送或修改原项目，不执行rebase/cherry-pick/force push；主会话仅协调本地提交。
