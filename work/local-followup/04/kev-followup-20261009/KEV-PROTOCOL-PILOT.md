# Kev 协议与中文路由小样本

日期：2026-10-09。状态：有限真实服务 pilot 完成；这不是独立准确率验收，也不代表已接入 Ceres API。

## 版本与隔离

- 集成工作树 HEAD：`8c136eecf98cc4b37a2ffe7924c6f245a02315a1`。
- 实际调用源码：[`backend/app/services/kev_provider.py`](../../../../backend/app/services/kev_provider.py)，SHA-256 `5059a7e61dda6590b57c17532fb96f6907db6b5c40ab213c728964bdba824566`。
- 角色判断版本：`ceres2-coco-role-entry-v1`；政策预取版本：`ceres2-coco-policy-prefetch-v1`。角色指令 SHA-256 `37abcbe05986697e84eb3dad377ebbf7a92ca80f92123dd52b07c1cceef7aa8c`；完整行为以该源码版本中的 `INSTRUCTIONS`、`CRITERIA` 及 `judge_policy` 定义为准。
- 规范化公开 case manifest SHA-256 `a5d777a49c8385f4b9592dcbd0dd66d3ef64ecea7cddb0325713cca090edf294`；仅输入/上下文 SHA-256 `e5c046f0cab6e480c432ee3e63190214818766a6bde56c29d29f38cad8125303`。
- 环境由 `env -i` 隔离，仅给 provider 子进程设置 `KEV_BASE_URL=http://127.0.0.1:8009`，并保留 HOME/PATH；集成工作树 `.env` 不存在。没有启动 Ceres API、访问 DB、调用主模型或重试请求。
- 直接调用当前 `judge(state)` 与 `judge_policy(state, remaining_seconds=3.0)`；角色和政策预取都受 3 秒 timeout 限制。
- 忽略目录结构化记录：`work/local-followup/04/kev-followup-20261009/tmp/kev-protocol-pilot.jsonl`，SHA-256 `9347bf6f52b5ced56ffaed0e990812efd1be6d1d4704092d4af42763611a8f53`。它仅保留合成输入及解析后的字段/耗时/错误类型，不保留完整 HTTP 响应正文。

## 服务卡片与模型设备

- `GET http://127.0.0.1:8009/v1/models`：HTTP 200，schema 为 `models[]`，共 2 个卡片。
- `kev-latest`：`base=Qwen/Qwen3.5-4B-Base`，`device=cuda`，`backend=torch`，`dtype=float32`；`run` 字段出于安全仅记为已读/已脱敏。
- `jev-latest`：同一 base/device/backend/dtype；`run` 字段已脱敏。Ceres provider 请求的是 `kev-latest`。
- 用户确认该部署位于 amax GPU1；服务卡片只报告泛化设备名 `cuda`。`nvidia-smi` 将服务 PID 2701504 映射到 GPU index 1，进程显存约 17,240 MiB。
- upstream HEAD `fe64b1274ea7f80d4095866df90666abb03e9cf6`；Kev adapter snapshot `139fdd94f1b6a6ad80cc15e08fcb99cac885a101`；Qwen base snapshot `1001bb4d826a52d1f399e183466143f4da7b741b`。

## 9 次真实 provider 调用

每个 case 只发起一次 HTTP 请求。正/负类别是本 pilot 预先写定的合同探针；歧义例不设金标准。耗时是本机单调时钟测得的完整 provider 方法调用时间。概率列按 yes/no/uncertain。

| Case | Lane | 输入 | 预设 | 实际 choice | 概率 (yes/no/uncertain) | Schema / error | 耗时 ms |
|---|---|---|---|---|---|---|---:|
| `role-positive-order-issue` | role-entry | 我已经提交的订单 ORD-DEMO-100 刚才发现少了一盒鸡蛋，能帮我申请售后吗？ | yes | yes | 0.6903 / 0.1194 / 0.1904 | valid | 361.898 |
| `role-positive-shipping` | role-entry | 我已下单并付款，订单 ORD-DEMO-101 显示已经发货了，我想查一下物流到哪了。 | yes | yes | 0.3655 / 0.2784 / 0.3561 | valid | 282.444 |
| `role-positive-cancel-refund` | role-entry | 昨天提交的订单 ORD-DEMO-102，我现在想取消这笔订单并退款，应该怎么处理？ | yes | yes | 0.5968 / 0.1394 / 0.2638 | valid | 279.431 |
| `role-negative-shopping` | role-entry | 我在挑牛奶，帮我比较一下低脂和全脂哪个更适合做早餐。 | no | no | 0.0149 / 0.7652 / 0.2199 | valid | 277.468 |
| `role-negative-general-policy` | role-entry | 一般情况下，超市买到的商品可以在几天内退货？ | no | no | 0.0355 / 0.7570 / 0.2075 | valid | 260.245 |
| `role-negative-greeting` | role-entry | 你好，今天有点热，想和你随便聊聊。 | no | no | 0.0088 / 0.8237 / 0.1675 | valid | 262.894 |
| `role-ambiguous-order-status` | role-entry | 我刚才那笔订单到底提交成功了吗？如果已经下单我想取消退款，如果还没下单就不用处理。 | 观察，无金标 | uncertain | 0.0881 / 0.3170 / 0.5949 | valid | 278.369 |
| `policy-positive-general-return` | policy-prefetch | 请问超市一般的生鲜退货规则是什么？商品买回家发现坏了能退吗？ | yes | yes | 0.6938 / 0.1472 / 0.1590 | valid | 226.988 |
| `policy-negative-shopping` | policy-prefetch | 帮我挑两款适合做早餐的酸奶，重点比较蛋白质和价格。 | no | no | 0.0382 / 0.6674 / 0.2944 | valid | 229.124 |

## 观察与边界

- 本次 `9` 次请求全部完成；`9/9` 返回 `kev-latest` 且通过当前 Pydantic schema，错误/超时 `0`。
- 有预设类别的 `8/8` 条与本 pilot 标签一致；歧义项返回 `uncertain`，仅作合同观察，不计入命中率。该小样本不是独立评测集，不能据此宣称分类质量达标。
- 歧义项没有附带多轮 `recent_dialogue`，实际覆盖的是单条消息里的订单提交状态不明；它不验证跨轮上下文消解。
- 单次耗时范围 `226.988–361.898` ms；九次累计 `2458.861` ms。样本均低于 3 秒调用上限，但没有测试负载下长尾、冷启动或并发时延。
- 已证实当前 Ceres provider 能以 `kev-latest` 请求服务并解析角色/政策两种响应 schema；这不是 Ceres 端到端导航/政策检索验收，不验证页面切换、重复请求、订单授权或真实业务写入。
- 本报告不修改产品代码、原 `.env`、部署服务、数据或索引；不替代后续独立基线和用户本人体验验收。
