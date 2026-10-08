# Ceres1 评测参考与 Ceres2 适配

本文件说明方法来源和适配边界；执行状态在 [本轮 TASK](../tasks/ceres2-local-followup.md)，不继承任何历史成绩。

## 固定来源

参考仓库 [2061623884/ceres](https://github.com/2061623884/ceres)，分支 `codex/ceres-v4-evaluation`，用户指定并已只读核实的提交为 `72bb1b99bf040c8b0bae5d026888bc059bc9423d`。
该提交的评测脚本另固定产品候选 `ac895fd620af617fa31f4e0006841a4d6a89cd53`。评测脚本提交与其产品受测提交是两个版本，不能互换。

已读取的方法来源：

- [V4 规格](https://github.com/2061623884/ceres/blob/72bb1b99bf040c8b0bae5d026888bc059bc9423d/docs/plans/ceres-v4-evaluation-spec.md)、[评测集说明](https://github.com/2061623884/ceres/blob/72bb1b99bf040c8b0bae5d026888bc059bc9423d/evals/v4/README.md)、[总 TASK](https://github.com/2061623884/ceres/blob/72bb1b99bf040c8b0bae5d026888bc059bc9423d/tasks/ceres-v4-evaluation.md)。
- [任务执行与评分](https://github.com/2061623884/ceres/blob/72bb1b99bf040c8b0bae5d026888bc059bc9423d/scripts/eval_v4.py)，重点为 `check`、`invariants`、`plan_constraints`、`execution_result`、`batch_summary`。
- [评分器负例测试](https://github.com/2061623884/ceres/blob/72bb1b99bf040c8b0bae5d026888bc059bc9423d/scripts/test_eval_v4.py) 与 [检索指标测试](https://github.com/2061623884/ceres/blob/72bb1b99bf040c8b0bae5d026888bc059bc9423d/backend/tests/test_rag_eval_metrics.py)。

只读源码对象位于本机 `/tmp/ceres1-evaluation-72bb1b9.git`，用精确 SHA 读取；bare 仓库的 HEAD 未设置，不作为运行工程。Tester 单独提取公开回归内容和 schema；实施者不读取混合文件中的验收正文，也不导入其数据库、索引、cookie、配置或 runtime。

## 方法映射

| Ceres1 方法/发现 | Ceres2 采用方式 | 不能据此声称的结果 |
| --- | --- | --- |
| 40 回归 + 20 新验收，20 核心三次，共 100 次计划 | 重新设计适用当前 canonical 商品、政策和 API 的场景，核心 pilot 后冻结继续；Tester 维护新验收 | 100 次已运行，或新验收等于严格盲测/统计泛化 |
| 每个执行独立状态；准备不算 Agent 成功 | 每题/重复执行新 owner 和唯一 canonical Guide session，后续动作在同题会话；使用新运行库 | 能直接复用旧商品 ID、旧会话或旧接口 |
| 缺预算/金额不能默认为零；错误价格即使内部自洽也失败 | 公共商品 Offer、Guide plan、cart 的事实与预声明条件分别检查；缺证据记未知/不满足，保留原因 | 有 plan 或非空 cart 就任务正确 |
| 拒绝切换仍换角色、无授权写入、错订单和重复副作用是关键违规 | 比对动作前后公开状态与本题明确授权；正确等待/合规拒绝单列 | 模型没报警就没有违规 |
| 失败、准备失败、脚本失败、未执行均保留计划分母 | batch 明确 outcome；无 run 的 capture 为 null；逐题继续，离线重评分不增加产品运行次数 | 删除失败项后的“成功率” |
| 逐轮时延、核心三次稳定性、usage 覆盖分别报告 | 保持本工程实际 15 秒/5 轮合同；客户端 SSE 到达与服务事件时间分开；未知成本不猜测 | TestClient 缓冲时间等于用户看到消息的时间 |
| 人工/语义判断与确定性业务评分分离 | 既有 owner/run 限定 v2 人工标注；自然度需要人工，未审阅为 unknown；模型裁判只作诊断 | runtime completed 或裁判无报错等于自然度通过 |
| MRR 漏召回计零，recall 按 gold ID 比例；无答案与降级分开 | 当前公开检索集检查 real hybrid 模式、有效 canonical ID 和多目标召回；不把空返回一律判错 | 受控召回代表真实 BGE 质量 |
| 历史 embedding 失败后 lexical 运行需明确标识 | 本工程已有真实 BGE/RRF；保持生产合同，不借参考的 lexical 路径冒充 hybrid | Ceres1 lexical 成绩证明 Ceres2 hybrid 通过 |
| 保存 source/data/index/model/Prompt/scorer/cases 和未提交源码 | 本轮每批保留实际冻结/hash；源码提交、运行版本、导出时源码分别记录 | 只记录 Git HEAD 就覆盖了工作树与已加载 runtime |

## 改进任务如何产生

先验证评分器负例和公共执行链，再记录当前基线。只有可复现的错误、召回缺口、合同不满足或人工质量标签才触发产品改动；按错误所在模块明确唯一 owner，准备最小复现，再由 Tester 验证修复和同条件对照。

GraphRAG 真实构建/Local/Global、Memory/Dream、浏览器与本人接受分别留证，不混入 100 次 API 任务计数。实际 provider 配置未就绪时可完成公开集、执行器、离线评分和受控验证；真实模型效果继续保留未执行。
