# 02 新环境100次基线与公开失败人工标注

- 状态：待验收；新100基线及11条公开样本/逐次标签草稿已完成。用户已确认dev-22业务pass，其余10条的23个Guide run及1个case级路由判断待答复；未释放03/06/07，不记本票已验收。
- 负责人：独立验收Tester维护原输入和私有20；主会话整理公开标注包，用户确认。
- 所属：[04总TASK](ceres2-local-followup-04-real-evaluation-feedback.md)；[规格](../docs/plans/ceres2-kev-quality-followup-spec.md)。
- 阻塞：[01真实Kev接入](ceres2-kev-quality-01-real-kev-routing.md)技术门槛已满足；03/06/07仍等待本票基线及用户实际标签确认。

## 交付

产品经理得到补齐真实Kev后的完整、可复现100次基线和8–12条公开代表样本；本人确认事实、期望和标签，产品修复使用这条新基线比较。

## 验收

- [x] 原40公开/20独立输入、rubric和100矩阵保持原版；先20pilot后同版续跑，失败/未知/未执行保留分母，不重跑冲成绩。
- [x] 固定源码、磁盘/运行时标签、模型、Prompt、语料/索引、配置与采集/评分器版本；新owner独立，不覆盖旧66/30/4。已加载源码等价性和未可观测配置保持unknown，不能把版本标签当成等价证明。
- [x] 功能、角色等待、澄清、保护终止、critical、Guide15秒分别报告；页面入口总耗时、完整usage/费用及Memory/Dream调用未观测，明确保留unknown。
- [ ] 公开8–12条样本有实际输入/回复、当前事实、期望、标签草稿；用户确认后记录实际审阅人/时间，Agent草稿不记成人工。
- [x] 私有20仅聚合回传，不向实施者披露题面/标识；公开与隔离边界及统计局限明确。

## 证据与下一步

新批次与旧批次分目录、分版本留存。实际在既有隔离API8017执行，raw仅独立Tester可读，写`work/local-followup/tmp/independent-acceptance/kev-20261009/`。安全证据：[冻结](../work/local-followup/04/kev-followup-20261009/02-BASELINE-FREEZE.md)、[环境pins](../work/local-followup/04/kev-followup-20261009/02-ENVIRONMENT-PINS.md)、[20pilot](../work/local-followup/04/kev-followup-20261009/02-PILOT.md)、[完整结果](../work/local-followup/04/kev-followup-20261009/02-RESULTS.md)。原输入、评分规则及100计划保持；01的独立owner/Memoryjobs不合入正式100，02各case/trial使用fresh owner。

B0冻结提交`f9d7b44870e447c1f592a12163ad443b17782980`。100/100已尝试，97 Guide/3角色等待，准备及执行器失败0；机器business为71 pass/26 fail/3 unknown。97/97 Guide满足15秒，3等待没有Guide时延；核心60试次44/14/2、三次业务全通过11/20。critical观察0/100，不等于安全验收；原始B0人工标签0/97，后续单条业务标签另存不回写。Graph实际调用0，完整浏览器/自然度、后台Memory/Dream及费用不属于本批通过结论。采样后仅整理文档，未做商品/Pi/Prompt修复。

当前执行器实际SHA`0e0aa5e24708d53ce0e1354fb48c6e0f3776e3462b294120e6a0709677da8530`；旧缺配100使用过更早的执行器，后来的已发布窄修未重跑旧66/30/4。本轮固定当前执行器，不能宣称与旧批次只有Kev一个变化；后续产品候选与本轮B0保持同执行器比较。冻结报告必须列实际源码hash、服务启动pin与采样时Git提交，纯文档提交不等于重启加载新源码。

公开[完整复核包](../work/local-followup/04/kev-followup-20261009/02-PUBLIC-REVIEW-PACKET.md)、[精确映射JSON](../work/local-followup/04/kev-followup-20261009/02-PUBLIC-REVIEW-PACKET.json)和[标签草稿](../work/local-followup/04/kev-followup-20261009/02-HUMAN-LABEL-DRAFT.md)包含11条公开用例、25次执行，7个核心各三次、24个实际Guide run及1个无Guide角色等待。冻结公开包是标注前的原始快照，其pending字段不覆盖下文单独的实际确认与标注产物。原草稿14 P/9 F/1 R及无Guide case级P不是人工标签；dev-06当前业务结果与机器证据完整性分开，dev-22的原R已由用户单独确认P。当前仅执行1条annotate_batch，未执行failure_intake。

两项实际标注问题已发给用户。用户对dev-22明确回复“如实无精确匹配可接受，判pass”，[确认记录](../work/local-followup/04/kev-followup-20261009/02-HUMAN-CONFIRMATION-RECORD.md)保存实际来源及记录时间；Tester经现有annotate_batch完成唯一1条标签，退出0，见[标注回执](../work/local-followup/04/kev-followup-20261009/02-HUMAN-ANNOTATION-RECEIPT.md)。新的标注batch留Git外，除这条标签外与原batch逐字段相同；原机器fail不改写，没有重评分或failure_intake。其余样本问题仍待答复，此前方案确认不代替样本确认。其余标签确认及实际run级标注落盘后释放03/06/07；没有用户确认的样本不进入调参/失败归档。商品/Plan只读[源码地图](../work/local-followup/04/kev-followup-20261009/PRODUCT-PLAN-SOURCE-MAP.md)是诊断准备，尚未实施修复。
