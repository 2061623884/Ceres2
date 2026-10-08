# Ceres2 真实模型任务评测（2026-10-08）

本报告记录一次真实 DeepSeek Flash 模型、真实 Ceres2 API/SSE 路径下的 100 行任务批次。自动评分显示有实际通过项，也发现业务失败和一个 runner bookkeeping 故障；本批次不包含完整真实 Guide 浏览器旅程，也未完成用户本人 UI 验收。另有独立 Firefox 产品到模拟订单旅程，不包含 Guide 或模型调用。私有 20 题只给出聚合结果，不在本文披露题面、用例标识或逐题输出。

## 执行范围与命令

输入使用既有 60-case 组合包（40 个公开用例与 20 个独立验收用例），runner 对 20 个核心公开用例各执行 3 次，所以计划共 100 个执行行。先完成 20 行 pilot，确认 Guide receipt 可采集且服务/runner 无系统性阻塞后，在相同批次上 resume 剩余 80 行。没有重跑失败案例、改写用例、mock provider 或更换模型。

执行时服务由基础设施 Tester 在隔离工作树启动于 `http://127.0.0.1:8015`；本 Tester 只通过公开 API/SSE runner 运行，使用工作树自有 `.venv`，`HOME` 未变更，本 Tester 未读取 `.env`。pilot 和 resume 均退出码 0。下面命令均从 `backend/` 执行：

```sh
../.venv/bin/python -m app.evaluation.run_baseline --api-base http://127.0.0.1:8015 --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --core-repeats 3 --max-executions 20 --output ../work/local-followup/tmp/independent-acceptance/real-live-batch.json
../.venv/bin/python -m app.evaluation.run_baseline --api-base http://127.0.0.1:8015 --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --core-repeats 3 --max-executions 80 --resume --output ../work/local-followup/tmp/independent-acceptance/real-live-batch.json
../.venv/bin/python -m app.evaluation.score_batch --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --batch ../work/local-followup/tmp/independent-acceptance/real-live-batch.json --output ../work/local-followup/tmp/independent-acceptance/real-live-score.json
../.venv/bin/python -m app.evaluation.report_batch --cases ../work/local-followup/tmp/independent-acceptance/cases-60-bundle.json --batch ../work/local-followup/tmp/independent-acceptance/real-live-batch.json --score ../work/local-followup/tmp/independent-acceptance/real-live-score.json --output ../work/local-followup/tmp/independent-acceptance/real-live-report.json
```

以上正式 runner、score、report 命令均退出码 0。首次从 `backend/` 误用了 `.venv/bin/python`，退出码 127；该错误发生在 runner 启动前，没有发 HTTP、没有创建 attempt、也没有更改批次，之后改用工作树自有的 `../.venv/bin/python`。服务在批次结束后由基础设施 Tester 优雅停止，exit 0，8015 端口已空闲；独立数据库与 capture 仍保留在忽略目录。

## 冻结版本与数据

