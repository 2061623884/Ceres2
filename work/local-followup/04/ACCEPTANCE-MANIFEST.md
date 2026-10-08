# 独立验收集清单

- 验收用例数量：20
- 验收集版本：`ceres2-local-followup-independent-acceptance-2026-10-08-v1`
- 验收集 SHA-256：`99134c5c4394e9319fcaeeb73736366c62e07b428206733af48c29f25fd74476`
- 60 条组合包版本：`ceres2-local-followup-60-case-bundle-2026-10-08-v1`
- 60 条组合包 SHA-256：`107bdb6d70d1731719c061a30c2a295b5d218d7732075fbdfcdd9b965c87b1d5`
- 原公开回归集版本：`ceres2-local-followup-dev-2026-10-08-v2`，40 条，SHA-256：`032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d`
- 新增验收集类别统计：`{"mixed_purchase_policy": 1, "policy": 6, "product_selection": 4, "purchase_planning": 4, "recipe_facts": 3, "routing": 2}`
- 新增集切分：全部 `split=acceptance`、`core=false`；40 条公开回归用例在组合包中保持原有字段与切分。

## 分离依据与限制

新增用例从 Ceres2 当前静态商品、Offer、菜谱和政策事实重新编写，加入多菜共享食材合并、菜谱需求到销售包装的覆盖与余量、多条目预算报价、跨商品单位价格比较、属性证据未知、具体订单角色边界和订单状态政策分界等约束。用例正文仅保存在受忽略的独立工作目录，公开 evals 未改动。

该集与公开回归集共享产品目录、政策体系及部分上位任务类型；本地 Tester 已能查看公开集，因此不能称严格盲测。多商品规划、预算、菜谱事实、政策查询、角色路由等场景族存在有意覆盖重合；结果只能作为本轮独立维护的验收样本，不能单独证明统计泛化。当前仅定义离线计划，真实 provider、真实模型与用户本人质量判断仍未执行。

## 离线计划评分证据

原始 100 条计划批次保留在 `work/local-followup/tmp/independent-acceptance/batch-plan-100.json`，SHA-256 为 `01f203014a7e3faaf6dee1672c1de0b4cbbfff54ed0d7c42363dc77499d1acd8`；组合包字节 SHA-256 为 `107bdb6d70d1731719c061a30c2a295b5d218d7732075fbdfcdd9b965c87b1d5`。原 `score-plan-100.json` 与 `report-plan-100.json` 作为首次评分记录保留；首次结果将未运行的路由检查计为 8 个业务失败，未手工改写。

评分器修复后，仅对同一组合包和原批次执行离线重评分，产物为 `score-plan-v2.json` 与 `report-plan-v2.json`。修复后的 `backend/app/evaluation/score_batch.py` SHA-256 为 `464c7130ed8e8f13287b88b41e8ca8572d344b6381e79445061e76bc2c973e9a`；`backend/app/evaluation/report_batch.py` SHA-256 为 `3775cbf968dc574ebdcd171a123bf381af75c4dfeff10a42e08a722c917c702f`。

使用的离线命令（工作目录 `backend/`）：

```sh
../.venv/bin/python -m app.evaluation.score_batch --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --batch ../work/local-followup/tmp/independent-acceptance/batch-plan-100.json --output ../work/local-followup/tmp/independent-acceptance/score-plan-v2.json
../.venv/bin/python -m app.evaluation.report_batch --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --batch ../work/local-followup/tmp/independent-acceptance/batch-plan-100.json --score ../work/local-followup/tmp/independent-acceptance/score-plan-v2.json --output ../work/local-followup/tmp/independent-acceptance/report-plan-v2.json
```

修复后报告计数为 planned 100、attempted 0、not_run 100、Guide runs 0；业务 verdict 为 pass 0、fail 0、unknown 100。此处只离线重评分与汇总，未重新生成批次、发 HTTP 请求或调用真实模型；真实模型状态仍为 `not_run`。
