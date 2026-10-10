# 02 新环境基线 B0 冻结记录

冻结日期：2026-10-09。Root 已明确放行 02；Root 记录 01 formal controlled regression 为 GREEN，另给出指标字符串 `1/3.41s`（具体分母定义未提供），并释放 01 技术门槛。此记录固定本轮输入、评分规则和计划执行环境。未在本文猜填没有可读证据的运行时或配置字段；首个 pilot capture 若能观察到相关字段，将在 `02-PILOT.md` 单独记录，不回写本冻结记录。

## 代码与运行环境

- 工作树：`/data/amax/Documents/projects/Agent/Agent产品/Ceres2-integration-20261008`，branch `codex/ceres2-local-followup-20261008`。
- Git 冻结 HEAD：`f9d7b44870e447c1f592a12163ad443b17782980`；tree：`f6dd1554335b9da351a89ec825b3c6034d47c2e5`。该提交是相对 `9e9be1da8ef7dd7ba630a2025e63835612e4795e` 的 docs/state-only 更新。
- 当前隔离 Ceres API：`http://127.0.0.1:8017`，由现有 exec session `78420` 服务。服务由 `9e9be1da8ef7dd7ba630a2025e63835612e4795e` 启动，Root 报告实际 source/harness 来源为 `5b24c4b1c0fde053e46c916e8b4e935fb54eb7c9`。本轮不重启服务；API 所加载代码与当前 Git HEAD 的逐字等价性为 unknown，不作等价声明。
- B0 当前执行器 `backend/app/evaluation/run_baseline.py` SHA-256：`0e0aa5e24708d53ce0e1354fb48c6e0f3776e3462b294120e6a0709677da8530`。评分器 `score_batch.py`：`cb255c4f6cdbe211dbad04d4425be77e14383da2f9080da44b9db50f068efb07`；报告器 `report_batch.py`：`59415a08949e4cbab7b86c4f6b28d4fc907f90c95a5126268019934bb7f175e5`；批次运行工具 `batch_runs.py`：`4d1bba5c7d7c3b497c2914c6177a88bc121ca0f7d914572846c1210f49c22172`。
- 上一轮 100 运行于 HEAD `00b397443bd7258d2166c6445ac4ac066cefd21d`，使用旧 `run_baseline.py` SHA-256 `cdda0026e00531cff82cfb1fdd0559d067d1184610055d207fadf46cf7e52b29`。该旧 runner 只作为历史版本标识；此后窄幅 runner/harness 修复未重采样/重评分旧 66/30/4。本次 B0 使用当前 `0e0aa5e…` runner，不能把旧批次统计当作本 runner 下的实测结果。
- `source_revision`、`build_revision`、`prompt_revision` 将以本次 capture 中的实际运行时事件为准；冻结前未从运行时 capture 获得这些值，当前均记录为 unknown。不得由 HEAD、磁盘文件或历史批次推断 loaded-code equivalence。

## 模型、provider 与 Kev

- 主回答、Memory extraction、Dream 配置模型：Root 已确认均为 `deepseek-flash`，DeepSeek API host `api.deepseek.com`。API key 不读取、不保存、不展示。
- 真实 Kev：用户 GPU1 现有服务 `http://127.0.0.1:8009`，模型标签 `kev-latest`；按已确认规格使用 3 秒调用上限。此服务由用户维护，本轮不重启、不改配置。
- 主/提取/Dream 的非 secret 配置摘要 hash：当前可读材料未提供，记录 unknown；不读取 `.env`，不从模型名或 provider 推算。
- 01 安全结果报告 `work/local-followup/04/kev-followup-20261009/KEV-NAVIGATION-POLICY-RESULTS.md` SHA-256 `0693f9cc238a65870f021126d334343599a43975e3a2450efc89d8414672bb6d`。它记录的是已接受的 01 API/角色/政策/浏览器证据，不替代 02 基线，也不替代 01 TASK 最终本人验收。

## 输入、rubric 与计划矩阵

- 公开 40 输入版本 `ceres2-local-followup-dev-2026-10-08-v2`，SHA-256 `032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d`。
- 私有 20 输入版本 `ceres2-local-followup-independent-acceptance-2026-10-08-v1`，SHA-256 `99134c5c4394e9319fcaeeb73736366c62e07b428206733af48c29f25fd74476`。题面及标识仅由独立 Tester 保留；本报告、pilot/results 和公开导出均不得包含私有题面或标识。
- 组合包版本 `ceres2-local-followup-60-case-bundle-2026-10-08-v1`，SHA-256 `107bdb6d70d1731719c061a30c2a295b5d218d7732075fbdfcdd9b965c87b1d5`。100 行矩阵固定为公开 core 20 案各 3 次，另外 20 个公开案和私有 20 案各 1 次；合计公开 80 行、私有 20 行。rubric、用例、输入字节和该矩阵均不修改。
- 原离线矩阵文件 `batch-plan-100.json` SHA-256 `01f203014a7e3faaf6dee1672c1de0b4cbbfff54ed0d7c42363dc77499d1acd8` 仅作矩阵基准留存。B0 由上述原组合包与 `--core-repeats 3` 新建不同 raw batch；不覆盖旧离线计划、旧 66/30/4 batch/score/report 或前次真实模型 raw。

