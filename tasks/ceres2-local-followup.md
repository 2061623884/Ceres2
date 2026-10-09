# Ceres2 本机后续开发

- 状态：进行中（当前Kev轮01技术门槛通过、新100基线已执行，人工标签待确认，后继产品修复/图对照及体验验收未完成；前次缺配66/30/4及已发布driver/harness窄修保留原版本，本轮不合并、不推送）
- 主责任：本机主会话，唯一协调分支、状态、文件责任和交付；专职 Tester 独占测试/构建/安装/运行验证，Standards/Spec 独立只读。
- 起点：`170fac0bc75fcc855897b073337ba218abeb5b7d`
- 分支：`codex/ceres2-local-followup-20261008`
- 工作树：`Ceres2-integration-20261008`
- 方案：[本机后续开发](../docs/plans/ceres2-local-followup-spec.md)
- 来源：[云端九票 TASK](ceres2-local-cloud-integration.md)、[Ubuntu 交接](../docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md)

## 当前状态与下一步

2026-10-09 用户已按to-spec/to-tickets明确认可[新规格](../docs/plans/ceres2-kev-quality-followup-spec.md)、三个测试入口和[10票依赖](../docs/plans/ceres2-kev-quality-followup-tickets.md)。正式票据已逐票发布，[04](ceres2-local-followup-04-real-evaluation-feedback.md#已确认纵切票据)按implement-spec执行，具体技术门槛与后继释放只在对应票据及04维护。[真实Kev导航/政策/浏览器证据](../work/local-followup/04/kev-followup-20261009/KEV-NAVIGATION-POLICY-RESULTS.md)与早期provider探针分开；采集器失败及未知项保留，不继承旧验收。原基线及已发布记录保留；本轮不合并、不推送、不改原工程。

前次真实评测交付的授权覆盖原工程`.env`中模型配置只读复用以及当时交付分支的常规推送：基础设施Tester限定字段注入隔离进程，使用新库和固定新索引，独立验收Tester20核心pilot后同版续100计划。原配置/旧运行状态不修改或迁入，凭据不进入工具输出/Git。实际证据写`work/local-followup/04/real-model-20261008/`，原0次计划及离线v1-v4记录保留。100次正式尝试结束：机器business 66 pass/30 fail/4 unknown，core60试次44/13/3、三次均business pass11/20；每轮15秒100/100。真实Guide终态另为66 completed/24 waiting_confirmation/9 failed/1 protected，不能和业务判分互相替代。唯一公开dev-01 trial3模型未给plan，声明确认步骤组装触发TypeError并保留为runner_failed；不删除/重跑来改善成绩。该报告/审查交付已普通push核实；当前新一轮按上段不推送。

本机准备已完成，来源和实际验证见[冻结结果](../work/local-cloud-integration/local-acceptance-20261008/LOCAL-ACCEPTANCE-RESULTS.md)。该结果属于仍无新产品修改的 `170fac0`：真实 BGE/新 hybrid smoke、静态新库、受控 provider 的 Firefox HTTPS 旅程通过；并非真实模型质量或整体验收。

用户最新明确按implement-spec实施，完成后不合并先审阅；并要求参考Ceres1 `72bb1b99bf040c8b0bae5d026888bc059bc9423d`，以尽可能完整的测试/评测为主。分支已从170建立，旧amax/main现场保持独立。当前六个CLI与共享capture模块、三个测试模块及40公开用例已实现；初次26项通过后两轴审查/Root自查定位指标、不可比较值与金额总和缺口，单一owner修复；delta新增金额诊断漏项也已补齐。最终代码`739f13ead0c53ce9d82519efc30f51263e29ab45`，专职Tester同一冻结29项全部通过/15.73s，见[最终工具验证](../work/local-followup/01/tool-combined-final-delta.md)。包含CLI→真实TCP FastAPI/Pi的受控模型smoke，不能视为真实provider质量通过。

参考适配见[Ceres1方法](../docs/ceres1-evaluation-reference.md)，分层验证见[覆盖计划](../work/local-followup/COVERAGE-PLAN.md)。40公开和20新验收冻结，旧100次离线计划/误fail/v1-v4更正保留在[独立清单](../work/local-followup/04/ACCEPTANCE-MANIFEST.md)；本次另生成真实新批次，见[正式报告](../work/local-followup/04/real-model-20261008/REAL-TASK-EVALUATION.md)。原739的[Standards](../work/local-followup/05/STANDARDS-FINAL-REVIEW.md)/[Spec](../work/local-followup/05/SPEC-FINAL-REVIEW.md)是原工具代码审查，不代替真实结果或新脚本/报告审查。[组件报告](../work/local-followup/04/real-model-20261008/REAL-COMPONENT-VERIFICATION.md)列实际Graph、90提取/合成Dream和独立Firefox；正式Graph0调用、Kev缺配和本人质量仍开放。[04剩余实施顺序](ceres2-local-followup-04-real-evaluation-feedback.md#后续实施顺序与可观察交付)按真实失败推进，不预写大后端或换模型提高分数。

现有产品与170非evaluation路径无差异；本机完整回归原始752 passed/4 failed。4个失败来自嵌套pytest/模型缓存环境，针对补验通过，原全量不改写全绿，见[产品回归](../work/local-followup/01/product-baseline-170-full.md)。Pi/frontend类型/构建、真实BGE18开发题、官方GraphRAG受控库另留版本，不加总。交接见[本地交接](../docs/LOCAL-CHANGES-HANDOFF.md)。

`00b397`工具交付时新.env为空，见[当时检查](../work/local-followup/05/FINAL-DELIVERY-CHECK.md)；本次限定原配置进程注入，主/提取/Dream均`deepseek-flash`，实际HTTP/SSE与组件调用已记录，不再以presence作为成功证据。Kev缺配仍实测error/not_configured；原.env不修改、新.env未被填密钥。报告完成后本交付分支常规推送，不合并。

## 实施票与依赖

- [01 Ceres1适配、用例与批次分析](ceres2-local-followup-01-evaluation-foundation.md)：待验收，受控实现/验证及最终审查已冻结。
- [02 公共HTTP/SSE任务执行](ceres2-local-followup-02-public-baseline.md)：待验收，原七条runner测试/受控真实API smoke、本次真实100采集及缺plan诊断的第八条runner验证完成。
- [03 完整回归与组件/浏览器覆盖](ceres2-local-followup-03-comprehensive-verification.md)：待验收，分层证据已留；全量环境失败和对应补验保持原记录。
- [04 真实评测与失败反馈](ceres2-local-followup-04-real-evaluation-feedback.md)：进行中，本次真实100报告已完成，业务失败/未知、Kev/图任务/更多driver/人工反馈仍待后续。
- [05 双轴审查与独立交付](ceres2-local-followup-05-review-handoff.md)：待验收，本次工具/报告两轴复审及源码/报告候选普通push读回核实完成；等待用户审阅，不关闭更广规格。

## 验收

- [x] Ceres1方法适配、公开任务/机器判分/自然度标签与独立验收职责明确；不读现有holdout。
- [x] 同条件真实模型基线与必要 GraphRAG Local/Global 执行，保存版本/调用/错误证据。本次正式100与独立Graph180s分别留证，不签生产图15s通过。
- [ ] 有依据的产品修复/优化通过受影响回归与前后效果比较。
- [ ] 至少完成一次采集、人工标注、失败用例回归和版本对照的反馈闭环。
- [ ] 确认/重复提交/停止/SSE 恢复、Memory/Dream 剩余合同分别留证；未运行不写通过。
- [ ] 最终候选通过适用测试与两轴独立审查，用户本人接受 UI 和对话自然度。
- [x] 提交独立可审阅分支，交接实际通过/失败/未执行及配置要求；源码/报告候选常规push已读回核实，见[回执](../work/local-followup/05/REAL-PUBLICATION-RECEIPT.md)；不合并，等待用户审阅。

## 所有权与边界

主会话维护方案、TASK、分支与参考适配。followup_eval/followup_experience为初次实现owner；review_fixes完成原739审查修复。real_runner_fix是本次真实结果之后driver/harness窄修的唯一owner，当前源码冻结于cbca；原模型任务/源码清单不覆盖为新版本。test_optimization独占执行验证/组件，独立验收Tester维护隔离样本与实际批次。[35项组合](../work/local-followup/01/tool-combined-after-real-harness-casefold-fix.md)属于4008；[最终5项](../work/local-followup/05/real-harness-final-signature-cleanup-green.md)仅验证后来提交到cbca的两处必填签名，不加总。[Standards](../work/local-followup/05/REAL-STANDARDS-FINAL-REVIEW.md)/[Spec](../work/local-followup/05/REAL-SPEC-FINAL-REVIEW.md)最终复审已完成，未重新采样/评分原100。共享schema/DB/migration/fixture/Pi/Prompt/前端未转交，无问题证据不得改动；新增实际缺陷先明确唯一owner。

新业务库、索引、模型缓存与凭据不入Git；所有交易/履约仍模拟。上一轮源码/受控证据保持版本，不继承为本轮验收。本轮按已确认规格仅只读复用原模型配置；不修改原工程、不合并、不推送、不部署、不执行rebase/cherry-pick/force push。主会话唯一协调本地提交，前次发布授权不扩大本轮范围，worker禁止自行发布。
