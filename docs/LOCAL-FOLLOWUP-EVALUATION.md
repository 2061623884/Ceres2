# 本机任务评测使用说明

范围和当前状态分别见 [规格](plans/ceres2-local-followup-spec.md) 与 [TASK](../tasks/ceres2-local-followup.md)。参考方法固定于 [Ceres1 72bb1b9](ceres1-evaluation-reference.md)。本文件是工具入口，不是实际模型成绩。

## 输入、采集与计划

公开集 [40条用例](../evals/ceres2-local-followup-dev.json) 和 [rubric](../evals/ceres2-local-followup-rubric.md) 使用当前 fixture/API 事实，20条核心三次加20条常规一次，共 **80次公开计划**。另20条新验收由Tester隔离维护，合并后才是100次计划。不能把40公开题说成100次，也不能把计划说成已运行。

每次执行使用独立合成owner，同题后续动作沿该owner/session。执行器只连接明确指定的评测服务，不启动服务器。公共API的业务价格、库存、订单、支付、退款和配送均为模拟。

真实采样前由Tester核对本工作树独立配置、固定源码/模型/Prompt/语料/索引与调用范围。保持原项目配置和活动状态独立；凭据不进Git。所有测试、构建、启动和模型验证命令由专职Tester执行。

下面命令从 `backend/` 执行，产物目录默认由Git忽略。首次核心pilot最多实际执行20次，其余计划记录not_run；该命令需要已准备好的评测API和获准模型配置。

```bash
../.venv/bin/python -m app.evaluation.run_baseline \
  --api-base http://127.0.0.1:8015 \
  --cases ../evals/ceres2-local-followup-dev.json \
  --core-repeats 3 --max-executions 20 \
  --output ../work/local-followup/tmp/baseline-public.json
```

确认pilot的输入和判分规则后，使用同一输入/计划/目标续跑：

```bash
../.venv/bin/python -m app.evaluation.run_baseline \
  --api-base http://127.0.0.1:8015 \
  --cases ../evals/ceres2-local-followup-dev.json \
  --core-repeats 3 --resume \
  --output ../work/local-followup/tmp/baseline-public.json
```

resume只执行not_run，已失败尝试保留；输入hash、计划或API目标变化会拒绝，不能覆盖旧轨迹。源码/配置改变后建立新批次；更正评分另留来源，不增加产品调用次数。

采集文件包含case_set hash、plan、每题outcome和实际capture-v2；无run为capture=null。逐题前后读取Guide/cart/orders/opening及当前Offer。支持预声明续问、计划确认和同body/key重复确认；未支持的setup/动作显式报错，不把首句执行当成完整旅程。

## 机器评分与人工标注

```bash
../.venv/bin/python -m app.evaluation.score_batch \
  --cases ../evals/ceres2-local-followup-dev.json \
  --batch ../work/local-followup/tmp/baseline-public.json \
  --output ../work/local-followup/tmp/baseline-score.json
```

机器结果仅说明预声明硬条件和公开事实。它检查当前Offer、金额与逐步授权；合法确认与重复副作用分开。缺失/null证据不当成零或满足，合法无方案由eq null声明。准备失败、脚本失败和未执行保留计划分母；完成状态不能替代质量。

汇总报告使用与评分完全相同的原batch字节；人工标注改变batch后须重新离线评分，不能把旧score配新batch。

```bash
../.venv/bin/python -m app.evaluation.report_batch \
  --cases ../evals/ceres2-local-followup-dev.json \
  --batch ../work/local-followup/tmp/baseline-public.json \
  --score ../work/local-followup/tmp/baseline-score.json \
  --output ../work/local-followup/tmp/baseline-report.json
```

报告分别列实际Guide终态、观察到的critical及观察分母、每轮15秒达标/超时/未知、核心三次业务/时延组合结果和usage覆盖。Guide completed不等于整案质量；首个有用结果未人工标注时保留unknown/null，不以首interim或首字节代替。

自然度、政策/菜谱语义及最终任务满意度使用人工v2 JSONL，沿用`owner_id/run_id/verdict/error_type/severity/expected_behavior/rationale/reviewer/reviewed_at`；verdict为pass/fail/needs_review。记录只绑定实际owner/run，未审阅保持null。

