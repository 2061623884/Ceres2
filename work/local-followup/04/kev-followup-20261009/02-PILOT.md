# 02 新环境基线 B0：20 行 pilot

日期：2026-10-09。本文记录原 100 行矩阵的首批 20 行；不替代最终 100 行结果。公开/私有用例正文、标识及逐行输出均不在本文件中。

## 固定版本和执行

- Git 冻结：HEAD `f9d7b44870e447c1f592a12163ad443b17782980`，tree `f6dd1554335b9da351a89ec825b3c6034d47c2e5`；冻结记录见 [`02-BASELINE-FREEZE.md`](./02-BASELINE-FREEZE.md)，pilot 后未改写。
- 实际执行环境及非 secret pins：[`02-ENVIRONMENT-PINS.md`](./02-ENVIRONMENT-PINS.md)，SHA-256 `4872aa8c4bac4b09f557e6fb00c64ac1bbd0e9f534585a6fb581a015302b555f` (corrected digest; metadata only).
- 本轮 8017 API 调用实际经过已存在的 Kev GPU1 HTTP 服务 `127.0.0.1:8009`。没有重启或更改 Kev 服务、配置或用户状态。该说明更正冻结文件中“本轮不访问 GPU1”的不准确措辞；冻结文件保持原样。
- 01 正式受控回归的精确结果为 **1 项测试通过，用时 3.41 秒**（pytest 总墙钟 4.64 秒），不是含义不明的 `1/3.41s`。01 测试没有调用真实 Kev；B0 本 pilot 按正式路径调用了现有 Kev。
- Guide 时限固定为 **15,000 ms**；20 条均以此阈值计量。“20 pilot”是样本数，不是时限。
- B0 在 01 已完成数据/index 准备后使用已启动的 8017 服务和 warm hybrid/Graph index；它不是与未来冷启动候选版本可直接比较的 cold-start 基线。
- Pilot 使用固定 60-case bundle 与原 core20×3 / public non-core20×1 / private20×1 计划，未改变输入、rubric 或矩阵。Pilot 运行、评分、报告命令均退出码 0。执行器、评分器、报告器 SHA-256 分别为 `0e0aa5e24708d53ce0e1354fb48c6e0f3776e3462b294120e6a0709677da8530`、`cb255c4f6cdbe211dbad04d4425be77e14383da2f9080da44b9db50f068efb07`、`59415a08949e4cbab7b86c4f6b28d4fc907f90c95a5126268019934bb7f175e5`。
- 精确执行命令（工作目录 `backend`）：

  ```text
  ../.venv/bin/python -m app.evaluation.run_baseline --api-base http://127.0.0.1:8017 --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --core-repeats 3 --max-executions 20 --output ../work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-batch.json
  ```

  评分与报告分别使用 `app.evaluation.score_batch`、`app.evaluation.report_batch`，读取同一 bundle 与上述 raw batch，输出 pilot score/report。完整参数、日志均保存在 ignored 的 `work/local-followup/tmp/independent-acceptance/kev-20261009/`。

## Pilot 观察

计数来源是 pilot JSON 的离线评分和报告。planned 100、attempted 20、not_run 80；本批 20 条均进入 `guide_run`，role wait、preparation failure、runner failure 均为 0。100 行计划分母上的业务 verdict 为 pass 14、fail 5、unknown 81；其中仅对已尝试 20 条，verdict 为 pass 14、fail 5、unknown 1。未运行行的 unknown 不应解读为已评测失败或通过。

20 个 Guide receipts 的终态为 completed 12、waiting_confirmation 6、failed 1、protected 1；其余终态 0。Guide receipt 终态是运行阶段观测，不与独立业务 verdict 混为一谈。critical findings 为 0，执行分母 20；这只表示本 pilot 未检出 rubric 中已定义的 critical finding，不构成安全通过结论。