- 执行工作树 HEAD 为 `00b397443bd7258d2166c6445ac4ac066cefd21d`；本轮固定实现源码提交为 `739f13ead0c53ce9d82519efc30f51263e29ab45`。版本事件报告 `source_revision=94491a3fe4b85acbc2e47046210a90215ca76713b94d6b90a352574d2c19f974`、`build_revision=d28a9cd82cd2e852d249ccc38a0fb52e13e1ac7ce95ccf3dd715ba67194a5d01`、`prompt_revision=123f4be3aa6a70bc08a8430cbb6d24e6cf4e0d7d1d85ca1548d5c2c5f814cf31`。事件中的 `source_scope=disk_at_admission`、`build_scope=worker_disk_at_start`，但 `loaded_code_equivalence=unknown`；不能宣称这些运行时 revision 与 Git 树逐字等价。
- 输入组合包版本 `ceres2-local-followup-60-case-bundle-2026-10-08-v1`，SHA-256 `107bdb6d70d1731719c061a30c2a295b5d218d7732075fbdfcdd9b965c87b1d5`。独立验收 20 题版本 SHA-256 为 `99134c5c4394e9319fcaeeb73736366c62e07b428206733af48c29f25fd74476`，只作为输入 provenance；本文不复述其题面或条目标识。原离线计划 `batch-plan-100.json` SHA-256 `01f203014a7e3faaf6dee1672c1de0b4cbbfff54ed0d7c42363dc77499d1acd8` 完整保留，真实运行写入新的 ignored batch。
- 固定评测模块：`run_baseline.py` SHA-256 `cdda0026e00531cff82cfb1fdd0559d067d1184610055d207fadf46cf7e52b29`；`score_batch.py` `cb255c4f6cdbe211dbad04d4425be77e14383da2f9080da44b9db50f068efb07`；`report_batch.py` `59415a08949e4cbab7b86c4f6b28d4fc907f90c95a5126268019934bb7f175e5`；`batch_runs.py` `4d1bba5c7d7c3b497c2914c6177a88bc121ca0f7d914572846c1210f49c22172`。
- 实际模型为 `deepseek-flash`，API host `api.deepseek.com`。非 secret 配置摘要 SHA-256 `f1bd1b5983a0a07206a4bb1f549130b4a8b8b49afcb7b0bef845634503f2cbec`；密钥没有写进本文、capture 摘要或 Git。隔离 demo 数据库初始 seed 为 73 个商品、73 个 Offer，Memory 表开始为空；价格、库存与订单仍是模拟数据。
- 本地商品/知识 fixture 哈希：`products.json` `ce5c0856bf1e39b92ae52b6b81faa90ebf579221afb0908b5bf542a9205f2322`；`offers.json` `c2fabcefe264d3bf532a1a3a82e2d8eba1a1477bd11a66db59ce1528c84f7c9f`；`recipes.json` `1fd396fe8255961fd8c423817efe0d80a1a0ad8377b26e42104a76886c3ed45c`；`ingredients.json` `a9079a1c7ca8d3f94c4efdfa004ede7e48b5ea568f7cb8025804124ad82ca19d`；`policies.json` `7a370431a1a9c2df2b818218f3c54cb01946f93fa027aad44021dd1637f10502`；`knowledge-provenance.json` `973aaed308f0ae32ea56d25183ede9b783025062ccd6bebddf31a8c3c1d98089`。
- Hybrid 索引 SHA-256 `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`；Graph manifest SHA-256 `3aad90d9d498e614ddd30799275881c5fc53b9f45c1dbba5fc62eb067cdb3787`。本地 embedding 为 `BAAI/bge-small-zh-v1.5`，revision `7999e1d3359715c523056ef9478215996d62a620`、512 维；snapshot tree SHA-256 `70ab3a152b39753ca0815774a822d5ca35d7716aafa40b6d0b8e23e6598fed71`，主权重 SHA-256 `354763b9b1357bc9c44f62c6be2276321081ed2567773608c0d0785b61d5a026`。

GraphRAG 3.2.0 正式构建成功：44 entities、61 relationships、26 text units、11 communities、10 reports；11/11 provider completions 成功，耗时 86.3 秒、provider usage 48,420 tokens；另有 9 次本地 BGE embedding、tokenizer 计数 9,847（非付费 LLM tokens）。独立 local/global query smoke 分别耗时 18.0 秒和 18.7 秒，组件 deadline 为 180 秒；这两项不是 15 秒 Guide 预算验证。实时 100 行批次记录 Graph query/tool/provider/embedding 调用均为 0，因此构建和独立 smoke 成功不等于 GraphRAG 已在本批真实任务中承担检索。

## 任务结果

实际批次 100 行均 attempted，0 not-run，0 preparation-failed。score 阶段结果为 `guide_run=99`、`runner_failed=1`；这不表示只有 99 个 Guide capture：100 行都保留了 Guide receipt/capture，receipt terminal status 为 completed 66、waiting_confirmation 24、failed 9、protected 1。业务 verdict 汇总为 pass 66、fail 30、unknown 4。

其中公开执行 80 行的 business verdict 为 pass 55、fail 22、unknown 3（79 行 phase outcome 为 guide_run，1 行 runner_failed）；私有验收 20 行聚合 verdict 为 pass 11、fail 8、unknown 1，逐题内容和标识不披露。类别汇总如下：

| 类别 | 执行数 | Pass | Fail | Unknown |
|---|---:|---:|---:|---:|
| 购买规划 | 24 | 10 | 10 | 4 |
| 商品选择 | 33 | 27 | 6 | 0 |
| 菜谱事实 | 20 | 18 | 2 | 0 |
| 角色路由 | 9 | 0 | 9 | 0 |
| 政策 | 12 | 11 | 1 | 0 |
| 购买与政策混合 | 2 | 0 | 2 | 0 |

核心集 20 个案例各执行 3 次，共 60 行；business verdict 汇总 pass 44、fail 13、unknown 3，严格三次均业务通过为 11/20。评分器记录 46 个 major `hard_check_failed` findings（重复 trial 保留为独立执行行）；critical findings 为 0，critical 计算分母为 99。`check_evidence_missing` 有 33 条、`budget_quote_pending_decision` 有 1 条。零 critical finding 只表示评分器在 99 个 eligible 行里没有生成该类 finding，不能解读为全批安全通过。

