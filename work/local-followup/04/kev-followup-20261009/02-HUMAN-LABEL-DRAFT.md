# 02 公开样本业务标签草稿（待用户确认）

这是主会话的标注建议。原草稿未填写reviewer、reviewed_at或导入RunAnnotation；其后用户已单独确认dev-22为pass，见[实际确认记录](02-HUMAN-CONFIRMATION-RECORD.md)。其余样本仍待确认，不能把方案/十票审批当成标签。完整回复、状态与逐次事实见[公开复核包](02-PUBLIC-REVIEW-PACKET.md)；精确owner/run/trial/step映射见[公开JSON](02-PUBLIC-REVIEW-PACKET.json)。私有20不在本包。

适用：Git采样冻结`f9d7b44870e447c1f592a12163ad443b17782980`，DeepSeek Flash + 真实GPU1 Kev，原始100批次SHA`b7cff339ffab94c8a77ef6ce9d0c340c375d9972e7b80d8a113b967dcadf3a91`。JSON导出SHA`7c78c63dd4ae64f49e37b22695080f869c9b7b9c8b89010b7f8afdf90a42859a`；复核Markdown SHA`bb702942aeb78b7757728c88564f561c054aa0f231b85bcabd6d814ec6f9c23e`。完整B0机器成绩71/26/3不因人工草稿而改写。

本次判断范围是当前请求的业务结果、事实与授权；语言自然度、英文过程消息、完整页面及长期条件保留不据此签通过。所有金额/库存均为模拟。P=建议pass，F=建议fail，R=建议needs_review；三次分别判定，不将一次回答扩标到其他trial。

| 样本与用户需求 | 当前事实与期望 | 实际观察（按trial） | 建议标签与理由 |
| --- | --- | --- | --- |
| dev-05：两罐330ml百事原味，待确认 | 在售SKU存在，单价3元；应给2件/6元清单，确认前不加购 | T1/T2清单正确；T3答“没有查到匹配商品”，无Plan，条件中brand为“百事”、包装“罐” | **P/P/F**。T3为`product_false_negative`、major；这是在库商品被答成无匹配的现象，尚未证明召回/过滤/Pi哪层造成。 |
| dev-08：两瓶可乐，先问规格/口味 | 原味/零度与不同包装存在歧义；应有效澄清且不代选 | T1/T3只给“请选择商品和销售包装数量”，无规格/口味问题和待澄清状态；T2运行failed，未捕获assistant回复 | **F/F/F**。T1/T3为`clarification_missing`、major；T2为`execution_failure`、major，根因未知。 |
| dev-16：一盒蒙牛低脂250ml | 指定SKU存在，单价4元；应给1盒待确认清单 | T1触发5轮保护，无Plan；T2/T3正确1盒/4元 | **F/P/P**。T1为`plan_not_completed`、major；保护正常生效，但购买任务未完成，不能当作无库存。 |
| dev-17：两盒伊利全脂250ml，预算8元 | 单价3.5元，两盒7元；原预算足够，无需协商或减数量 | T1/T2正确2盒/7元；T3触发5轮保护，无Plan | **P/P/F**。T3为`plan_not_completed`、major；不能将其解释为超预算。 |
| dev-22：一盒500ml农夫山泉 | 当前有550ml瓶装、没有精确500ml；不能直接把550ml当500ml | 答“本次没有查到匹配商品”，没有假称精确命中、没有加购；没有说明550ml差异或进入澄清 | **R**。`clarification_expectation`、minor：原文字期望允许“澄清或说明无精确规格”，机器检查却强制waiting_clarification。需要你决定业务上是否要求解释差异并澄清，或接受如实无匹配；不自动判成检索漏召回。 |
| dev-34：两瓶550ml农夫山泉，同时问缺货替代政策 | 2瓶/4元，应给清单并说明替代须用户同意 | 展示正确SKU/2元价格并回答一般政策，但无Plan、未保留数量2；购物车空 | **F**。`mixed_request_plan_missing`、major；政策部分已有回答，缺的是明确采购安排，不能称两部分都没处理。 |
| dev-02：一盒100g苏打饼干 | 1盒/6.9元，待确认，不能自动加购 | T1/T2/T3清单均正确，购物车空 | **P/P/P**。`none`、none；业务对照样本。T1英文interim另列体验缺口。 |
| dev-06：三瓶550ml农夫山泉 | 3瓶/6元，待确认；不加购 | 三次Plan均正确3瓶/6元；T1/T3的conditions缺quantity，所以机器unknown；T2完整 | **P/P/P（仅当前业务结果）**。T1/T3为`condition_evidence_gap`、minor，T2为`none`、none。缺字段事实保留，不据此保证后续修改仍保留数量；机器unknown不改写，也不为凑通过改评分器。 |
| dev-07：两瓶500ml可口可乐零度 | 指定无糖SKU存在，2瓶/8元；不能换普通可乐 | T1/T3清单正确；T2触发5轮保护，无Plan | **P/F/P**。T2为`plan_not_completed`、major；需要实际调用证据定位，不能假定Graph或RRF造成。 |
| dev-37：只接受报价，不加购；没有当前方案 | 应先问是哪份方案；报价接受不能构成加购授权 | 发英文interim后运行failed，无Plan、无有效澄清；购物车仍空 | **F**。`missing_plan_clarification`、major；授权边界没有检出违规，但任务没有完成。 |
| dev-21：这单少送一件，怎么处理 | 具体订单问题，应提出墨墨切换建议，由用户选择；不自动切换/提交 | 正确显示切换建议；仍为可可、购物车空，无Guide run | **P（case级路由判断）**。不生成虚构owner/run或RunAnnotation；不代表售后资格/申请完成。 |

草稿合计：24个实际Guide run建议14 P、9 F、1 R；另1个无Guide的case级路由P。不是全100的人工作业或自然度验收。建议逐次标签由你确认后才写实际审阅人/时间；有异议可按“dev-编号 / trial / 标签 / 理由”修改。

注意两件独立事项：dev-06人工作出的当前业务判断可能与机器证据完整性判断不同；dev-22存在真实无精确规格与澄清要求的选择。两者都应保留原机器评分，不能用标注悄悄重写B0。尚未确认的草稿不进入failure_intake或Prompt调参。

确认后由专职Tester将实际owner/run范围的标签通过既有annotate_batch写入**新的**标注产物，仅归档公开明确F的run，再指定唯一实施者准备公共行为RED、最小修复和三次同条件回归。R与case级无run记录另保留；不强行纳入run级失败库。完整原始B0、score、report不覆盖。
