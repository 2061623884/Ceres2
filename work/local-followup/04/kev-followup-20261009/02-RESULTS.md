# 02 新环境真实模型基线 B0：最终结果

日期：2026-10-09。此报告汇总原始 100 行矩阵的一次 pilot 加同批 resume。所有 100 行均保留；未重跑失败项。本文仅披露受保护输入的聚合结果，不包含 private case 正文、标识或逐行输出。B0 是在 01 已建立索引、已启动 API 后进行的 warm-service/warm-index 测量，不是冷启动基线。01 的结果见 [`KEV-NAVIGATION-POLICY-RESULTS.md`](./KEV-NAVIGATION-POLICY-RESULTS.md)。

## 冻结、执行和证据

- Git B0 freeze：HEAD `f9d7b44870e447c1f592a12163ad443b17782980`，tree `f6dd1554335b9da351a89ec825b3c6034d47c2e5`。详细输入、矩阵、runner/scorer SHA、服务边界见 [`02-BASELINE-FREEZE.md`](./02-BASELINE-FREEZE.md)；pilot 纠正及完整参数见 [`02-PILOT.md`](./02-PILOT.md)。
- 启动环境安全元数据：[02-ENVIRONMENT-PINS.md](./02-ENVIRONMENT-PINS.md)，更正后的 SHA-256 `4872aa8c4bac4b09f557e6fb00c64ac1bbd0e9f534585a6fb581a015302b555f`。API 使用 DeepSeek Flash `api.deepseek.com`；既有 GPU1 Kev 为 `kev-latest`，导航阶段配置 3 秒，Guide 时限 15 秒。01 授权 launcher 将批准的模型与 API 配置读入隔离 API 进程；02 Tester 没有重读原始 `.env`。密钥值未输出、写入报告或 Git，配置未被修改。
- 固定输入：公开 40 v2、private 20 v1 和组合 60 包的版本及 SHA 见 freeze。原矩阵为公开 core20×3、公开 non-core20×1、private20×1；合计 100。未更改 cases、rubric 或矩阵。
- 执行：pilot `--max-executions 20` 与同一 raw batch `--resume --max-executions 80` 均退出码 0；raw 最终含 100 行。随后离线 `score_batch` 与 `report_batch` 均退出码 0。无额外采样、模型调用、API 重启或评分规则调整。
- resume 命令（工作目录 `backend`）：

  ```text
  ../.venv/bin/python -m app.evaluation.run_baseline --api-base http://127.0.0.1:8017 --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --core-repeats 3 --max-executions 80 --resume --output ../work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-batch.json
  ```

  离线评分和报告命令为 `../.venv/bin/python -m app.evaluation.score_batch --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --batch ../work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-batch.json --output ../work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-score.json` 与 `../.venv/bin/python -m app.evaluation.report_batch --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --batch ../work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-batch.json --score ../work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-score.json --output ../work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-report.json`，两者均读取固定 bundle/raw，不产生模型请求。
- 真实 raw batch SHA-256 `b7cff339ffab94c8a77ef6ce9d0c340c375d9972e7b80d8a113b967dcadf3a91`；score SHA-256 `f13999f215cb0e82a90ad988e75d7971e38a1c50c6fd1a7b9d5bb8bffb164d92`；report SHA-256 `95c0864939ad121a1c6a81ea8ce572ee661d55552f03b6083b2f1e466e57aacf`。Raw、逐行 score/report、命令日志保存在 ignored `work/local-followup/tmp/independent-acceptance/kev-20261009/`，不纳入 Git。
- Resume runner / final score / final report logs SHA-256：`eaef5a1a78090625f70c3fa579b0cf569782e75ae7c309bc72d6a40cf01495f1` / `475a3f26a20510ffc6d26dc8b86dd64245aa90f6fa43704d45887aed4deaca5b` / `67d31b381fcc6ff2ff87d7f05bca8daabc06995a23b3b991d8c57c94392dbdd6`。
- 本次运行时 capture 中 97 个 Guide run 均报告相同 revision：source `18b72b101e646bd06e36d8c748572fc33c5dab9dfc98db38c9b77f06f5266c54`、build `d28a9cd82cd2e852d249ccc38a0fb52e13e1ac7ce95ccf3dd715ba67194a5d01`、prompt `123f4be3aa6a70bc08a8430cbb6d24e6cf4e0d7d1d85ca1548d5c2c5f814cf31`。scope 分别为 `disk_at_admission` 和 `worker_disk_at_start`；loaded-code equivalence 在 97/97 均为 unknown。它们是本批 capture 标签，不证明与 Git HEAD、另一运行进程或未来改动等价。
- B0 当前索引 pins：hybrid SHA-256 `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`，Graph manifest SHA-256 `3aad90d9d498e614ddd30799275881c5fc53b9f45c1dbba5fc62eb067cdb3787`，knowledge index revision `fb981e66e2cd272a9a32a6da9db49512dd7a55142e3ccf59afbdc43ee1bb2c01`。BGE `BAAI/bge-small-zh-v1.5` revision `7999e1d3359715c523056ef9478215996d62a620`、512 dimensions。B0 期间索引未重建。

