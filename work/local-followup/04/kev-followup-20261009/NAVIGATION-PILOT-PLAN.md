# Kev 导航公共 API Pilot 计划

状态：预声明，未执行。等待主会话确认 launcher GREEN 且本树隔离 API 确实运行在 127.0.0.1:8017 后，再启动真实 HTTP pilot；本文不授权当前启动服务。

## 来源与边界

- 计划基于固定工作树 HEAD `8c136eecf98cc4b37a2ffe7924c6f245a02315a1` 的公共导航合同：[`navigation.py`](../../../../backend/app/api/navigation.py)、[`navigation schemas`](../../../../backend/app/schemas/navigation.py)、[`navigation_service.py`](../../../../backend/app/services/navigation_service.py)。隔离 launcher GREEN 见 [首 GREEN](./LAUNCHER-GREEN.md) 和 [Memory 配置增量 GREEN](./LAUNCHER-GREEN-MEMORY-DELTA.md)；直接 Kev 协议样例见 [9-call pilot](./KEV-PROTOCOL-PILOT.md)。
- 只调用 8017 隔离 Ceres API 的 session/opening/routes/prompt-displayed/switches/opening endpoints；所有 Kev 判断通过现有 8009 的 `kev_provider.judge`，不直接调用第二条客户端、不替换模型、不注入分类结果。
- 不调用 `/api/v1/guide/turns` 或其他生成入口。导航只需要真实 Kev；主模型调用预期 0，政策预取 `judge_policy` 调用预期 0，购物车/订单/售后业务写入预期 0。隔离服务按 launcher 合同运行正常生产 MemoryWorker；无 Guide 消息，不预期触发提取任务。
- 不使用旧 `provider_job serve`（它绑定旧 runtime 状态路径），不碰原工程 `.env`、旧 DB、旧评测批次或私有20。所有 API session 仅在本树隔离 DB；每个 case 用独立 cookie/owner 与新 session，同一 case 的 route replay 复用原 cookie/session/body。
- 这是 API/服务合同检查，不是 browser 可见性证明，也不是新100基线。`prompt-displayed` 由测试客户端按公共接口确认，不代表真实浏览器显示过。

## 预声明矩阵

规范化 case manifest SHA-256：`b0bd0126e64de804c21c2280a875d9842a1a28059b237843477b6a51cadc629a`。六个不同的 request id；其中 accept case 对 `/routes` 同 body replay 一次，因此预期 7 个 `/routes` HTTP 请求、6 次真实 `judge` 请求。

| Case | request_id | 原始中文输入 | 既有直接 pilot 观察 | 流程 |
|---|---|---|---|---|
| `nav-accept-handoff` | `kev-nav-accept-201` | 昨天提交的订单 ORD-DEMO-102，我现在想取消这笔订单并退款，应该怎么处理？ | `yes`（仅上一轮单次观察，不是独立金标） | accept；相同route body replay |
| `nav-decline-switch` | `kev-nav-decline-202` | 我已经提交的订单 ORD-DEMO-100 刚才发现少了一盒鸡蛋，能帮我申请售后吗？ | `yes`（仅上一轮单次观察，不是独立金标） | decline |
| `nav-no-shopping` | `kev-nav-shopping-203` | 我在挑牛奶，帮我比较一下低脂和全脂哪个更适合做早餐。 | `no`（仅上一轮单次观察，不是独立金标） | none |
| `nav-no-general-policy` | `kev-nav-policy-204` | 一般情况下，超市买到的商品可以在几天内退货？ | `no`（仅上一轮单次观察，不是独立金标） | none |
| `nav-no-greeting` | `kev-nav-greeting-205` | 你好，今天有点热，想和你随便聊聊。 | `no`（仅上一轮单次观察，不是独立金标） | none |
| `nav-uncertain-submit-state` | `kev-nav-uncertain-206` | 我刚才那笔订单到底提交成功了吗？如果已经下单我想取消退款，如果还没下单就不用处理。 | `uncertain`（仅上一轮单次观察，不是独立金标） | none |

