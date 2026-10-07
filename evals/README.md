# 当前优化的评测入口

`ceres2-optimization-retrieval-dev.json` 是 18 条固定开发查询。用 `work/ceres2-optimization/testing/retrieval_dev_eval.py` 和 `relevance_hits_smoke.py` 对同批候选比较 sparse、dense、RRF 与最终 hits。它参与过门槛调参，不能作为独立验收集。当前模型、语料、索引、Prompt 与未提交源码 hash 见相应报告。

`ceres2-optimization-failure-regressions.json` 登记本次真实暴露的错误、归因、期望与回归入口；它是开发回流记录，人工签核状态保持待复核，不能冒充盲评或独立产品评分。业务及 SSE 回归在 `backend/tests/` 与本任务 testing 目录，真实 GraphRAG 查询和浏览器证据各自保留层次。

导出只针对一个明确 owner，原始运行与标注文件都放 Git 忽略的 `data/generated/evals/`。人工逐个核对当前用户请求、权威事实与事件，为要标注的 run 写一行 JSONL：

```json
{"run_id":"实际导出的run_id","verdict":"fail","error_type":"retrieval","severity":"major","expected_behavior":"描述应取得的条款、商品或行为，并给依据","rationale":"描述观测与期望差异，引用该run的事件","reviewer":"实际审核者","reviewed_at":"2026-10-07T12:00:00+08:00"}
```

以下命令只附上明确提供的标注，不推断标签、修改数据库、训练模型或替换知识：

```bash
cd backend
../.venv/bin/python -m app.evaluation.export_runs --owner-id '<owner_id>' --output ../data/generated/evals/captured.jsonl
../.venv/bin/python -m app.evaluation.annotate_runs --captures ../data/generated/evals/captured.jsonl --annotations ../data/generated/evals/review.jsonl --output ../data/generated/evals/reviewed.jsonl
```

每个标注文件中 run_id 唯一，且必须属于提供的导出；不存在的 run 或非法字段明确失败。未标注运行保持 `labels: null`，未知 usage 不计为零。只有人工核准的失败，才由任务维护者去敏为稳定 case 并加入开发回归集：固定用户输入、期望身份/事实、错误归因、数据及执行版本，再指定现有回归入口。修复后对同版开发集复测，记录剩余失败；确认加购不自动成为正向质量标签。

Dots 独立维护产品评分协议、盲评和独立验收集；本地不假定其已完成。自然性、首个有意义消息、首个可操作结果、完成时延、调用/token 与严重错误按其明确分母交接。宿主事件写入时间和浏览器实际显示时间分别保留，Global 模型选出的关系与宿主原始事实投影分别评分。