9 个 Guide terminal `failed` 的错误码聚合为：`PI_ANSWER_INVALID` 4、`PI_GENERAL_CHANNEL_FORBIDDEN` 2、`PI_UNKNOWN_REFERENCE` 2、`PI_UNGROUNDED_BUSINESS_TEXT` 1。自动评分不等于人工评价；100 行均未人工 review。

一个公开执行行 `dev-01:trial:3` 被 runner 记录为 `runner_failed`。首轮 Guide receipt 和 before/after/capture 均已采集；after 状态是 `guide.plan=null`、task 仍 active。该行声明后续 `confirm_plan` 步骤，但没有 plan 时该动作没有可执行输入；runner 在构造确认请求时解引用 `plan['plan_id']`，触发 `TypeError: 'NoneType' object is not subscriptable`，没有发送 confirm HTTP。它是模型未生成所需 plan 后，runner 未将依赖步骤标记为不可执行而报错；不是 SSE/receipt 解析错误。原行保留为 runner_failed，其业务 verdict 为 unknown，没有重跑或伪装为后续步骤成功。

本轮可公开复核的业务失败例子（均来自公开回归子集，商品与价格是 demo fixture）：

- `dev-08` 要求先确认两罐商品的规格/口味；回复列出多个 330ml、500ml、不同口味和多包装选项后结束，没有保留澄清问题。
- `dev-16` 的确切蒙牛低脂 250ml 纸盒商品存在于 catalog，模拟报价 ¥4.00；检索工具三次返回成功，但助手称没有匹配商品且没有 plan，构成检索结果未落到回答的 false negative。
- `dev-17` 的两盒伊利全脂 250ml 商品模拟总价 ¥7.00，低于 ¥8 限额；执行多次商品搜索后进入 `protected`，未给购买 plan。
- `dev-05` 的精确 Pepsi 原味 330ml 罐装 SKU 存在于静态 fixture，模拟价 ¥3.00；重复执行中回复称无匹配商品。
- `dev-22` 对一个 550ml 水商品的规格是否可接受需要澄清，但回复称无匹配商品，没有提出规格问题。
- 公开订单角色用例均没有实际 Kev 判断；助手提及点击角色入口不能计为已经完成角色切换。
- `dev-34` 需要商品 plan 并说明替代商品应先征求同意，实际只返回政策说明，没有 plan。

## 延迟、多消息事件与人工质量边界

Guide 15 秒阈值有 100 个样本，100 pass、0 timeout、0 unknown。first-final latency 为 91 个样本，p50 4,096.534ms、p95 5,939.098ms；stream-complete 为 100 样本，p50 4,089.587ms、p95 5,899.782ms。失败的 9 个 terminal run 没有 final-answer latency。

真实 SSE capture 中，39/100 个 run 发出了至少一个 `message.interim`，总计 43 个 interim 事件；61/100 没有 interim。33 个 run 的 interim 在 `turn.completed` 前发出，另外 6 个在 `error` terminal 前发出；39 个都早于各自 stream closure。首次 interim 的报告 timing 有 39 个样本，p50 2,059.054ms、p95 3,356.061ms。这里统计的是 `message.interim` 消息事件，不把 `progress` 当作对话消息；它证明一个 user turn 可以发布多条模型消息，但不能说明这些消息自然或有用。

first useful result 有 100 个候选样本，人工有效性标签 observed=0、unknown=100，`human_annotated=false`。人工 review 0/100。自然度、主动性是否合宜、first useful time 均未验收。首个 interim/final 字节、progress 事件和模型自动评分都不替代人工有用性标注。

## Provider usage 与后台 Memory

100 个 capture 汇总出 409 条 `provider_call_end` 记录：`primary_pi` 340、`interim_audit` 68、`general_audit` 1。409 条记录的 `usage.input`、`usage.output`、`usage.totalTokens`、`usage.cacheRead` 均为非空数值；观察和分别为 2,200,915、28,452、2,229,367、2,030,720。`usage.cacheWrite` 在 409 条记录中均为 null；每条 `cost` 也为 null。cacheRead 是 input 的子集，不能再与 input 相加。以上为捕获到的 provider usage 字段汇总，不是费用估算。

