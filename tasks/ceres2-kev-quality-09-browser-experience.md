# 09 多消息与完整用户页面旅程

- 状态：待开始。
- 负责人：体验/前端唯一实施者，专职Tester实际浏览器验证，用户本人接受。
- 所属：[04总TASK](ceres2-local-followup-04-real-evaluation-feedback.md)；[规格](../docs/plans/ceres2-kev-quality-followup-spec.md)。
- 阻塞：[05图决策](ceres2-kev-quality-05-pi-graph-evaluation.md)、[06售后](ceres2-kev-quality-06-aftersales-lifecycle.md)、[08Memory/Dream](ceres2-kev-quality-08-extraction-dream.md)技术门槛。

## 交付

用户在当前构建版页面连贯完成Guide交流、选择商品/数量、确认加购和模拟订单/售后衔接；复杂任务的过程消息有用、连贯而不重复，保持统一Grok bot风格。

## 验收

- [ ] 冻结上述候选，用真实浏览器和真实API/模型执行完整旅程，UI动作不由DOM/直接业务API调用替代。
- [ ] 商品详情、数量/方案修改、确认/幂等、模拟结算/订单与必要售后衔接可用；停止/重连等既有合同有实际证据。
- [ ] interim与runtime进度/最终答案分开，简单问题可直接完成，不机械拆final或加固定消息数。
- [ ] 按实际消息审阅及时/必要/连贯/重复/套话及结果一致性，有用性不以首字节代替。
- [ ] 确实问题才改UI/Prompt，适用公共行为回归/类型/构建与浏览器复验；用户本人风格/自然度接受独立记录。

## 证据与下一步

技术页面门槛通过后冻结候选并释放10；本人未确认时本票仍待验收，不影响先完成最终技术报告，但整体不能已验收。
