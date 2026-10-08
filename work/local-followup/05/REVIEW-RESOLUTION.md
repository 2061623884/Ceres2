# 初次审查发现与修复依据

初次审查固定候选为 `e855d691d0a446c9e5385196134b55f2ec609320`，起点为 `170fac0bc75fcc855897b073337ba218abeb5b7d`。本文记录修复原因，不代替独立delta复审或TASK状态。

| 来源 | 问题或判断 | 处理与验证 |
| --- | --- | --- |
| Spec | 汇总缺Guide完成/终态、关键违规、逐轮15秒、首个有用结果和组合稳定性 | report增加分项分母与核心三次业务/时延结果；没有人工有用性证据时明确unknown，不用interim或首字节替代；`tester-report-cli-status-red/green.md` |
| Spec | 非可比较check值抛TypeError导致整批中断 | 保存值、类型和原错误原因到evidence gap后继续；未知operator的配置错误仍传播；`score-batch-noncomparable-red/green-v2.md` |
| Standards | 四个实际caller重复capture/annotation身份校验 | 抽取至现有`batch_runs.annotation_for_capture`，供compare/score/report/failure使用；共同回归覆盖原身份/格式行为 |
| Standards | runner/scorer重复分派三个预声明动作 | 保留独立执行与判分决策，避免评分直接复用执行器结论；不为三个现有动作新增多态平台。此为说明，是否接受由Standards复审判断 |
| 主会话自查 | 错误的方案合计或确认后cart金额可能未被判错；缺Offer提前跳过已知金额检查 | 核对selected行合计、确认后Offer单价/行额/总额；缺Offer仍核对已知金额，缺金额不填零；`score-batch-amount-closure-red/green.md`及`score-batch-missing-offer-amount-red/green.md` |

最终专职Tester共同运行21项evaluation、7项runner、1项受控真实TCP FastAPI/Pi smoke：29 passed，15.87s。适用源码为213文件manifest `29bdaf543db8b498dc30adb9deab2da14c8eeaac9bcaf456cc0612f71716ae91`，前后未变，见[最终报告](../01/tool-combined-reviewfix-final.md)。这些结果不代表真实provider质量、100次任务已执行或本人验收。

上述修复仅涉及evaluation与其测试/rubric；非evaluation产品源码相对170起点未变。原始失败及首次审查报告保留，不覆盖。

## 4e021候选delta复审的补充发现

[Standards delta](STANDARDS-DELTA-REVIEW.md)确认无硬违规，重复校验已处理，独立执行/评分分派为可接受取舍。[Spec delta](SPEC-DELTA-REVIEW.md)另指出两处诊断漏项：行额已知但数量/单价缺失时合计仍可核对；成功receipt商品不匹配后仍须核对cart金额。两项不构成已知错误被判pass的漏洞，但会遗漏可观察的critical细项或将可判的合计错误降为unknown，仍按现有rubric修复。

专职Tester分别证实receipt/cart漏报RED及部分行额合计RED，见`amount-delta-red.md`与`amount-delta-partial-total-red.md`；首轮RED未到达后一个断言，第二次调整断言顺序及源码版本另留证，没有把未执行断言算作红测通过。中间仅修合计后的结果继续RED在receipt场景，见`amount-delta-partial-total-intermediate.md`。两项修复后窄GREEN 1 passed，最终共同29 passed/15.73s，见[最终金额delta冻结](../01/tool-combined-final-delta.md)，213文件manifest `8d3724cba223fb46bc46eb198aaf3a378c2096e1e930b4648fda6f5ee1b6aa1a`前后未变。缺细节仍保持evidence gap，已知合计相符不自动pass；成功回执mismatch后独立列出cart金额违规。最终独立复审另留结果，本文不代签。
