# TASK 08：既有首页活动成品选购

状态：待验收

阶段：受控技术完成；外部验收待完成

技术放行：已放行

放行范围：仅受控技术依赖。主会话条件批准，Tester2026-10-06 09:45 UTC确认合入后228API／265runtime-UI-harness文件精确相同。真实provider／浏览器／本人验收待验证。

最近更新：2026-10-06 09:45 UTC。候选`2fa6ebd7ecb75eb9a0b9e958ea5171d18ef59b9e`无冲突合入`a0bb165`；最终82项公开场景、runtime/frontend build/typecheck、4个实际App受控DOM与合入后源码完全一致。保留04饮品条款、05模块、09结果行为，静态catalog与Offer均70项。08受控技术放行；不将最终82项当全量或真实模型／浏览器／本人验收。

最终证据：[82公开](../work/next-experience/10/runs/next08-composed05-public/record.json)、[runtime](../work/next-experience/10/checks/next08-composed05-runtime/record.json)、[frontend＋4DOM](../work/next-experience/10/checks/next08-composed05-ui/record.json)、[合入一致性](../work/next-experience/10/next08-integration-equality.json)、[release](../work/next-experience/08/release.md)。生成dist须Tester重建，不在源等价证明内。06已获通知先同步08窄runtime guard再继续表达流改动；其新候选需重新验证受影响组合。

本票唯一范围：既有首页活动入口与限定成品关联记录；复用01问题／选择／确认合同，主题fixture记录由01协调归档，不能创建竞争供给权威。 App由03唯一维护，Pi runtime／问题合同与静态供给清单由01维护；main／router注册和合入由集成负责人维护。测试、构建与安装仅Tester执行。当前不声明本票验证通过。

负责人：implement_next_activity_flow。状态由主会话／集成负责人维护；测试执行仅专职Tester。

范围依据：[已批准规格](../docs/plans/ceres2-next-experience-spec.md)；[总 TASK](ceres2-next-experience.md)。

**交付：** 用户点击已有首页“减脂活动”卡，进入受限真实成品集合，选品、清单到确认加购，保留退出和修改目标能力。

前置放行：01受控技术已放行（2026-10-06 09:07 UTC）；本票尚无实现／验证通过。

**阻塞：** [01 零食选类到确认加购](ceres2-next-01-snack-selection.md)

**验收条件：**
- [ ] 使用既有卡片和现有选择／确认链，不新建活动平台。
- [ ] 沙拉／拼盘／饮品只作为真实成品，不能自动拆食材；未具供给不编造商品。
- [ ] 当前预算、数量、饮食、库存和报价保护与普通购物相同。
- [ ] 主题外新目标明确更新／退出，旧问题和选择正确失效。
- [ ] 活动名称不作为减脂功效证据；日期／折扣有来源，未确认奖励／日程／文案不加入。

**迁移／数据：** TOP-成品最小主题集合和现有卡片映射，尽量用已存在成品 Offer；每项来源、包装、价格、库存、主题关联可追溯。GREENRESET／FreshBreak 仅灵感。

**必要证据：** 真实首页点击→候选→清单→确认和购物车状态；成品不拆分、无匹配、主题退出、库存／价格变更；按需补真实主模型样例，不拿静态截图当闭环证据。

## 下一步与证据

前置01已获受控技术放行；从本次释放集成tip建立独立工作树，先准备公开可观察RED场景交Tester，后进行最小纵向实施。现有问题／确认合同直接复用，共享修改先协调唯一维护人。

执行证据目录：`work/next-experience/08/`。受控测试、真实模型、真实 UI、自然语言审阅与本人验收分别记账；当前全部未验证。完成实现只能记待验收，不能代替本人验收。
