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

## 最终评分器版本离线复核（v3）

最终 review-fix 提交 `4e021e46e8c16671ae1366ec09c11f39bad01bd6`（起点 `170fac0bc75fcc855897b073337ba218abeb5b7d`）更新了评分与报告模块。为核对最终版本，本次只对上述同一 60 条组合包与原始 100 条计划批次离线重评分和汇总；未生成新批次、读取 `.env`、发送 HTTP、启动 Guide 或调用模型。使用工作树自有 `.venv`，命令继承当前 `HOME`，没有覆盖它。

输入文件字节与前述 SHA-256 相同：组合包 `107bdb6d70d1731719c061a30c2a295b5d218d7732075fbdfcdd9b965c87b1d5`，计划批次 `01f203014a7e3faaf6dee1672c1de0b4cbbfff54ed0d7c42363dc77499d1acd8`。最终运行模块版本：`score_batch.py` SHA-256 `20e27571e8f65b08560275a3bc066302c14eb0a7dc76f038dbb203ab474d8ca7`；`report_batch.py` SHA-256 `59415a08949e4cbab7b86c4f6b28d4fc907f90c95a5126268019934bb7f175e5`。

工作目录为 `backend/`。两条命令均退出码 0：

```sh
../.venv/bin/python -m app.evaluation.score_batch --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --batch ../work/local-followup/tmp/independent-acceptance/batch-plan-100.json --output ../work/local-followup/tmp/independent-acceptance/score-plan-v3.json
../.venv/bin/python -m app.evaluation.report_batch --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --batch ../work/local-followup/tmp/independent-acceptance/batch-plan-100.json --score ../work/local-followup/tmp/independent-acceptance/score-plan-v3.json --output ../work/local-followup/tmp/independent-acceptance/report-plan-v3.json
```

生成文件位于被忽略的 `work/local-followup/tmp/independent-acceptance/`，没有加入 Git：

- `score-plan-v3.json` SHA-256：`cdc5c1b697c2c7085569fa133fa5e7bf0266765111d67ccd1702c917a8295198`
- `report-plan-v3.json` SHA-256：`ddaec0fa8a1ccbb07f196dfe319a1cf42d243892de4c98d7d7d6e429644677b7`

最终计数仍为 planned 100、attempted 0、not_run 100、Guide runs 0；100 条业务 verdict 均为 `unknown`，没有 `pass` 或 `fail`。输出 JSON schema 标识沿用 `ceres-local-followup-score-v1` 与 `ceres-local-followup-report-v1`；`v3` 是本次证据文件版本名，不是新增 schema 版本。

新增报告字段的边界也按最终代码核对：终态分布中的 observed Guide runs 为 0，各终态计数均为 0；critical violations 为 0，但其 execution denominator 也是 0，因此只能说明本批次没有可观察执行，不能据此称关键违规检查通过或系统安全。15 秒阈值记录为 15,000 ms，但 samples 为 0（pass、timeout 也为 0），所以时延没有测量。first useful result 的 samples 和 observed 均为 0、unknown 为 0、human_annotated 为 false；报告定义明确要求有人工有用性标注，进度事件及首段 interim/final 字节本身不构成有用结果。核心稳定性是 20 个计划案例，但没有已执行试次，不能称三次稳定。成本、provider usage 与 latency 均为未观测/无样本。

本次仅确认离线评分在 100 个未运行计划上保持未知态，并确认报告不会把零观测写成质量通过；它不增加模型执行量，也不关闭真实模型、用户体验或完整任务验收。

受忽略目录的一级文件名（仅清单，不含题目正文）：`acceptance-20.json`、`cases-60-bundle.json`、`batch-plan-100.json`、`score-plan-100.json`、`report-plan-100.json`、`score-plan-v2.json`、`report-plan-v2.json`、`score-plan-v3.json`、`report-plan-v3.json`。

## 最终金额诊断版本离线复核（v4）

金额诊断复审修复后的最终源码提交为 `739f13ead0c53ce9d82519efc30f51263e29ab45`（已在该提交上执行本次复核）。该提交的组合验证证据记录为 29 passed、1 warning、15.73 秒，见 [`tool-combined-final-delta.md`](../01/tool-combined-final-delta.md)。本次只用相同的 60 条组合包与 100 条原计划离线重评分和汇总，没有新建批次、发 HTTP、启动 Guide、读 `.env`、调用模型或覆盖此前版本；使用本地 `.venv`，`HOME` 沿用当前值。

输入摘要仍为组合包 SHA-256 `107bdb6d70d1731719c061a30c2a295b5d218d7732075fbdfcdd9b965c87b1d5` 和计划批次 SHA-256 `01f203014a7e3faaf6dee1672c1de0b4cbbfff54ed0d7c42363dc77499d1acd8`。最终源码：`backend/app/evaluation/score_batch.py` SHA-256 `cb255c4f6cdbe211dbad04d4425be77e14383da2f9080da44b9db50f068efb07`；`backend/tests/test_local_followup_evaluation.py` SHA-256 `4f218062ff96fcd87c01da59d61bd83b2a9c9dd3aadeda5a20fdbffb6208dbe7`；`backend/app/evaluation/report_batch.py` SHA-256 `59415a08949e4cbab7b86c4f6b28d4fc907f90c95a5126268019934bb7f175e5`。

工作目录为 `backend/`，两条命令各自退出码均为 0：

```sh
../.venv/bin/python -m app.evaluation.score_batch --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --batch ../work/local-followup/tmp/independent-acceptance/batch-plan-100.json --output ../work/local-followup/tmp/independent-acceptance/score-plan-v4.json
../.venv/bin/python -m app.evaluation.report_batch --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --batch ../work/local-followup/tmp/independent-acceptance/batch-plan-100.json --score ../work/local-followup/tmp/independent-acceptance/score-plan-v4.json --output ../work/local-followup/tmp/independent-acceptance/report-plan-v4.json
```

v4 产物保存在被忽略的临时目录，未加入 Git：`score-plan-v4.json` SHA-256 `cdc5c1b697c2c7085569fa133fa5e7bf0266765111d67ccd1702c917a8295198`；`report-plan-v4.json` SHA-256 `ddaec0fa8a1ccbb07f196dfe319a1cf42d243892de4c98d7d7d6e429644677b7`。两者与 v3 文件字节相同；v4 记录了最终金额诊断源码下的重新评分，而这份零执行批次没有产生新的业务证据。JSON 内 schema 标识仍为 `ceres-local-followup-score-v1` 和 `ceres-local-followup-report-v1`，`v4` 是证据文件版本标签。

实际计数：planned 100、attempted 0、not_run 100、Guide runs 0；业务 verdict 为 pass 0、fail 0、unknown 100。观察到的终态数为 0；critical findings 为 0、execution denominator 也为 0，不能当作关键违规检查通过。15 秒阈值为 15,000 ms、samples 0；first useful result 的 samples/observed/unknown 均为 0，`human_annotated=false`，没有人工效用结论。20 个核心案例均未执行，不能得出三次稳定性结论；provider usage、cost 和时延均无样本。

重查后被忽略目录一级文件只新增 `score-plan-v4.json` 与 `report-plan-v4.json`；原 20 条正文文件名仍为 `acceptance-20.json`，其正文未读取输出或改写。
