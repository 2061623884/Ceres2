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

该集与公开回归集共享产品目录、政策体系及部分上位任务类型；本地 Tester 已能查看公开集，因此不能称严格盲测。多商品规划、预算、菜谱事实、政策查询、角色路由等场景族存在有意覆盖重合；结果只能作为本轮独立维护的验收样本，不能单独证明统计泛化。上文 v1–v4 记录的是不同版本下的离线计划重评分；其“真实模型未执行”仅适用于那些离线产物。后续实际运行的真实模型批次单独记录在本清单末尾及[真实任务评测报告](real-model-20261008/REAL-TASK-EVALUATION.md)，不覆盖此前离线证据。

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

在 v4 离线复核时，被忽略目录一级文件只新增 `score-plan-v4.json` 与 `report-plan-v4.json`；原 20 条正文文件名仍为 `acceptance-20.json`，该阶段未读取或改写题面。之后的真实模型任务评测按单独授权由唯一 Tester 读取原验收题面并执行，输入文件未改名或改写；后续公开材料仍只登记其版本/hash 与聚合结果。

## 实际模型任务评测批次（2026-10-08）

实际运行、评分与限制详见[真实任务评测报告](real-model-20261008/REAL-TASK-EVALUATION.md)。本节只登记批次身份与关键聚合数；v1–v4 的离线计划与评分文件均保留，不被本次执行覆盖。

- 源码工作树 HEAD：`00b397443bd7258d2166c6445ac4ac066cefd21d`；该次评测所固定的实现源码提交：`739f13ead0c53ce9d82519efc30f51263e29ab45`。运行事件中的 `loaded_code_equivalence=unknown`，不据此宣称精确运行时等价。
- 输入组合包：`ceres2-local-followup-60-case-bundle-2026-10-08-v1`，SHA-256 `107bdb6d70d1731719c061a30c2a295b5d218d7732075fbdfcdd9b965c87b1d5`。既有计划文件仍为 100 planned、0 attempted，SHA-256 `01f203014a7e3faaf6dee1672c1de0b4cbbfff54ed0d7c42363dc77499d1acd8`；实际执行写入新的 ignored batch，不覆盖此计划或 v1–v4 文件。
- 实际批次 `work/local-followup/tmp/independent-acceptance/real-live-batch.json` SHA-256 `db0b98e3adce9879644bf7fabeea90b6ab928885424ce5b917a3204e77d87918`；score SHA-256 `3c3b74f1d3ed189b12875897ff7a61926eb21689ddca9625f6838aa740cb96f7`；report SHA-256 `dde87227d4f38085c07dc78448c696252c559e26ae3c05b835e4efb94a10cb5a`。pilot20 score/report SHA-256 分别为 `525ccbc89dcb8f1cb3d771a1a9d981984520472ffc06f235e60714d31287e6aa` 与 `81b319a4445d867df03b5e33e8ffffe76bc3236d2066eb6f1bd7dd0f757c6963`。
- 100 planned / 100 attempted / 0 not_run；阶段结果 `guide_run=99`、`runner_failed=1`。100 个执行行均保留 Guide receipt/capture，终态是 completed 66、waiting_confirmation 24、failed 9、protected 1。业务 verdict 是 pass 66、fail 30、unknown 4。该“runner_failed”是模型没有返回依赖后续确认动作所需的 plan，runner 在构造该动作时出现 TypeError；原执行未重跑，详见报告。
- 关键违规 findings 为 0，计算分母为 99 个可评分执行行；这不是 100 条均无风险或安全性通过的结论。15 秒时限样本 100、通过 100；核心集 20 个案例各运行 3 次，严格三次业务全通过为 11/20，核心业务 verdict 汇总 pass 44、fail 13、unknown 3。人工 reviewed=0，first useful result unknown=100。
- `message.interim` 实际出现在 39/100 个 run（43 个 SSE interim 事件）；33 次在 `turn.completed` 前，6 次在 `error` 终态前，均先于该 run 的 stream closure。该数只描述消息事件与时序，不代表 interim 有用、自然或质量合格。
- 捕获到 409 条 provider-call usage 记录；input/output/totalTokens/cacheRead 的实际 provider SSE 观测和分别为 2,200,915 / 28,452 / 2,229,367 / 2,030,720，cacheWrite 在 409 条均为 null。96/100 run 的 provider-call summary 完整，但 full usage field completeness 为 0/100；值是已观察下界，不能当作完整任务 token/cost。
- 100 行真实任务分为公开执行 80 行与独立验收 20 行。公开部分 verdict 为 pass 55、fail 22、unknown 3；独立验收只记录聚合 verdict pass 11、fail 8、unknown 1，不在本清单或报告披露其题面、标识或逐项结果。
- 实际模型为 DeepSeek Flash（`deepseek-flash`，API host `api.deepseek.com`）；非 secret 配置 SHA-256 `f1bd1b5983a0a07206a4bb1f549130b4a8b8b49afcb7b0bef845634503f2cbec`。密钥不写入清单、报告或 Git。
- 本次实际模型评测并不等于整体验收：浏览器端到端、人工自然度/有用性标注仍未完成。KEV 未配置，角色路由用例没有真实 Kev 判断；GraphRAG 构建与独立 query smoke 虽成功，但 100 个 Guide 任务中的 Graph 调用数为 0。
