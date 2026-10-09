# 04 真实模型评测与失败反馈

- 状态：进行中；to-spec、三个测试入口与10票粒度/依赖均获用户明确确认，正式逐票发布并进入implement-spec。当前执行01技术接入；已有探针/5b24候选不继承验收，真实Ceres路由/完整新基线、售前修复/图对照/人工反馈及综合体验验收未完成。
- 负责人：主会话协调，Tester 运行与维护隔离验收；产品缺陷另指定唯一 owner。
- 所属：[总 TASK](ceres2-local-followup.md)；[规格](../docs/plans/ceres2-local-followup-spec.md)。
- 前置：01/02 场景/脚本/评分冻结；按用户最新授权复用原模型配置，其余原运行数据禁止迁入。配置可用性以本次Tester真实预检为准。

本次起点`00b397443bd7258d2166c6445ac4ac066cefd21d`（工具源码739）。test_optimization唯一负责限定模型配置只读复用、独立新状态与真实API/Graph/Memory/必要浏览器；acceptance_final_tester唯一负责原60组合包/100计划的真实新批次及隔离20题。原离线计划及v1-v4不覆盖；pilot/真实报告写`work/local-followup/04/real-model-20261008/`，真实capture/模型日志保持Git外，失败和未知如实报告。

## 2026-10-09 下一轮设计讨论

后续仍在当前工作树/分支，旧交付起点`8c136eecf98cc4b37a2ffe7924c6f245a02315a1`，已做探索候选为`5b24c4b1c0fde053e46c916e8b4e935fb54eb7c9`。用户确定的业务顺序和三项设计决策保持，且已按其要求完成to-spec与to-tickets审阅：[已确认规格](../docs/plans/ceres2-kev-quality-followup-spec.md)、[已确认任务图](../docs/plans/ceres2-kev-quality-followup-tickets.md)。当前售前产品源码未改；只按已获批票据执行，不合并、不推送或改原项目。

用户后续要求“按照to-spec→to-tickets→implement-spec执行”，并对完整呈现的scope/接缝/10票图回复“认可规格、测试入口及10票依赖”。Tester此前只读核对草案链接、编号与依赖无环；Root随后正式发布逐票文件。审批不代替执行/评测或人工标签本身。