```bash
../.venv/bin/python -m app.evaluation.annotate_batch \
  --captures ../work/local-followup/tmp/baseline-public.json \
  --annotations ../work/local-followup/tmp/annotations.jsonl \
  --output ../work/local-followup/tmp/baseline-annotated.json
```

时间来源也需区分：客户端首个message.interim、首个answer.delta和stream完成从run POST开始计时；不含角色预检，不自动等于“首个有用结果”。多轮顶层计时指首轮run，steps分别记录各轮；服务端recorded_at另留。provider diagnostic tail不能冒充完整usage，未知成本不猜。

## 失败反馈与版本对照

只把明确审阅为fail、带期望和原因的样本纳入开发回归，保留原case/execution/run/版本来源；未标注和隔离验收不自动进入调参数据。修复前保留失败批次，按失败模块准备最小复现，再由Tester复验。

```bash
../.venv/bin/python -m app.evaluation.failure_intake \
  --cases ../evals/ceres2-local-followup-dev.json \
  --batch ../work/local-followup/tmp/baseline-annotated.json \
  --output ../work/local-followup/tmp/failure-regression.json
```

多轮标注覆盖captures中的每个真实run，末轮capture是同一run的alias；首轮错误不能被末轮pass掩盖。报告保留末轮字段的作用范围及全run标签，不将末轮pass签成整案自然度通过。

两侧用相同固定输入各自采集、审阅后，按case/execution对照：

```bash
../.venv/bin/python -m app.evaluation.compare_runs \
  --baseline ../work/local-followup/tmp/baseline-annotated.json \
  --candidate ../work/local-followup/tmp/candidate-annotated.json \
  --output ../work/local-followup/tmp/comparison.json
```

不同owner保留各自身份；输入不同必须明示，不能宣称同条件改善。未知质量仍未知，缺少pair明确列出，不删失败或未执行来提升成绩。

## 单独门槛

backend全量、官方GraphRAG受控组件、真实BGE公开检索、实际浏览器、真实主模型/图模型/Memory-Dream及本人接受分别留证。完整售后、初始化订单/记忆和更多业务动作driver未由本工具实现；已有受控生命周期测试单独报告。这些缺口不通过增加一句自然语言期望追认为已覆盖。

## 按本次授权复用amax配置

用户已明确允许只读使用原amax `.env`模型配置真实测评并发布交付分支。本次实际主/Memory模型为`deepseek-flash`；采用隔离进程注入，不拷贝原运行状态或整份配置，也不写密钥到Git。以下真实服务命令从本工作树根目录执行（Node22.19环境及本树独立依赖已准备）：

```sh
.venv/bin/python work/local-followup/04/real-model-20261008/provider_job.py serve
```

该有限测试入口只读取原`.env`获准字段，明确使用`data/runtime/real-model-20261008/`与当前新索引，监听8015；生产MemoryWorker保持启用。它不会填充新树blank.env。结束以SIGINT优雅停止。模型/API/Kev配置改变时建立新批次，不沿用本次resume；启动服务和真实采样仍由专职Tester执行。

本次已完成同一60包的20pilot+80resume，正式batch/score/report在独立Tester忽略目录，40公开与20隔离输入hash未变；[真实任务报告](../work/local-followup/04/real-model-20261008/REAL-TASK-EVALUATION.md)列命令与hash，[组件报告](../work/local-followup/04/real-model-20261008/REAL-COMPONENT-VERIFICATION.md)列新hybrid/Graph、真实提取/合成Dream和独立Firefox订单旅程。真实100结果66/30/4，核心三次11/20；当前图任务调用0、Kev缺配、人工自然度未知，不能把组件功能成功签成整体质量通过。

当前driver/harness源码为`cbca5d15bd40bd200f542d0eeaa1bc8192af9424`：缺plan确认诊断、Graph未知证据、进程配置隔离与必填签名已按审查修复，35项组合回归与最后5项harness验证按各自版本留证。实际100仍对应旧执行HEAD `00b397443bd7258d2166c6445ac4ac066cefd21d`，修复后未重新采样/评分。旧41项清单只用于实际执行溯源；当前受影响11项见[最终源码清单](../work/local-followup/04/real-model-20261008/REAL-HARNESS-FINAL-SOURCE-HASHES.sha256)，完整对应关系见[交接](LOCAL-CHANGES-HANDOFF.md#实测后的工具修复与验证)。
