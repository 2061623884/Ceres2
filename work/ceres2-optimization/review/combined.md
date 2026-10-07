# 独立两轴源码审查

基线 `b118dbea3852026c6a04c790b1e27df67c3c9c18`；审查对象为本地提交前的冻结源码，两个审查者各自只读检查，以下保留原结论。测试与真实采样由专职 Tester 提供，见 [最终技术证据](../testing/final-technical-gates-current-prompt-v2-2026-10-07.md)。源码清单见 [snapshot](review-snapshot.json)。本人验收与独立自然性评分仍开放，状态只在 TASK 维护。

# Standards review

Fixed point: `b118dbea3852026c6a04c790b1e27df67c3c9c18`; `commit list=[]`. Reviewed the tracked diff and snapshot sources; excluded generated databases/indexes. This reviewer ran no tests, lint, typecheck, build, or install.

## Findings

No confirmed hard standards violation. Python remains business authority (ADR 0002); fixtures remain local, generated outputs untracked, and the optimization TASK owns status (`AGENTS.md`, `docs/agents/issue-tracker.md`).

**Possible Fowler smell — Duplicated Code:** `runtime/pi/src/worker.ts:147–176,280–301` has similar audit-Agent setup. Ordinary audit failure stops the request; interim audit failure withholds an optional message. This remains a non-actionable heuristic unless an abstraction preserves both contracts; not a standards breach.

## Incremental review

After-sales changes keep explicit package counts/photo scope and commit the application, receipt, and handoff together (`backend/app/mercury/aftersales.py:78–92,198–217`). Seed correction is limited to two provenance-listed chips SKUs and preserves existing Offers (`backend/app/services/seed_service.py:45–56`, `data/fixtures/knowledge-provenance.json:32–42`). Evaluation labels remain human-authored, and development regressions are distinguished from independent acceptance (`backend/app/evaluation/annotate_runs.py:10–35`, `evals/README.md:3–23`).

Event timing uses nullable additive storage and does not rewrite old payloads or cached results; API, exporter, and frontend contracts align (`backend/app/migrations/__init__.py:34–37`, `backend/app/services/guide_run_service.py:146–150`, `backend/app/evaluation/export_runs.py:26–39`, `frontend/src/lib/saleGuide.ts:581–591`). Human-ticket reads exclude later responsibility generations (`backend/app/human/service.py:37–54`), with lifecycle readback coverage (`backend/tests/test_integrated_lifecycle.py:195–212`).

The Pi main request uses native `tool_choice=auto` without JSON mode, supported by the documented same-version A/B evidence; official-host thinking remains disabled (`runtime/pi/src/worker.ts:210–218`, `docs/adr/0004-demo-knowledge-retrieval.md:13`). `finish_response` is a non-business tool gated on `guide_request`; its arguments retain existing answer-kind callers, end the loop, and remain subject to Python `_answer` reference checks (`runtime/pi/src/worker.ts:127–145,227–234,317`, `backend/app/services/pi_product_runtime.py:352–364`). Completion text is not published as interim.

`recipe_facts` validates refs against this run’s searched dishes and ingredient IDs against those dishes, presents fixture-backed base quantities/shared required ingredients, and reads candidate products through current Catalog/Offer (`backend/app/services/pi_product_runtime.py:414–447`, `backend/app/services/dish_service.py:36–39`, `docs/plans/ceres2-optimization-spec.md:114`). It does not propose or mutate a cart. `graph_retrieval` records actual query revision and manifest (`backend/app/services/pi_product_runtime.py:140–153`). The new completion/recipe guards are task-backed, not speculative parameters.

Latest delta: the interim-only prompt rejects positive recipe ingredient, quantity, serving, and shared-ingredient assertions as task facts; `GENERAL_CLAIM_PROMPT` is unchanged (`runtime/pi/src/general-claim.ts:2,4`; `worker.ts:153,282`). Tester reports final `current-prompt-v2` regression 441/441, 16 focused runtime/typecheck/build and thinking/native/controlled checks passed, and exact-prompt semantic smoke 13/13; the latter remains same-model and non-blind (`work/ceres2-optimization/testing/backend-full-regression-current-prompt-v2-2026-10-07.json:1–19`, `interim-claim-semantic-audit-v2-2026-10-07.json:1–20`, `tasks/ceres2-optimization.md:50`). Firefox v6 records one fully visible interim before terminal seq17 and no result-introduction call (`browser-interim-smoke-recipe-facts-visible-v6-2026-10-07.json:39–44,63–100,252–340`); TASK records visible final recipe facts (`tasks/ceres2-optimization.md:52`). It used manual-role fallback and frame-boundary pauses, so does not establish automatic routing or unassisted latency. Task remains 待验收 pending user acceptance, independent scoring, and human review (`tasks/ceres2-optimization.md:52–56`). No standards issue; I ran no tests.

