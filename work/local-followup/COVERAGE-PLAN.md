# 当前版本测试与评测覆盖计划

适用起点 `170fac0bc75fcc855897b073337ba218abeb5b7d` 及本轮实际未提交源码。
这是执行前覆盖清单，**不是通过报告**。每项由 Tester 记录实际命令、源码/输入 hash、结果与缺口；正式状态在 [总 TASK](../../tasks/ceres2-local-followup.md)。

## 分层范围

| 层次 | 要观察的行为 | 已存在的测试/入口（存在不代表本轮通过） | 本轮证据要求 |
| --- | --- | --- | --- |
| 评测工具 | 身份/版本对照、精确标注、未知质量、失败归档、完整分母、错误价格负例 | `test_local_followup_evaluation.py`、`test_local_followup_baseline.py` | CLI RED/GREEN 与最终工具回归，合成证据不称真实 Agent 质量 |
| 购物规划 | 单菜/多人/多菜、已有食材、缺货/部分购买、规范数量与预算 | purchase/dish/multidish/supply/budget/quantity public suites | 最终同版 backend 全量；不能只检查非空 plan |
| 品类内选购 | 候选约束、当前商品身份/Offer、比较、选择及数量 | comparison、next snack/drinks、integration shopping suites | 当前供给事实与选定结果，确认前 cart 不变 |
| 角色与政策 | 可可判断一次、显式切换/拒绝、政策预取与请求内复用、未知/异常不伪装 | judge role/prefetch/reuse/safety、next navigation/shared policy | 公共状态与实际诊断，Thinking 精确官方 host wire 合同 |
| 对话与执行 | 原生完成、混合引用、可选经审校 interim、稳定消息、15秒/5轮保护 | native finish/reviewed interim、guide lifecycle/deadline/disconnect/recovery | 受控合同与真实客户端到达另列；自然度待人工 |
| 检索 | BM25/dense/RRF、namespace/alias/无答案、canonical ID | graph real BGE、graph backend/CLI、公开 retrieval dev | 独立当前模型缓存/新索引、18公开题结果及召回指标；不称 holdout |
| 官方图组件 | 官方库 BYOG/local/global、canonical witness、deadline/usage/provenance | graph official library/runtime/worker suites | 锁定知识环境受控传输；真实 LLM graph 另列 |
| 模拟生命周期 | 商品详情/加减、明确确认、订单、售后数量/照片/人工、重放幂等 | checkout/purchase/aftersales/human/order-case/integrated suites | 公共接口结果与浏览器旅程；业务均模拟 |
| Memory/Dream | 显式 CRUD、相关范围、迟到 fence、删除/重启、门槛/冷却/租约 | memory public/wire/atomic/deletion/background/dream/recovery suites | 受控模型与时钟合同；真实 extraction/Dream 另列 |
| 构建 | Pi 与前端类型/产物 | 两处 package.json、frontend 严格 TS 命令 | 当前 Node/依赖与源码/build hash；原项目依赖不借用 |
| 实际浏览器 | 真实 DOM、interim 在终态前可见、刷新/停止、模拟闭环 | 本机 Firefox HTTPS journey 脚本 | 原准备 run11 保持历史；若产品/浏览器脚本改变需新冻结新执行 |
| 真实任务质量 | 40公开/20新验收、20核心三次；实际硬条件、关键违规、等待/拒绝 | 新 task cases + HTTP/SSE executor + deterministic scorer | 100计划分母，先核对pilot；provider配置缺失保留未执行 |
| 本人接受 | Grok bot 风格与可可自然多条回复是否合适 | 用户在真实页面审阅 | 不由 API/模型裁判代签 |

## 运行约束

所有安装/测试/lint/typecheck/build/服务/模型/浏览器验证命令只由专职 Tester 执行。用隔离新数据库/索引/身份，不读原 `.env`、运行库或未授权 listener；用户本轮配置不因测试挪动或覆盖。

最终 backend 全量与知识环境补验按对应冻结源码分别登记，重叠测试不相加。中途 RED、脚本失败和修复前结果保留；更正评分只重评分并注明来源，不新增模型执行次数。

关键限制：运行 completed 不是质量 pass；未知标签/usage/金额/时延不填零；没有 Guide run 不造 capture。真实模型、Graph LLM、Memory/Dream 与用户审阅没有证据就保持未验证。
