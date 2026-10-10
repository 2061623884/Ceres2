# 01 评测数据与批次分析

- 状态：待验收；六CLI/共享capture与40公开场景已冻结，本次真实100评分/报告已留证、cbca工具最终两轴完成，待用户审阅；人工反馈闭环仍开放。
- 负责人：followup_eval；主会话维护参考适配与状态，Tester 独占验证。
- 所属：[本轮总 TASK](ceres2-local-followup.md)；[规格](../docs/plans/ceres2-local-followup-spec.md)。
- 前置：无。只读参考 Ceres1 `72bb1b99bf040c8b0bae5d026888bc059bc9423d`。

## 范围与文件

公开开发/回归集、rubric，新 compare/annotate/failure 模块及对应公共 CLI 测试。
沿用 capture/manual labels v2，批次按 case/execution 配对，保留 owner/run 和版本；未知质量不能从运行完成推断。
不改现有导出/标注服务、数据库、共享 fixture、Pi、Prompt 或前端。不读取原或新隔离验收正文。

## 验收与证据

- [x] compare 公共 CLI 按 case 配对，跨 owner 的运行保持各自身份，未标注质量为 unknown；[RED](../work/local-followup/01/compare-batch-red.md)、[GREEN](../work/local-followup/01/compare-batch-green.md)，1/1，仅适用于证据中的源码 hash。
- [ ] 标注绑定精确 owner/run，不能标错对象；无运行状态不伪造运行标注。
- [ ] 显式失败 intake 生成有期望/原因/来源的开发回归项；未标注不自动归为通过或失败。
- [ ] 公开 40 场景有当前商品/政策/接口事实来源，机器判分、人工自然度与未知项明确分开。
- [ ] 计划分母包括失败、准备/脚本失败及未执行；未知金额/计时/usage 不填零。

初候选e855的18项评测CLI测试与另外7项runner/1项真实API受控smoke同命令26项通过，见[初候选证据](../work/local-followup/01/tool-combined-final.md)。审查补修后固定代码`739f13ead0c53ce9d82519efc30f51263e29ab45`，最终共同29项（21 eval、7 runner、1 app）通过，见[最终冻结](../work/local-followup/01/tool-combined-final-delta.md)；原26项和4e021的前次29项不覆盖补修后源码。公开v2 hash `032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d`；标注/失败split隔离、预算等待、缺行/空证据、batch-source绑定及全run标签都有实际正负例。100离线未执行项全部unknown，真实质量仍阻塞。上面清单最终关闭以审查/用户接受为准，不把工具通过改称真实采样通过。

后续真实执行另见[正式报告](../work/local-followup/04/real-model-20261008/REAL-TASK-EVALUATION.md)：100实际尝试，机器66通过/30失败/4未知。原离线100全部unknown只用于当时未执行计划；新实际批次不覆盖旧版。实测后的driver/harness诊断窄修见[交接](../docs/LOCAL-CHANGES-HANDOFF.md#实测后的工具修复与验证)，35项组合与最后5项按各自源码留证。

下一步：用户审阅；按[04](ceres2-local-followup-04-real-evaluation-feedback.md)完成明确人工标注、失败回归及版本比较，实际自然度/满意度未判分。
