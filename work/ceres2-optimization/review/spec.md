# Spec 轴独立复核

对照基线 `b118dbea3852026c6a04c790b1e27df67c3c9c18` 只读检查当前快照；未运行测试或其他验证。

已授权目标仍是：一条用户请求运行一个 Pi 主循环，可选地在含真实工具调用的 assistant iteration 中生成普通过程文本；不要求每轮发言，不另开气泡生成请求；最终由 `finish_response` 结束该循环，Python 校验引用并呈现业务事实（规格 [11–15, 34–44]）。当前 worker 仅从完成的、带非终态工具调用的 assistant 消息读取文字；最终工具轮、空白和无法识别的旧 JSON 不成为 interim（`runtime/pi/src/worker.ts:248–275`）。可可提示使用中文，简短说明核对方向，不预报结果（`backend/app/prompts/experience.json:2–17`）。

**成本与审校：**文案由主循环原生生成；每条候选另调用同一配置模型的审校 `Agent`。无效、失败或不确定结果均扣留，未核验商家事实和执行承诺不能发布（`runtime/pi/src/worker.ts:276–305`; `runtime/pi/src/general-claim.ts:1–4`）。usage 单独记作 `interim_audit`，主循环等待审校后执行工具，并在结束前等待审校队列（`worker.ts:113–120, 313–318`）。这是额外审校调用与时延，不是额外生成气泡的调用；当前规格明确要求分项计量（`ceres2-optimization-spec.md:42–44`）。我未发现用户禁止额外审校/provider 调用的明确指令，也未将这一已授权成本视为偏离。

审校通过后 Python 在独立短事务中检查会话/任务版本与运行状态，再原子写 `GuideMessage` 和 `message.interim`；不会提交运行 Session 中的购物/记忆变更（`pi_product_turn_service.py:136–170`）。前端 live 与 reconnect 共用事件处理，按稳定 ID 去重并把 interim 插入运行占位消息前；重新连接不会把它显示在最终回复之后（`App.tsx:1284–1295, 1381–1388, 1432`）。事实查询结果不再触发通用结果介绍；现只对问题选项、商品卡、确认回执或新方案触发（`App.tsx:1439–1442`）。

`recipe_facts` 仅用本轮菜谱引用及其规范食材，呈现 fixture 基准量；商品信息按明确请求重读当前 Catalog/Offer，不提案、不加购（`pi_product_runtime.py:414–447`; `dish_service.py:36–39`）。未发现超出授权的业务范围或数据权限。TASK 当前为待验收；用户本人验收、人工标签复核及独立自然性盲评仍开放（`tasks/ceres2-optimization.md:1, 50–56`; `evals/ceres2-optimization-failure-regressions.json:1–4, 50–61`）。

## 最新增量

审校提示现在把任何肯定的菜谱食材、用量、份数或共用关系说法都视为任务事实，不能因其像日常常识或不带门店名而放行；查找方向仍可说，`GENERAL_CLAIM_PROMPT` 未改（`runtime/pi/src/general-claim.ts:1–4`）。与当前源码哈希一致的同模型提示 smoke v2 为 13/13 预期判断相符；早期 v1 的 8/9 及食材事实漏拦仍保留为旧版本证据。v2 仍是同模型 prompt-path smoke，不代表独立准确率或盲评（`interim-claim-semantic-audit-v2-2026-10-07.json:8–20, 302–426`）。

最终 `current-prompt-v2` 全量 backend 回归由 Tester 报告 441/441 通过，exit 0；源码快照哈希与 Tester 记录绑定，并包含修订后的 thinking/native transport 断言（`backend-full-regression-current-prompt-v2-2026-10-07.json:1–20`; `backend/tests/test_official_deepseek_thinking.py:260–301`）。同版语义 smoke 为 13/13，但仍是同模型开发提示检查，不是盲评（`interim-claim-semantic-audit-v2-2026-10-07.json:8–20, 426`）。Firefox recipe-facts v6 的 current prompt 哈希与现源一致；真实 interim SSE seq 3 在终态 seq 17 前出现，气泡 opacity 1、视口完整可见，fact-only 没有 result-introduction 调用（`browser-interim-smoke-recipe-facts-visible-v6-2026-10-07.json:8–20, 38–52, 71–103, 253–270`）。它使用手动 role fallback，并在 SSE 帧间等待 DOM 采样；这不验证自动路由或无干预浏览器时延。第五条 failure-intake 记录仍为 `human_review_status: pending`。我未运行 Tester 检查；TASK 已待验收，用户验收和独立自然性盲评未完成（`evals/ceres2-optimization-failure-regressions.json:1–4, 50–61`; `tasks/ceres2-optimization.md:50–56`）。