上述输入全为合成公开探针，`selected_object=null`。订单编号仅出现在消息文本中，不在任何真实订单库查询，也不产生业务写入。新 opening 的 `recent_dialogue` 为空；最后一条是“提交状态不明”的单消息歧义探针，**不覆盖跨轮上下文歧义**。

## 每个 case 的公共 HTTP 步骤与断言

1. 使用自己的 cookie jar 发 `GET /api/v1/bootstrap`，从当前服务返回值读取 store/zone；创建一个 Guide session，然后 `POST /api/v1/navigation/sessions/{session_id}/opening`，role=`keke`。不调用 Guide turn。
2. `POST /routes`，请求仅含预声明 request_id、opening_id、role=`keke`、原始 message、`selected_object=null`。记录单调时钟请求总耗时，并从响应只提取 `status`、`source_role`、`target_role`、`authorized_role`、`show_prompt`、`original_message`、`entry_judgment(outcome,elapsed_ms,reason)`、概率与错误类型；不保留完整 `provider_output` 或 HTTP 正文。
3. 预期 `yes` 才返回 `status=switch`、`target_role=momo`、`show_prompt=true`；这只是切换建议，`authorized_role` 尚空、`continue_original=false`，不视作自动切换或售后授权。预期 `no`/`uncertain` 留在 `keke`、不出现 switch prompt、原文完整保留。当前服务把非 yes 分支投影为 `ready/keke`；若真实输出不符预期，只记录差异，不改 response、不重试。
4. `nav-accept-handoff` 对完全相同 request body 第二次 `POST /routes`。期望返回相同既有 route receipt。必须同时有隔离 Kev 观察端可核验的 per-request 计数证据：首次决策计数 +1、replay 不增加。只凭 API 响应相等不能证明没有重复判断；若服务没有安全计数/审计接口，就将“未重复调用”记为不可观测，不宣称通过。
5. 对两个 `yes` case，只有实际 route 确实返回 switch 时才继续：按显示接口 `POST /prompt-displayed`，然后分别执行 accept=true 与 accept=false 的 `POST /switches`。接受后再 `GET /opening`，要求 role=`momo` 且 `handoff.original_message` 精确等于对应原文；本流程只验证路由交接，不向 momo 发送消息。拒绝后要求 role=`keke`、无 handoff、pending route 已消费。若判断未返回 yes，不强造确认动作，记录接受/拒绝分支未被触发。
6. 三个 no 与 uncertain case 只读 `GET /opening` 验证 role 仍为 `keke` 且没有 pending handoff。每种首路由只计一次真实 `judge`。

## 计数、时限与停止条件

- 分母固定：6 个不同 route request；HTTP route 请求数计划为 7（accept case 含一次重放）；真实 Kev `judge` 请求预期为 6。`judge_policy` 预期 0，主模型预期 0，Guide turn 预期 0。逐项保存 HTTP client elapsed 与 API `entry_judgment.elapsed_ms`，二者均使用 3 秒作为观察上限，不提高源码 timeout。
- 每个 case 最多一次原始判断；仅 accept case 重放同一已持久化 request，绝不重发成新 request id。Timeout、HTTP error、schema error 和预期不一致均保留原结果，不自动重试，不删除记录。
- 测量调用计数前，主会话须确认独立服务提供不会泄露输入/凭据的 Kev 调用观察方式。服务若只能提供总量，就记录执行前后差值；无法将计数归到该批则说明粒度不足，不把同响应或 200 当调用计数证据。
- 当前直接 pilot 的 9 条输出仅作为预先选分支的样本背景，非独立金标；导航 API 结果另行记录，不能把这 6 条宣传为精度评测或新环境完整基线。此计划不改40旧 cases/rubric，也不触碰20验收题。