来源归因有一个重要边界：这 409 条事件自身没有 `usage_source` 字段。实际 runtime 路径由 [`provider-observation.ts`](../../../../runtime/pi/src/provider-observation.ts)（SHA-256 `b8eb1fa6a231e92efd5ef48568ab9feaf8f75448d38479cee0a323ca5ae0f7bf`）直接解析 provider SSE `data[].usage` 的 `prompt_tokens`、`completion_tokens`、cached token 与 `total_tokens`，并只把实际数字写入 usage；[`worker.ts`](../../../../runtime/pi/src/worker.ts)（`6d3c8661fb6ff84087352c96bbed22032e636d7b283735551c87926fd80197d3`）将数值附到 `provider_call_end`；[`pi_product_runtime.py`](../../../../backend/app/services/pi_product_runtime.py)（`e2bb4936085cbcc0621953409c09b96b2ddd5080ab9449549a72afe1c97749a2`）再累计该事件。因此这些非空字段按实现来源归为 provider SSE observation，不是 SDK estimates 或默认 0；源归因来自固定源码路径，不是 capture 中显式的 per-record `usage_source` 标签。

run 级 `provider_calls_complete` 是 96/100 true、4/100 false；100/100 的 `provider_records_truncated=false`。这两个字段含义不同：记录未因 64-record tail 上限而截断，不保证 4 个 run 的 provider call summary 完整。即使在 call summary 完整的 run 中，cacheWrite 也没有可用 provider 值，因此 100/100 的 full usage field completeness 都是 false。409 条已记录数值是实际可观察总量的下界，不能当成 100 个 run 的完整 token 总量。report JSON 因覆盖不完整而保持 `observed_usage=null`、`observed_usage_complete=false` 是正确的；本报告只另列已观察部分。无 cost 数值，不推算费用。单独的 provider preflight 为 11 tokens、约 0.7 秒；不属于 100 行任务，也不计入上述 409 条。

正式 GraphRAG build 的 48,420 provider tokens 与 9 次本地 BGE embedding 已在上节单列，不计入 Guide task usage。生产 MemoryWorker 对 90 个 extraction jobs 全部记录 `completed`，失败/待处理为 0；Memory provider token usage 未持久化，实际调用量与 tokens 均 unknown，不能按 job 数推算。没有满足 Dream 阈值的 owner，Dream job/call 为 0。

## 检索、角色路由和未完成项

Hybrid 索引构建完成且版本固定。runtime summary 中 81 次 product retrieval 均显示 tool call 成功，16 次 policy lookup；这些是执行与工具状态，不代表 81 次商品召回都相关或回答正确。菜谱 retrieval 为 0。100 个 Guide run 的 Graph 调用/查询/provider call/embedding 均为 0，因此这批没有测到 Graph 对任务答案的实际贡献。

`KEV_BASE_URL` 缺失，100 个 navigation entry judgment 均为 `error/not_configured`，没有真实 Kev role judgment。9 条 routing 用例业务 verdict 全 fail；它们不代表 KEV 本身已完成评测，也不能以显示角色按钮替代真实路由。

后续仍需在配置 Kev 后重新运行角色判断用例；修复公开集暴露的精确商品 false negative、澄清行为、预算/plan 与产品政策混合流程；增加对 GraphRAG 真实 Guide 调用与 15 秒预算的任务验证；完成完整真实 Guide 浏览器旅程和本人 UI 验收，并补充人工自然度、有用性标签。独立 Firefox 产品到模拟订单旅程已完成，但不覆盖 Guide 或模型行为。当前库存与价格仍为模拟数据；模拟订单已真实写入本树隔离 SQLite，但不代表真实商业交易或履约。

## 证据文件

忽略目录保留原始 live batch 与 JSON score/report：

- `work/local-followup/tmp/independent-acceptance/real-live-batch.json` — SHA-256 `db0b98e3adce9879644bf7fabeea90b6ab928885424ce5b917a3204e77d87918`
- `work/local-followup/tmp/independent-acceptance/real-live-score.json` — SHA-256 `3c3b74f1d3ed189b12875897ff7a61926eb21689ddca9625f6838aa740cb96f7`
- `work/local-followup/tmp/independent-acceptance/real-live-report.json` — SHA-256 `dde87227d4f38085c07dc78448c696252c559e26ae3c05b835e4efb94a10cb5a`
- `work/local-followup/tmp/independent-acceptance/real-live-pilot-score.json` — SHA-256 `525ccbc89dcb8f1cb3d771a1a9d981984520472ffc06f235e60714d31287e6aa`
- `work/local-followup/tmp/independent-acceptance/real-live-pilot-report.json` — SHA-256 `81b319a4445d867df03b5e33e8ffffe76bc3236d2066eb6f1bd7dd0f757c6963`

JSON schema 仍为 `ceres-local-followup-score-v1` / `ceres-local-followup-report-v1`；`real-live` 是本次文件标签，不代表新的 schema 版本。原始题目和对话 capture 只保存在被忽略目录；本文仅列公开回归示例，未引用私有题目正文或标识。
