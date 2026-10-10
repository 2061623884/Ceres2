# TASK 09：售后结果后回到购物

状态：待验收

阶段：受控技术完成；外部验收待完成

本地真实验收更新（2026-10-06）：真实浏览器已从选品、独立加购确认及独立模拟结算生成 6 袋 ¥35.40 的新订单。订单联系墨墨后，手动续接同角色请求与重复订单关联并行，出现 PUT order 409，前端清空订单显示；权威 case 仍绑定正确订单，资格查询自然完成，提案／申请／回执均为 0。当前 `MercuryChat.tsx` dirty 修复先完成会话初始化再消费 handoff，已选同订单不重复 PUT，消费 entry 不再次初始化；后端并发、责任及确认保护不改。修复后完整售后／返回购物、两轴复审及受影响验证尚待完成，不继承下方受控结果。原失败及只读状态证据：[本地真实验收](../work/next-experience/live-acceptance/README.md)。

后续真实续接（2026-10-07）：上述修复两轴静态复核无阻断。新请求在同一订单生成整单 ¥35.40 提案，Tester 独立点击确认提交；模拟申请为 `requested`，回执唯一，未审批／未到账；结果介绍失败保留业务回执。显式返回可可未重放旧步骤，cart 为 0、订单／结算回执／售后申请／售后回执各 1；新的饮水目标却触及 5 轮搜索上限，没有候选。已准备 Prompt 消歧待实际回归，整条购物往返旅程仍待通过。CTA 独立完整截图缺失如实记录，未来同版新旅程补证，不补造旧截图。

技术放行：已放行

放行范围：仅受控技术依赖。主会话条件批准；Tester于2026-10-06 09:35 UTC确认合入后最终production／runtime／frontend／09测试／DOM源一致。真实provider／浏览器／本人验收仍待验证。

最近更新：2026-10-06 09:35 UTC。候选`33458264465c3553e054dc6152a055f4d2d0d97a`无冲突合入`d74d82a`。最终当前04组合上6项新公开场景、runtime/frontend checks、response-loss recovery DOM和全App购物→售后→回购物旅程通过，合入后精确源一致。仅3个继承测试及新增helper不同，对应已7项GREEN的`f5b885f`显式role fixture。早期40项受影响回归保留原候选范围，不加总冒充最新全量。

最终证据：[6项公开](../work/next-experience/10/runs/next09-final-public/record.json)、[runtime](../work/next-experience/10/checks/next09-final-runtime/record.json)、[frontend及两DOM](../work/next-experience/10/checks/next09-final-ui/record.json)、[合入一致性](../work/next-experience/10/next09-integration-equality.json)、[先前40项](../work/next-experience/10/runs/next09-regression-final/record.json)、[实施与限制](../work/next-experience/09/implementation.md)。

保留警告：实际App受控旅程出现继承的ShelfScreen render期间更新ShoppingApp React warning；主会话定为非阻塞技术债、留最终review，日志不压制。通过断言不代表真实浏览器布局质量。人工责任／事务保护和原规则未削弱；申请提交不等于到账。

负责人：implement_next_shopping_return。当前状态由主会话／集成负责人维护，所有安装、build、typecheck与测试由Tester执行。

范围依据：[已批准规格](../docs/plans/ceres2-next-experience-spec.md)；[总 TASK](ceres2-next-experience.md)。

**交付：** 一条现有购物到新订单、售后申请再回购物的完整旅程；用户明确控制导航和每个写入，已完成步骤不重放。

前置放行：01／02／03中适用前置已受控技术放行（2026-10-06 09:16 UTC）；本票尚无实现／验证通过。

**阻塞：** [02 两角色无订单政策问答](ceres2-next-02-shared-policy.md)；[03 一次 Kev 与用户选择跳转](ceres2-next-03-role-navigation.md)

**验收条件：**
- [ ] 购买确认后独立模拟结算生成同一权威订单，售后角色实际查询此订单。
- [ ] 一般政策、具体资格、提案、确认提交分开；角色跳转／选订单不代替申请确认。
- [ ] 提交称申请已提交，不称退款到账／退货完成；同请求重放同一回执。
- [ ] 用户选择回购物，主要交接原请求，必要标识帮助定位，目的角色重查；明确返回不重复确认导航。
- [ ] 失败记录保留且暂停售后步骤，仍可选择购物；成功／失败都不能被后续购物覆盖或重提。
- [ ] 人工负责期间禁止 Agent 并发提交同事项，保留异步工单入口与责任保护。

**迁移／数据：** 复用 Checkout、订单、Mercury 和人工服务；通过现有模拟购买／结算形成 ORD-售后正常、资格外、故障、人工负责场景，不导入第二演示订单库。现有商品足够演示，无须等待新饮品或活动。

**必要证据：** 公开跨角色 API／SSE 全链和真实页面点选；查询订单／申请／购物车终态；重复提交、故障、人工责任竞态与目的角色重查。表达修改交公共 Prompt 负责人，不复制私有模板。

## 下一步与证据

全部前置已获受控技术放行；从释放集成tip创建独立工作树，先冻结适用业务基线并准备公开可观察RED，再按TDD实施。不得继承外部验收通过。

执行证据目录：`work/next-experience/09/`。受控测试、真实模型、真实 UI、自然语言审阅与本人验收分别记账；当前全部未验证。完成实现只能记待验收，不能代替本人验收。
