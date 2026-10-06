# TASK 07：两角色自然表达受控优化

状态：待验收

阶段：受控指令交付完成；真实语言效果待验证

技术放行：已放行

放行范围：仅受控技术依赖。主会话条件批准，Tester确认候选1349186的238文件与2角色＋37公开测试精确一致；不等于自然语言改善或外部验收。

负责人：implement_next_natural_expression。 状态由主会话维护；测试执行仅专职 Tester。

最近更新：2026-10-06 10:55 UTC。候选`1349186b8a3b1aec39107a1a4f995aafaf33c32d`无冲突合入`6391507`，仅三个production expression字符串改变，冻结before／after／协议保留。2角色请求合同与同一37公开用例通过；scripted连接语不证明真实生成质量。静态intro Prompt Unicode codepoint由Keke 925→1656、Momo 935→1665，明确更长，不等同token，不宣称成本／时延改善。真实before/after模型采样、blind语言审阅、浏览器、holdout与本人验收未运行。

证据：[2角色](../work/next-experience/10/runs/next07-candidate-contract/record.json)、[37公开](../work/next-experience/10/runs/next07-candidate-public/record.json)、[精确等价](../work/next-experience/10/next07-release-equality.json)、[比较协议](../work/next-experience/07/comparison-protocol.md)、[长度](../work/next-experience/07/prompt-lengths.json)、[release](../work/next-experience/07/release.md)。restart probe在1349186通过1/1（5.10秒），仍需最终freeze重跑，不能泛化成所有重启情形。

范围依据：[已批准规格](../docs/plans/ceres2-next-experience-spec.md)；[总 TASK](ceres2-next-experience.md)。

**交付：** 导购和售后基于已正确的业务／流式合同，说得简短自然，先结果、后必要下一步，同时有可靠调用与性能对照。

**阻塞：** [06 先显示结果再流式介绍](ceres2-next-06-result-first-stream.md)

**验收条件：**
- [ ] 仅在已验证模块化与结果流基线上优化，冻结前后实际 Prompt、数据、模型和用例。
- [ ] 中文简洁自然、不过度重复；政策来源／条件、无结果、申请提交≠到账和失败状态完整。
- [ ] 不用更少调用牺牲复杂需求、记忆边界、授权或事实；优化真实收益及退化均报告。
- [ ] 调用、token 和各延迟分段可追溯；未知不记零，不把保护上限当 SLA，不提前宣称提升。
- [ ] 开发／回归与独立 holdout 隔离，不读取私有 holdout 调 Prompt。

**迁移／数据：** 只改现有模块的确有依据表达与上下文选择，不扩商品供给或更换模型来污染对照。固定两角色、四能力、无结果／失败／成功代表 fixture。

**必要证据：** 相同场景前后公开旅程／页面、原始模型对话与人工语言审阅；正确性零严重违规先行，再报告实际成本和分位／样本限制。公共 Prompt 由 05 唯一维护，09 等合入后最终票再冻结全版。

## 下一步与证据

06已获受控技术放行。先冻结现有06表达Prompt／源／数据／模型配置和固定场景，交Tester测baseline再准备RED；只在保持事实、授权和失败语义的前提下做本票优化。runtime／Prompt唯一维护权现由06交接07，App修改继续协调03，集成入口归integrator。

执行证据目录：`work/next-experience/07/`。受控测试、真实模型、真实 UI、自然语言审阅与本人验收分别记账；当前全部未验证。完成实现只能记待验收，不能代替本人验收。