Kev同时影响角色入口与政策预取，因此接通后的新基线与旧缺配批次条件不同；旧66/30/4保留为原环境结果，不离线改成新成绩。Graph当前仅用于显式菜谱关系探索，正式100调用0不等于该工具接入失败；已有Local/Global组件查询约18秒，不能替代15秒Pi集成测量。实施方案沿[原规格中的下一轮讨论](../docs/plans/ceres2-local-followup-spec.md#下一轮真实问题改进设计讨论)细化。用户已确认：主会话整理8–12条公开样本与草稿，由用户确认人工标签；图只有质量和15秒均达标才进核心；受影响场景各三次达标、完整候选与新环境基线检查无回退，剩余失败保留。标签本身尚未确认，未执行新基线或产品修复。

用户明确Kev是其在amax GPU1的本地部署；Tester此前只读确认8009 loopback候选进程、`amax-direct-download`中的完整base权重缓存元数据和GET models HTTP200，原.env缺KEV_BASE_URL。现态不是模型协议/中文分类/3秒通过证据，实际pilot另留`work/local-followup/04/kev-followup-20261009/`。仅连接现有服务，不重启/改原配置；服务事实和实际推理证据分开留存。

真实协议pilot见[9次记录](../work/local-followup/04/kev-followup-20261009/KEV-PROTOCOL-PILOT.md)：7次角色judge、2次policy judge；9/9有效schema且模型标签kev-latest，226.988–361.898ms、错误/超时0、不重试。8条预设类别全部一致，单消息歧义例uncertain只作观测；不是独立分类准确率或跨轮上下文验收。模型卡片schema是models[].name，已确认torch/float32/Qwen3.5-4B-Base，实际进程在GPU index1。当前尚未通过Ceres公共导航接口或运行新100基线。

当前责任：Root维护TASK/规格/Git；followup_experience唯一维护01/02所需评测入口，test_optimization独占01服务/协议/浏览器验证，acceptance_final_tester独占02私有20与正式100批次。03–10在前置未满足时不得实施；具体owner届时指定。共享入口/Prompt/schema未转交并发修改。

## 已确认纵切票据

- [01真实Kev交接与政策预取](ceres2-kev-quality-01-real-kev-routing.md)：当前可执行。
- [02新基线与人工标签](ceres2-kev-quality-02-baseline-labels.md)：依赖01技术门槛。
- [03商品/澄清](ceres2-kev-quality-03-product-clarification.md)：依赖02。
- [04Plan/混合政策/确认](ceres2-kev-quality-04-plan-confirmation.md)：依赖03。
- [05真实Pi图对照](ceres2-kev-quality-05-pi-graph-evaluation.md)：依赖04。
- [06售后生命周期](ceres2-kev-quality-06-aftersales-lifecycle.md)：依赖02。
- [07显式记忆](ceres2-kev-quality-07-explicit-memory.md)：依赖02。
- [08提取与Dream](ceres2-kev-quality-08-extraction-dream.md)：依赖07。
- [09页面/多消息](ceres2-kev-quality-09-browser-experience.md)：依赖05/06/08技术门槛。
- [10最终验证交接](ceres2-kev-quality-10-final-verification.md)：依赖09技术门槛。

## 范围与验收

- [x] 40 公开回归、20 新隔离验收、20 核心各三次，共 100 计划执行；先核对 pilot，再同版继续，失败/未执行均保留。本次100 attempted，不表示100业务通过。
- [ ] 实际功能、关键违规、等待/拒绝、逐轮时延、首个有用结果、usage 覆盖与核心稳定性分别报告。
- [x] 真实官方 GraphRAG build/local/global，以及 Memory 提取/Dream 所需实际调用；不以脚本 fixture 代替。Graph为组件180s，Dream为独立10合成初态+真实模型；正式Guide图/自然Dream未满足另留缺口。
- [ ] 采集→显式标注→失败回归→有依据修复→同条件版本比较形成一次闭环。自然度由人工判断，模型诊断不替代业务事实。
- [ ] 本人接受 UI/语言质量；未完成保留待验收，不因程序结束关闭。

原工具交付证据：[20新验收与60bundle/100离线计划](../work/local-followup/04/ACCEPTANCE-MANIFEST.md)。当时100planned/0attempted/100not_run/100unknown，原未执行误评分8fail和离线修正版本均留存；没有HTTP/模型调用仅描述该离线批次，不覆盖本次新真实执行。来源、病例隔离局限明确，不能称盲测/泛化。

本次配置预检确认原amax使用`deepseek-flash`且Memory模型已配置，Kev地址缺失。沿最新“使用原配置”指令保持该模型，不沿历史qwen记录另选模型。Kev缺项须记录实际路由合同及失败原因；若现产品可继续真实Guide，可采样主Pi/Graph/Memory，不把fallback记为真实Kev成功。

本次真实最终计数：planned100/attempted100/not_run0，business66 pass/30 fail/4 unknown；20核心60试次44 pass/13 fail/3 unknown、三次均达业务条件11/20，15秒100/100。phase outcome99 guide_run/1 runner_failed，后者也保留1个completed capture，所以真实Guide capture/receipt为100，终态66 completed/24 waiting_confirmation/9 failed/1 protected。critical观察0、eligible分母99，不能签为系统安全或本人接受。Interim有39/100 run、43 events，不含tool progress；首useful无人标注保持unknown。正式生产Memory90 extract jobs completed，无自然Dream；独立合成10记录的真实Dream另列，不污染正式owner。真实Graph官方build86.3s，local/global组件样例使用180s而非Guide15秒预算。原输入/原始轨迹不覆盖，[任务报告](../work/local-followup/04/real-model-20261008/REAL-TASK-EVALUATION.md)与[组件/Memory/Firefox](../work/local-followup/04/real-model-20261008/REAL-COMPONENT-VERIFICATION.md)列实际命令、输入/source/hash及失败/未测边界。

另一个明确未完成项是完整售后/Memory状态setup与更多动作driver；当前正式任务工具只支持小型采购续问/确认/重放，独立Firefox模拟订单旅程另列。下一步先处理本次公开精确商品false negative、澄清不足、无plan依赖步骤分类和Kev缺配，再形成同条件优化回归；不补造人工标注或改变原结果。

## 后续实施顺序与可观察交付

1. 本次20核心pilot、同版续100尝试已完成，原始结果保留为DeepSeek基线。后续任何脚本/规则更正或产品修复建立新版本，不修改旧66/30/4。公开dev-01 trial3缺plan导致TypeError应补明确动作不可执行诊断；先验证已有public失败，不读取私有20调参。
2. 商品false negative/澄清/预算plan与混合政策失败按原run证据定位：检索成功不等于相关商品进入最终回答，protected不算完成。下一轮固定同一模型/Prompt/数据/索引，公开受影响用例复验，再选择需要的新独立验收。首useful和自然度由实际人工标注，不以39有interim的数量代签。
3. 本次真实Graph组件已运行，但正式100里Graph调用0；下步补显式Guide图任务与15秒保护实测/成本收益对照，而非拿组件180秒成功签生产达标。正式Memory未达自然Dream门槛，合成10记录一次真实Dream只验证工作流；更正/删除/冷却及完整自然生命周期仍按既有合同留证。原18检索开发题不证明独立泛化。
4. 订单/售后/记忆的完整评测只按当前公共接口补最小setup和预声明动作：先明确所需初始状态、授权及可判分结果，再指定唯一owner。优先补模拟采购确认至订单、目标订单售后明确确认/重放、Memory显式更正/删除；不搭通用工作流平台。新增动作由独立执行与评分负例验证，不扩展自动通知或真实交易。
5. 人工审阅实际采样中的对话/事实/检索/动作/时延错误，至少完成一次采集→标注→公开失败回归→最小产品修复→同条件复验→版本对照。可可消息及UI改进仅由这些证据驱动；独立验收正文不进入Prompt或调参。用户在真实页面接受自然度与Grok bot风格后才关闭本人验收。

本次真实基线与组件已经执行，上述标明的下一阶段优化、更多driver、反馈闭环与本人验收仍未执行；本次报告发布不关闭更广整体规格。