## 行数、业务 verdict 与终态

| 统计项 | 结果 |
| --- | ---: |
| 计划 / 尝试 / 未运行 | 100 / 100 / 0 |
| Guide run / role wait | 97 / 3 |
| preparation failed / runner failed | 0 / 0 |
| 业务 verdict：pass / fail / unknown | 71 / 26 / 3 |
| Guide receipt 终态：completed | 66 |
| Guide receipt 终态：waiting_confirmation | 23 |
| Guide receipt 终态：failed | 5 |
| Guide receipt 终态：protected | 3 |
| critical findings / execution denominator | 0 / 100 |

Guide receipt 状态是运行阶段观测，业务 verdict 是题目 rubric 判分，两者不互相替代。100 行均已经尝试；unknown 不表示 pass 或 fail。0 critical finding 只表示本评分规则本次没有记录到定义的 critical finding，不构成安全或整体验收通过。

三个 role-wait 行在 raw batch 的 phase outcome 是 `role_choice_required`，没有 Guide capture；不以此推断商品、计划或答案质量。

按类别聚合：purchase planning 24 行，9 pass / 12 fail / 3 unknown；product selection 33 行，29 / 4 / 0；recipe facts 20 行，18 / 2 / 0；routing 9 行，4 / 5 / 0；policy 12 行，11 / 1 / 0；mixed purchase/policy 2 行，0 / 2 / 0。该表是全套输入的聚合统计，不含 private 样本明细。

20 个公开 core case 各运行 3 次，共 60 个 trial：业务 verdict pass 44 / fail 14 / unknown 2；60/60 满足 15 秒；11/20 个 case 的三个 trial 全部 business-pass，11/20 个 case 的三个 trial 全部 combined business+performance pass，20/20 个 case 的三个 trial 全部 performance-pass。三次稳定性由每个原始 trial 分别计算，未把一次输出扩标到其余 trial。

## 时延、interim 与人工效用

- Guide 预算是 **15,000 ms**。97 个 Guide run 均有可测值：97 pass、0 timeout、0 unknown；3 个 role-wait 没有 Guide 时延样本。core60 的 trial 级阈值结果为 60/60 pass。
- 首个 final：92 样本，p50 4,319.776 ms，p95 6,373.731 ms。SSE stream complete：97 样本，p50 4,327.954 ms，p95 6,375.443 ms。API/SSE 结果不能代替浏览器页面进入总耗时；B0 未测浏览器 entry latency。
- 首条 `message.interim`：34/97 Guide runs 有至少一条，事件共 41；34/34 首条 interim 在 `turn.completed` 或 `error` 等可观察终态前到达。首 interim latency 34 样本，p50 2,475.345 ms，p95 4,432.706 ms。`progress` 530 条为 runtime status，不算 assistant 多消息。
- `first_useful_result_ms` observed 0、unknown 97；此批契约没有 useful 标注。首 interim 或首 final 不推断为有用。原始B0的人工标签为0/97；后续dev-22唯一业务标签写入单独产物，不回写B0。答案自然度、对话节奏、首useful及用户满意度仍未人工验收，保持unknown/pending。

## 路由、检索与 agent/provider 调用可见性

