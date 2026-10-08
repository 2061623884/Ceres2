# Spec final review

固定 delta：`4e021e46e8c16671ae1366ec09c11f39bad01bd6` → `739f13ead0c53ce9d82519efc30f51263e29ab45`；总体起点 `170fac0bc75fcc855897b073337ba218abeb5b7d`。

## 缺失／部分

- 初审的报告字段缺口已修：Guide 终态、critical 违规及分母、逐轮 15 秒和核心 trial 稳定性均有汇总（`backend/app/evaluation/report_batch.py:369-394`）。首个有用结果仍明确为 unknown/null（`:375-385`）；规格允许未知保持未知，但实际测量尚未完成（`docs/plans/ceres2-local-followup-spec.md:79`）。
- 整体规格仍未完成：固定候选的 TASK 记载 100 计划、0 次真实尝试，以及 provider 配置缺失、真实 Graph/Memory 与更多订单/售后 driver 未完成（`tasks/ceres2-local-followup.md:17,21,28`；`tasks/ceres2-local-followup-04-real-evaluation-feedback.md:3,10-18`）。反馈闭环和本人验收也仍开放；不得据离线工具通过标为整体验收。

## Scope creep

未发现。金额核对对应规格的实际商品/数量/Offer 金额要求（`docs/plans/ceres2-local-followup-spec.md:77`）及 rubric 的合计和确认后购物车合同（`evals/ceres2-local-followup-rubric.md:21-23`）。

## 看似实现但不正确

本次复查未发现上述代码缺陷仍存在：已知行额现在独立参与 `selected_total_fen` 求和；缺行额仍留 evidence gap（`backend/app/evaluation/score_batch.py:439-468`）。成功 receipt 即使与请求 items 不符，仍继续核对购物车 Offer、行额和总额（同文件 `:185-253`）。不可比较检查值记录为 evidence gap 并继续后续检查/用例（同文件 `:383-395`）。

Tester 最新证据为 29 passed、15.73s；213 文件 manifest `8d3724cba223fb46bc46eb198aaf3a378c2096e1e930b4648fda6f5ee1b6aa1a`，本机源码 hash 与其列出的 scorer/test hash 一致（`work/local-followup/01/tool-combined-final-delta.md:17,21-33`）。本次只读复审，未运行测试或评分；真实评测和整体验收仍未完成。
