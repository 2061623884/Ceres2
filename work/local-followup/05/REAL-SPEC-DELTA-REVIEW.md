# 真实执行交付 Spec Delta 审查

审查范围：`fbb44854a412da8d77a7ec30426d240756a9d261...4008faacae169d18de80f6a444f59c47a93915b7`。只审真实执行结果与修复适用范围；未读取密钥、原始批次、私有验收题或 Standards 审查，也未运行验证。

## 结果适用范围

100 次真实结果仍是 HEAD `00b397443bd7258d2166c6445ac4ac066cefd21d`、工具源码 `739f13ead0c53ce9d82519efc30f51263e29ab45` 上的历史实测：66/30/4，不重跑、不改分。新 runner 只为未来执行把缺 plan 的 `confirm_plan` 从隐式 TypeError 改为明确 ValueError；外层仍输出 `runner_failed` 并保留 capture，普通无 plan 问答不进入该分支。[修复说明](REAL-REVIEW-RESOLUTION.md#L3) 第 3、7、13、15 行；[当前 runner](../../../backend/app/evaluation/run_baseline.py#L303) 第 303–307、376–381 行；受控用例同时覆盖失败 envelope、capture 保留和普通无 plan 回答：[测试](../../../backend/tests/test_local_followup_baseline.py#L866) 第 866–928 行。因此旧真实报告仍准确描述旧执行，不应据新诊断把该行改成 Guide/model failure 或通过。

## Unknown 与配置隔离

新 Graph 审计对未成功结果标为 `not_evaluated`，未观测指标保留 null；成功结果直接访问必需字段，合法空集合/零值仍按实际零计。Provider 汇总把无记录或缺失 token 保留为 unknown，观测到的零不丢失。[实现](../04/real-model-20261008/graph_audit.py#L32) 第 32–78、105–129 行；[harness](../04/real-model-20261008/provider_job.py#L79) 第 79–100 行；受控用例见[测试](../../../backend/tests/test_local_followup_real_harness.py#L51) 第 51–128 行。

环境 helper 按大小写不敏感清除当前 Settings aliases，再应用所选配置；serve 用例确认未继承 operator、写入暂停或 Kev 值，并保留 HOME/proxy。最新四模块回归记录为 35 passed/14.03s，关联 11 项源码清单；它只验证 synthetic env/fixture，不重放原始 100 行，也不是新真实模型、服务或浏览器证据。[最终受控回归](../01/tool-combined-after-real-harness-casefold-fix.md#L3) 第 3–13 行；[配置 helper](../04/real-model-20261008/harness_config.py#L20) 第 20–50 行。

## 未关闭项与结论

正式 Guide Graph 调用仍为 0、Kev 缺配、自然 Dream 为 0、人工 review 为 0，Firefox 旅程没有 Guide 调用；真实反馈闭环和本人 UI/自然度验收仍开放。[真实任务报告](../04/real-model-20261008/REAL-TASK-EVALUATION.md#L82) 第 82–86 行；[组件报告](../04/real-model-20261008/REAL-COMPONENT-VERIFICATION.md#L37) 第 37–45 行。窄修没有改变这些事实或把整体验收范围扩大。未发现本次 delta 的 Spec 不一致；整体 TASK 仍未验收。
