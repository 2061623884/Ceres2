# 真实模型交付 Spec 审查

审查范围：用户要求复用 amax 模型配置执行真实评测、补全报告并推送；对照 `docs/plans/ceres2-local-followup-spec.md` 与 TASK 04。只读审查候选提交 `fbb44854a412da8d77a7ec30426d240756a9d261`（基线 `00b397443bd7258d2166c6445ac4ac066cefd21d`）。未运行测试或复算评分。

## (a) 缺失或部分完成

真实任务报告完整区分了 100 次尝试、100 份 capture、99 个 `guide_run` 与 1 个 `runner_failed`；业务结果为 66 pass、30 fail、4 unknown，核心三次均过为 11/20，15 秒阈值 100/100。它也明确说明 critical 观察为零不能当作安全通过，且人工 review 为零、首个有用结果全为 unknown。见 [真实任务报告](../04/real-model-20261008/REAL-TASK-EVALUATION.md#L33) 第 33–50、64–68 行；[交付核对](REAL-MODEL-DELIVERY-CHECK.md#L15) 第 15–18 行。这满足了本次真实任务结果留证的要求。

更广的规格仍未完成：正式 100 个 Guide run 的 Graph 调用为零，Graph Local/Global 组件查询分别约 18.0/18.7 秒并使用 180 秒期限；Kev 未配置；正式提取有 90 个完成 job，但自然 Dream 为零，另一次 10 条合成输入的 Dream 不能替代自然生命周期；人工标注为零；Firefox 订单旅程的 Guide 调用为零。反馈闭环和本人 UI/自然度接受也未完成。见 [任务报告](../04/real-model-20261008/REAL-TASK-EVALUATION.md#L82) 第 82–86 行、[组件报告](../04/real-model-20261008/REAL-COMPONENT-VERIFICATION.md#L27) 第 27、33–45 行，以及规格第 73–91 行。这些缺口在交付中有如实披露，不能据此宣称整体规格验收。

## (b) 范围外扩

未发现超出授权的产品改动。新增 Firefox 仅覆盖产品到模拟订单流程，报告明确不把它算作 Guide 或模型验证；配置只读注入隔离服务，报告说明旧运行状态未迁入。它属于辅助证据，不关闭 Guide 浏览器验收。

## (c) 看似实现错误

执行器在没有 plan 时仍直接读取 `plan['plan_id']`：[run_baseline.py](../../../backend/app/evaluation/run_baseline.py#L303) 第 303–308 行。该路径导致公开 `dev-01:trial:3` 出现 TypeError。报告明确记为 runner 故障、未发送确认 HTTP、保留已有 capture，且将该行保留为 `runner_failed` / unknown，没有重跑或归作模型通过（真实任务报告第 50 行；TASK 04 第 28 行）。这会使该行的后续动作不可评，但当前报告没有掩盖其影响；本审查不要求改写原批次。

**结论：** 本次真实执行与报告口径符合用户要求，失败、脚本故障和未测项均有披露。TASK 04 及整体规格仍为进行中；本审查不构成整体验收。
