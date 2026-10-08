# Spec delta review

固定 delta：`e855d691d0a446c9e5385196134b55f2ec609320` → `4e021e46e8c16671ae1366ec09c11f39bad01bd6`；总体起点仍为 `170fac0bc75fcc855897b073337ba218abeb5b7d`。

## 缺失／部分

- 初审的报告指标缺口大体已修复：新增 Guide 终态、critical 违规及分母、逐轮 15 秒、核心 trial 业务/时延稳定性（`backend/app/evaluation/report_batch.py:286-389`）。首个有用结果字段诚实保留 unknown（同文件 `:375-385`），符合未知不猜测，但实际测量仍未实现；真实结果验收不能据此关闭。
- 真实采样与反馈闭环仍开放：TASK 记载 100 planned、0 attempted、100 not_run/unknown，且 provider 配置缺失、更多售后/Memory driver 未实现（`tasks/ceres2-local-followup.md:17,21,28`；`tasks/ceres2-local-followup-04-real-evaluation-feedback.md:3,16-18`）。这不是本次修复的代码缺陷，仍须保持未验收。

## Scope creep

未发现。金额核对落实“实际商品/数量/当前 Offer 金额”（`docs/plans/ceres2-local-followup-spec.md:77`），rubric 明确了方案合计及确认后购物车金额规则（`evals/ceres2-local-followup-rubric.md:21-23`）。

## 看似实现但不正确

- 方案合计在部分证据下漏判：规格要求 `selected_total_fen` 等于已选行 `line_total_fen` 之和（`evals/ceres2-local-followup-rubric.md:21`）。`score_batch.py:439-450` 仅在 quantity、unit_price、line_total 三者全有时才加入已知行额并维持可比较；若行额已知但 quantity 或 unit_price 缺失，合计不匹配会被降为 unknown，尽管该行额总和可核对。
- 成功 receipt 的 items 与请求不一致时，`score_batch.py:185-192` 走 mismatch 分支并跳过后续购物车价格/行额/总额检查；`evals/ceres2-local-followup-rubric.md:22` 要求对成功确认后的购物车逐项核对。虽然已有 critical 失败，具体金额违规会漏报。

初审 TypeError 问题已解决：`score_batch.py:383-395` 将不可比较值保留为 evidence gap 后继续，未知 operator 仍作为错误传播。Tester 新证据记录受影响工具组 29 项通过（`work/local-followup/01/tool-combined-reviewfix-final.md:17,25-33`）；本次只读复审，未运行验证命令。整体规格及真实质量仍未完成。