15 秒时限字段：样本 20、通过 20、超时 0、unknown 0。首 final 有 19 个样本（p50 4,317.535 ms，p95 6,688.332 ms）；stream complete 有 20 个样本（p50 4,320.078 ms，p95 5,897.459 ms）。API/SSE pilot 未测浏览器页面入口耗时。首 useful result 无人工标注，也未由本批契约测量：observed 0、unknown 20；首 interim、tool progress 和首 final 均不能替代 useful-result 标注。

消息事件观察：20 个 run 中 9 个至少发布一条 `message.interim`，总计 12 条；这 9 个 run 均在可见终态事件之前收到首条 interim。可测首次 interim 延迟 9 个样本，p50 2,369.876 ms、p95 2,930.128 ms。全批事件还包括 accepted 20、progress 110、plan.ready 6、answer.delta 91、turn.completed 19、error 1。`progress` 是运行状态，不计为用户可见 assistant 多消息。此计数只报告事件是否/何时可观察，不代表自然度或有用性判断。

Pilot 的 provider call summary 覆盖 20/20 runs，call 数完整性为 true；provider records 被截断的 run 为 0。可观察到 83 个 DeepSeek Flash / `api.deepseek.com` provider 响应记录：primary Pi 68、interim audit 15、general audit 0。来自原始 provider SSE response usage 字段的 input、output、totalTokens、cacheRead 在 83/83 记录存在，分别合计 457,764、5,806、463,570、417,792；记录中没有 `cacheWrite`（0/83 非空），因此完整 usage/cost 不可计算，成本为 unknown。report 的 `observed_usage_complete_runs=0` 指完整 usage 口径（包含缺失字段），不否定上述可见字段的下界/部分合计。Memory usage/token 未从数据库读取，本 pilot 不报告其 token 数。

检索路由观察：capture 记录商品检索路由 20/20 次成功返回；食谱检索路由 0 次；政策 lookup 1/1 次成功；B0 captures 内 Graph 工具、查询、provider 或 embedding 调用均为 0。capture 未保留查询结果或 SKU 候选明细，因此不能据此声称召回到相关商品或匹配成功。导航状态 ready 20；entry judgment 为 no 19、uncertain 1。判断结果不用于推算 Kev 请求数或把导航状态视为业务质量结论。

运行时 capture 在 20/20 行可读到同一 `source_revision` `18b72b101e646bd06e36d8c748572fc33c5dab9dfc98db38c9b77f06f5266c54`、`build_revision` `d28a9cd82cd2e852d249ccc38a0fb52e13e1ac7ce95ccf3dd715ba67194a5d01`、`prompt_revision` `123f4be3aa6a70bc08a8430cbb6d24e6cf4e0d7d1d85ca1548d5c2c5f814cf31`。这些是 capture 内的运行时标签，不据此宣称等价于当前磁盘 Git HEAD 或服务加载代码。

## 证据与继续决定

- Raw pilot batch SHA-256：`ddba090f5b051f2d36884824e0f5fa4fa5d15dd129b602d4a11614e921920f59`
- Pilot score SHA-256：`588dc90732d961e5eaafc9d664a033fc4330a7b5e834ed1b3421711d42ed4d28`
- Pilot report SHA-256：`074fae8d39191f5b0fa372bdbbba5039bcbfd41641acf63556185c34d91fcc54`
- Pilot runner / scorer / reporter logs SHA-256：`eaef5a1a78090625f70c3fa579b0cf569782e75ae7c309bc72d6a40cf01495f1` / `caa74819610d751eed67f5637a2550c8ae0f57bc0d4d47557718712b5c2eacd2` / `3945c7c185e3d2bc93d8154067233d631df24851a2d17e6e9635d818f9fb7266`。
- Batch、score、report 和完整日志均仅保存在 ignored `work/local-followup/tmp/independent-acceptance/kev-20261009/`；上文只列聚合信息，不复制单条用例、答案或私有标识。
- Pilot 没有发现系统性执行器、服务或采集阻塞。依 Root 明确授权，下一步在同一 raw batch 上 `--resume --max-executions 80`，保留现有 pilot 和失败，不重跑、不变更输入或配置。最终结论以完整 100 行批次及其离线评分、报告为准。
