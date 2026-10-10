# Spec review

固定比较：`170fac0bc75fcc855897b073337ba218abeb5b7d` → `e855d691d0a446c9e5385196134b55f2ec609320`；唯一提交 `e855d69 Add local evaluation workflow and versioned testing evidence`。

## 缺失／部分

- 报告汇总未满足规格指标：规格要求分别报告计划/尝试/完成/达标/失败、关键违规、逐轮 15 秒、首个有用结果、P50/P95、核心重复稳定性与 usage 覆盖（`docs/plans/ceres2-local-followup-spec.md:79`）。`backend/app/evaluation/report_batch.py:203-275` 汇总计划和 verdict、类别、核心三次 pass、延迟分位数、人工标签及 usage，但未汇总完成数、关键违规数、15 秒达标数或首个有用结果，因此真实采样后汇总报告仍缺这些要求。
- 真实评测与反馈闭环仍开放：规格要求真实采样、GraphRAG、标注到版本对照（`docs/plans/ceres2-local-followup-spec.md:23,65,73-85`）；TASK 明确 provider/Memory 配置缺失及订单/售后/Memory driver 未实现（`tasks/ceres2-local-followup-04-real-evaluation-feedback.md:3,16-18`）。离线清单为 100 planned、0 attempted、100 not_run、100 unknown（`work/local-followup/04/ACCEPTANCE-MANIFEST.md:31`）。这是已披露的阻塞/未完成项，不能记为通过；752/4 产品回归也未被重写为全绿（`work/local-followup/01/product-baseline-170-full.md:6,13`）。

## Scope creep

未发现超出 implement-spec 的行为范围。改动集中于评测执行/评分/比较工具、公开集与文档证据；任务所有权也将本轮限定在 evaluation 范围（`tasks/ceres2-local-followup.md:43`）。

## 看似实现但不正确

- 规格规定“缺失或非可比较值不算满足”（`docs/plans/ceres2-local-followup-spec.md:37`）。但 `backend/app/evaluation/score_batch.py:34-46` 对 `min`/`max`/`contains`/长度运算直接调用 Python 比较或 `len`；实际值类型不兼容时会抛 `TypeError`，中止整批，而不是记为不满足或证据不足。

只读审查；未运行测试、评分或服务命令。