# Spec 轴独立复核

对照基线 `b118dbea3852026c6a04c790b1e27df67c3c9c18` 只读检查当前快照；未运行测试或其他验证。

已授权目标仍是：一条用户请求运行一个 Pi 主循环，可选地在含真实工具调用的 assistant iteration 中生成普通过程文本；不要求每轮发言，不另开气泡生成请求；最终由 `finish_response` 结束该循环，Python 校验引用并呈现业务事实（规格 [11–15, 34–44]）。当前 worker 仅从完成的、带非终态工具调用的 assistant 消息读取文字；最终工具轮、空白和无法识别的旧 JSON 不成为 interim（`runtime/pi/src/worker.ts:248–275`）。可可提示使用中文，简短说明核对方向，不预报结果（`backend/app/prompts/experience.json:2–17`）。

**成本与审校：**文案由主循环原生生成；每条候选另调用同一配置模型的审校 `Agent`。无效、失败或不确定结果均扣留，未核验商家事实和执行承诺不能发布（`runtime/pi/src/worker.ts:276–305`; `runtime/pi/src/general-claim.ts:1–4`）。usage 单独记作 `interim_audit`，主循环等待审校后执行工具，并在结束前等待审校队列（`worker.ts:113–120, 313–318`）。这是额外审校调用与时延，不是额外生成气泡的调用；当前规格明确要求分项计量（`ceres2-optimization-spec.md:42–44`）。我未发现用户禁止额外审校/provider 调用的明确指令，也未将这一已授权成本视为偏离。

审校通过后 Python 在独立短事务中检查会话/任务版本与运行状态，再原子写 `GuideMessage` 和 `message.interim`；不会提交运行 Session 中的购物/记忆变更（`pi_product_turn_service.py:136–170`）。前端 live 与 reconnect 共用事件处理，按稳定 ID 去重并把 interim 插入运行占位消息前；重新连接不会把它显示在最终回复之后（`App.tsx:1284–1295, 1381–1388, 1432`）。事实查询结果不再触发通用结果介绍；现只对问题选项、商品卡、确认回执或新方案触发（`App.tsx:1439–1442`）。

`recipe_facts` 仅用本轮菜谱引用及其规范食材，呈现 fixture 基准量；商品信息按明确请求重读当前 Catalog/Offer，不提案、不加购（`pi_product_runtime.py:414–447`; `dish_service.py:36–39`）。未发现超出授权的业务范围或数据权限。TASK 当前为待验收；用户本人验收、人工标签复核及独立自然性盲评仍开放（`tasks/ceres2-optimization.md:1, 50–56`; `evals/ceres2-optimization-failure-regressions.json:1–4, 50–61`）。

## 最新增量

审校提示现在把任何肯定的菜谱食材、用量、份数或共用关系说法都视为任务事实，不能因其像日常常识或不带门店名而放行；查找方向仍可说，`GENERAL_CLAIM_PROMPT` 未改（`runtime/pi/src/general-claim.ts:1–4`）。与当前源码哈希一致的同模型提示 smoke v2 为 13/13 预期判断相符；早期 v1 的 8/9 及食材事实漏拦仍保留为旧版本证据。v2 仍是同模型 prompt-path smoke，不代表独立准确率或盲评（`interim-claim-semantic-audit-v2-2026-10-07.json:8–20, 302–426`）。

最终 `current-prompt-v2` 全量 backend 回归由 Tester 报告 441/441 通过，exit 0；源码快照哈希与 Tester 记录绑定，并包含修订后的 thinking/native transport 断言（`backend-full-regression-current-prompt-v2-2026-10-07.json:1–20`; `backend/tests/test_official_deepseek_thinking.py:260–301`）。同版语义 smoke 为 13/13，但仍是同模型开发提示检查，不是盲评（`interim-claim-semantic-audit-v2-2026-10-07.json:8–20, 426`）。Firefox recipe-facts v6 的 current prompt 哈希与现源一致；真实 interim SSE seq 3 在终态 seq 17 前出现，气泡 opacity 1、视口完整可见，fact-only 没有 result-introduction 调用（`browser-interim-smoke-recipe-facts-visible-v6-2026-10-07.json:8–20, 38–52, 71–103, 253–270`）。它使用手动 role fallback，并在 SSE 帧间等待 DOM 采样；这不验证自动路由或无干预浏览器时延。第五条 failure-intake 记录仍为 `human_review_status: pending`。我未运行 Tester 检查；TASK 已待验收，用户验收和独立自然性盲评未完成（`evals/ceres2-optimization-failure-regressions.json:1–4, 50–61`; `tasks/ceres2-optimization.md:50–56`）。
