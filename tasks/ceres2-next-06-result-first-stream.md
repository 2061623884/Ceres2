# TASK 06：先显示结果再流式介绍

状态：待验收

阶段：最终修正候选受控验证通过；外部验收待完成

技术放行：已放行

最终恢复放行（2026-10-06 12:03 UTC）：独立Standards／Spec及fixture窄复核均闭合；同一不可变候选`0c752a2`完整backend426/426、37受控DOM/client、runtime/frontend build/strict checks及OS restart1/1通过。Tester比对238backend源／280build-UI源与integration无差异。受影响受控技术门槛恢复，真实provider／浏览器／语言品质／holdout／V3比较／本人验收仍开放。以下旧审查记录保留历史，不覆盖本段当前状态。详见[最终验证](../work/next-experience/10/final-controlled-verification.md)。

修复候选更新（2026-10-06 11:30 UTC）：统一修复`7067f3f`及跨货架追加`f272fd8`已无冲突合入`d2166e3`。两个独立review均在f272fd8关闭具体实现问题，但受影响技术门槛仍未放行，等待同一修正候选完整验证／等价。原问题报告、历史111／6／37与追加52项分别保留，不能混成final通过。

最终审查更新（2026-10-06 10:59 UTC）：Standards P2：表达／恢复异常路径丢失诊断原因；P3：未使用onAccepted hook；其余review启发式待报告细化。 原受控证据保留其适用版本，当前受影响门槛暂停，不能继承为修复后通过。统一修复工作树`next-review-fixes`、分支`ceres2/next-review-fixes`从冻结`e267fc9`开始，由主会话指定单一作者；本文件是唯一当前状态源。

历史放行范围：仅此前受控技术依赖，当前等待上述修复与复验。主会话于2026-10-06 10:39 UTC依据Tester最终字节一致性明确批准；不代表真实provider／浏览器／自然语言审阅／本人验收。

最近更新：2026-10-06 10:40 UTC。最终候选`79d4234fe75fa1bc2ef5034cb2a97eac67f4446e`（含`dc00f324`主体及usage修正）无冲突合入`53d4b41`。Tester确认237源／生成JS文件对应当前109个不重叠公开回归，273对应runtime build，frontend／harness与35个受控DOM/client场景完全相同。当前批次为usage 3＋review 4＋rest 102；早期107和其失败历史保留各自候选。三个review问题关闭，随后usage缺失→SDK零值问题亦有独立RED→GREEN；未知数值现在null，明确0保持0，provider原始prompt_total不扣cache。

最终证据：[usage3](../work/next-experience/10/runs/next06-usage-green/record.json)、[review4](../work/next-experience/10/runs/next06-usage-review/record.json)、[rest102](../work/next-experience/10/runs/next06-usage-regression/record.json)、[最终等价](../work/next-experience/10/next06-release-equality.json)、[完整35DOM/build路径](../work/next-experience/06/release.md)、[消费合同](../work/next-experience/06/contract.md)。

限制：主模型只解释不可变权威结果，事实由host渲染、连接语经过校验；不把原始未验证token当事实。30／15秒为发布保护，不是阻塞SQL的端到端SLA。真实时序／语言质量和节省未宣称。07可基于本受控合同进入下一票，不能承接未完成的06产品能力。

负责人：implement_next_result_stream。 状态由主会话维护；测试执行仅专职 Tester。

范围依据：[已批准规格](../docs/plans/ceres2-next-experience-spec.md)；[总 TASK](ceres2-next-experience.md)。

**交付：** 用户分类／筛选后先看到可用卡片，完成动作后先看到权威回执，随后边生成边收到简短自然介绍；表达失败不会丢失结果或重复执行。

**阻塞：** [05 四类请求按需上下文且语义不变](ceres2-next-05-context-equivalence.md)

**验收条件：**
- [ ] 权威结果先发布／显示并可操作，表达调用不延迟承认业务成功。
- [ ] 主模型仅解释这份结果，不重新理解、筛选、改变商品或执行写入；按钮仍零 Kev。
- [ ] 简短介绍在生成期间渐进到达，不以“整段生成完后切 24 字符”冒充新流式能力；事实校验与结果引用仍保留。
- [ ] 表达失败／超时／用户停止／断流不回滚、重提或重新筛选；卡片／回执保留，加载明确收口。
- [ ] 重连／重复请求复用事件和业务回执，历史展示不触发第二次业务效果。

**迁移／数据：** 复用持久 SSE、结果引用与业务回执；只补结果／解释分离所需最小合同。冻结成功、无匹配、业务成功但表达失败、断流恢复 fixture；不增商业状态机。

**必要证据：** 带时序原始 SSE／页面录制，证明卡片可用早于介绍完成且介绍为实际增量；故障注入检查购物车／订单／申请不变与加载收口；受控及真实模型事实审阅，单独计表达调用／token／时长。

## 下一步与证据

05受控前置已放行；从释放tip建立新worktree，读取05 module-contract与原Prompt冻结基线，先为结果可用早于真实增量解释准备公开RED，再最小实施。07仍等待本票技术放行。

执行证据目录：`work/next-experience/06/`。受控测试、真实模型、真实 UI、自然语言审阅与本人验收分别记账；当前全部未验证。完成实现只能记待验收，不能代替本人验收。