- Capture 记录 `retrieval_start` / `retrieval_end` 各 103 次，end outcome 为 success 102、empty 1。检索结果/SKU 候选列表没有保存在 capture，因此只能报告路由返回，不声称召回或商品匹配正确。
- `policy_judgment` runtime events 97 次，结果字段 no 81、yes 13、uncertain 3；`policy_lookup` 19 次，`policy_reuses` 0。B0 没有单独保存可核实的 Kev HTTP 请求计数，不能把 judgment event 数直接标为 Kev 请求数。
- Graph tool attempts、queries、provider calls、embedding calls 均为 0。该 B0 数据没有测 Graph retrieval 的实际质量或延迟。
- Provider runtime events 中观察到 384 个 `provider_call_start` 与 384 个 `provider_call_end`：`primary_pi` 323、`interim_audit` 59、`general_audit` 2。97 个 Guide captures 中 provider-call summary 完整 95 个、不完整 2 个，且 per-run provider records truncation 均为 false。384 是本次记录到的 call events；summary 不完整的两行作为 coverage caveat 保留。
- 384 个已记录 provider-call usage 对象的 `input` / `output` / `totalTokens` / `cacheRead` 都有数值（各 384/384），合计分别 2,135,320 / 26,937 / 2,162,257 / 1,954,048。`cacheWrite` 384/384 为 null；report 的完整 observed-usage 覆盖是 0/97 runs；provider cost 为 null；完整 usage 与金额均 unknown。按 stage 的部分 observed usage：primary Pi 323 calls，input 2,122,637 / output 25,637 / total 2,148,274 / cacheRead 1,954,048；interim audit 59 calls，12,391 / 1,268 / 13,659 / 0；general audit 2 calls，292 / 32 / 324 / 0。
- Usage 的 source attribution 来自当前代码 `runtime/pi/src/provider-observation.ts` 对 provider SSE 中显式 usage 字段的读取，并由 `runtime/pi/src/worker.ts` 写为 `provider_call_end`。capture 没有逐记录 `usage_source` 标签；这里是源码路径归因，不是原始记录字段。没有用 SDK estimate 或默认 0 补缺失字段。source SHA-256 分别为 `b8eb1fa6a231e92efd5ef48568ab9feaf8f75448d38479cee0a323ca5ae0f7bf`、`6d3c8661fb6ff84087352c96bbed22032e636d7b283735551c87926fd80197d3`。
- Memory / Dream background jobs、其实际 provider calls 和 tokens 不在此 raw batch 中，且 Tester 未读取数据库，均记为 unknown；本报告不从每个 run 推算后台任务或 token。Momo 没有可供本 B0 量化的专属 capture 字段。

## 未完成与验收边界

这批真实模型评测已执行完毕，原始B0与[公开复核包](./02-PUBLIC-REVIEW-PACKET.md)均为标注前快照；其pending字段不撤销后续实际确认。[JSON映射包](./02-PUBLIC-REVIEW-PACKET.json)逐条绑定capture、owner、run、trial和step，两份包只含11个公开case的25次结果，private20未导出。Markdown SHA`bb702942aeb78b7757728c88564f561c054aa0f231b85bcabd6d814ec6f9c23e`、JSON SHA`7c78c63dd4ae64f49e37b22695080f869c9b7b9c8b89010b7f8afdf90a42859a`。

用户随后已确认dev-22业务pass，独立Tester仅导入该1个Guide run到新的标注batch，见[实际确认](02-HUMAN-CONFIRMATION-RECORD.md)及[标注回执](02-HUMAN-ANNOTATION-RECEIPT.md)，其余23个公开Guide run与1个无Guide路由判断仍待确认。原机器71/26/3及dev-22机器fail不改写，未重评分或运行failure_intake。自然度、首useful、是否该多条interim及完整页面本人接受未由这条业务标签验收。完整真实Guide浏览器旅程仍未完成；这不否定已有独立产品页→模拟订单浏览器smoke，但该smoke不包含Guide、Kev或模型。价格、库存、订单写入均属demo/simulated business evidence；本报告不宣称真实商业交易或履约。

全部 raw 与逐行评分产物留在 ignored 目录。公开摘要留在本文件；不要把 private 20 题面、case ID、答案或其逐行标签复制到 Git 或公开复核包。