## 商品、政策与索引数据

- 本次可读的静态 fixture SHA-256：`products.json` `ce5c0856bf1e39b92ae52b6b81faa90ebf579221afb0908b5bf542a9205f2322`；`offers.json` `c2fabcefe264d3bf532a1a3a82e2d8eba1a1477bd11a66db59ce1528c84f7c9f`；`recipes.json` `1fd396fe8255961fd8c423817efe0d80a1a0ad8377b26e42104a76886c3ed45c`；`ingredients.json` `a9079a1c7ca8d3f94c4efdfa004ede7e48b5ea568f7cb8025804124ad82ca19d`；`policies.json` `7a370431a1a9c2df2b818218f3c54cb01946f93fa027aad44021dd1637f10502`；`knowledge-provenance.json` `973aaed308f0ae32ea56d25183ede9b783025062ccd6bebddf31a8c3c1d98089`。
- 01 已记录 hybrid index SHA-256 `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`、Graph manifest SHA-256 `3aad90d9d498e614ddd30799275881c5fc53b9f45c1dbba5fc62eb067cdb3787`，产品知识 index revision `fb981e66e2cd272a9a32a6da9db49512dd7a55142e3ccf59afbdc43ee1bb2c01`。这些是 01 安全报告中的已记录值；B0 如有可观察 source/index revision，以 capture/runtime event 实际值为准。B0 期间不构建、不改写、不重启索引。
- B0 的实际 embedding model/revision 和当前模型权重文件 hash，在本轮可读的 01 安全报告中未给出，记录 unknown；不从前次构建记录继承。
- 新 Ceres 隔离业务库、checkpoint 和 owner namespace 由 infra launcher 管理。01 owners 和其 Memory jobs 不属于 B0 统计；本轮使用全新 case/trial owners。Tester 不读取既有 DB、旧 owner/session/cart/order/checkpoint/index state。与 B0 case/run/owner 的可归因统计只从本次 raw batch 和经授权的 B0 过滤聚合导出，私有详情不外发。

## 执行和报告边界

- Root 明确 GO：先 pilot 20。pilot 不出现系统性服务/采集阻塞时，在同一 B0 raw batch 上 `--resume --max-executions 80`；失败、unknown、未执行保留原分母，不重跑、不改模型、不改题、不改 rubric。
- 本 B0 仅使用隔离 Ceres API 8017 与既有真实 Kev 8009；不访问或改动生产 GPU1 服务，不改变数据库/索引/Prompt/模型。旧 01 owners 与 2 个 Memory jobs 排除在 B0 统计之外。
- Guide 15 秒为本批 API/SSE 可观察指标。浏览器页面入口总耗时不从 SSE 耗时推断；本批若无相应真实浏览器测量，报告为 unknown/not measured。真实答案效用、自然度及人工标签在用户确认前均保持 pending。
- 未来公开人工标签包需在 B0 完成后单独生成，只含 8–12 个公开样本的真实输入、完整回答、catalog事实、期望、checks、错误及版本；public-only JSON 保留 owner/run/trial/step 与原 raw 的映射，human-readable 包可隐藏内部 ID。reviewer/reviewed_at 在用户确认前留空；三次 core trial 必须逐条绑定，不能把一次回答扩标到三次。私有 20 不进入导出、标注或实施者数据。
- raw batch 与含私有任务的 score/report 均保存在 ignored `work/local-followup/tmp/independent-acceptance/kev-20261009/`，不写入 Git。面向 Root/用户的安全文件位于 `work/local-followup/04/kev-followup-20261009/`。

## 本轮输出路径

- Raw: `work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-batch.json`
- Pilot score/report: `work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-pilot-score.json`、`02-baseline-pilot-report.json`
- Final score/report: `work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-score.json`、`02-baseline-report.json`
- Safe summaries: `work/local-followup/04/kev-followup-20261009/02-PILOT.md`、`02-RESULTS.md`

本文件只登记 B0 冻结边界，不包含任何 B0 模型调用结果。运行过程中不改变本文件；观测到的运行时 revision、退出码和文件 SHA 放入 pilot/results 报告。
