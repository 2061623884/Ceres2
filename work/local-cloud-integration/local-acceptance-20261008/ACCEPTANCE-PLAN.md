# Ubuntu 本机验收执行范围

本文件是本机执行清单，不是第二份 TASK 状态。任务状态仍以
[九票总 TASK](../../../tasks/ceres2-local-cloud-integration.md)为准；执行结果由本轮 Tester 单独留证，未执行项不视为通过。

## 固定版本与来源

- 本机独立工作树：`Ceres2-integration-20261008`，detached HEAD。
- 源码／交接版本：`170fac0bc75fcc855897b073337ba218abeb5b7d`。
- tree：`295499ee22cc30485d38eba82e96330a39d7d573`。
- 发布分支：`ceres2/local-cloud-integration-20261007`。
- `90c8eab89397ee85454ce9b909206ffed7552e3e` 到该版本仅有文档／回执变更，`backend/`、`runtime/`、`frontend/`、`data/` 零差异；这是 Git 来源核对，不是重新测试。
- 云端 746 passed / 5 skipped、知识环境补验、183 项修复回归及最终 4 项检查分别属于交接记载的各自 pin。本机不重复累加它们，也不把它们登记为本机真实模型或页面验收。

执行依据：[当前 Ubuntu 交接](../../../docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md)、
[集成规格](../../../docs/plans/ceres2-local-cloud-integration-spec.md)、
[最终技术报告](../t09/FINAL-VERIFICATION.md)。

## 第一阶段：本机准备与受控浏览器

专职 Tester 执行安装、build、typecheck、索引构建和浏览器，不改变产品源码或依赖锁。

| 验证对象 | 可观察结果 | 证据边界 |
| --- | --- | --- |
| 本机 Python 与 Node 环境 | 独立业务／知识 venv、两处 npm 锁安装，pip check、Pi typecheck/build、前端 strict TypeScript/build 的实际退出结果 | 不借其他工作树环境；记录实际版本、lock、源码和 build hash |
| 新 hybrid 索引 | 固定 BGE revision 本地加载，新语料 manifest 与当前源码对应，公开开发用例实际检索 | BM25/BGE/RRF 证据；开发集不是独立质量成绩，不调用聊天 provider |
| 商品与订单 | 详情 → 明确加购 → 模拟结算 → 订单推进；确认前无购物车写入 | 真实页面／API 与模拟业务事实，不表述真实交易 |
| 角色入口 | Coco yes 时明确接受／拒绝；no、uncertain、error、timeout 继续原文；纯按钮不重放旧请求 | 真实页面与受控 Kev/Pi，不能证明真实模型判断质量 |
| 混合结果与消息 | 购物、政策和职责信息保留；多条审校过程气泡先于终态；刷新稳定 ID 不重复 | 真实 Pi SDK／SSE／浏览器；脚本控制模型输出，不证明自然度 |
| 停止与售后 | 停止后不再发布；选择订单、包装数量、照片、确认及对应工单 | 真实 LangGraph／API／页面，使用隔离合成身份和订单 |

使用固定版本的 [browser-support](../browser-support/README.md) 与
[浏览器旅程](../05/browser_journey.py)。若需适配本机浏览器，只改独立 harness 并记录其 hash；产品问题先反馈主会话，不为了通过测试直接改产品。

只使用本工作树的新缓存、索引、临时业务库和 fresh browser context。原 main 的 53 项 dirty、原 `.env`、运行库、session、checkpoint、旧索引和 holdout 均不读取或迁入。受控 fixture 需要项目 `.env` 不存在；本阶段不提前创建该文件。

## 第二阶段：真实模型与数据飞轮

这部分不随受控浏览器结果自动放行。按当前交接的真实 provider 范围完成独立配置后，再由 Tester 执行有限样本。不得把模板模型名当成换模型指令，不提高已有 temperature、输出额度或 15 秒预算；后台模型需分别配置。

| 样本 | 验收观察 |
| --- | --- |
| 购物＋一般政策混合请求 | 入口、政策判断／预取／复用、Pi、审校分别留证；引用有效，当前商品约束和 Offer 生效 |
| 同轮自然回复 | 可为零条或多条 interim；内容有必要、审校通过、无内部推理或未经证实事实，不按固定气泡数判断质量 |
| 菜谱事实与显式图关系 | 规范人数／用量与模型关系选择分别呈现；真实 GraphRAG Local/Global 的索引、调用、usage 和输出分别记录 |
| 拒绝／停止／刷新 | 没有重复气泡、旧请求重放或取消后的暂存业务提交；真实超时记录失败，不能提高预算后称原合同通过 |
| 运行采集 | 运行时版本与导出时源码分开，入口判断／检索／复用／主 Pi／审校／图调用分别计数，未知 usage／费用／时间保留未知 |

真实样本完成后，只导出新隔离 owner 的运行，使用现有
`app.evaluation.export_runs` 与 `app.evaluation.annotate_runs` 接口进行显式人工标注；未审阅样本的 labels 保留 null。失败样本附期望行为、实际证据及适用源码／Prompt／数据／索引版本，再进入公开开发回归；不自动训练或写入质量正标签。

## 本人验收与记忆生命周期

用户本人需接受整体 Grok bot 风格，以及切换、返回、详情、加购、订单、售后、过程消息是否自然、易懂。自动截图与脚本断言只提供审阅材料，不能代替本人接受。

Memory / Dream 沿用原任务的独立门槛，不用短聊天或一次 extraction 代替全部生命周期：聊天保存／查询／更正／删除，跨角色按需读取，迟到结果不覆盖更正／删除，重启不复活，以及真实 Dream 的 10 条／24 小时门槛、冷却和固定时钟边界。来源见
[显式记忆 TASK](../../../tasks/ceres2-runtime-upgrade-09-explicit-role-memory.md)与
[提取／Dream TASK](../../../tasks/ceres2-runtime-upgrade-10-recoverable-memory-dream.md)。

## 执行记录要求

每一层分别给出实际通过、失败、阻塞或未执行，附源码 pin、未提交 harness hash、依赖／build／数据／索引／模型／Prompt 版本和实际命令结果。保存截图、去敏摘要与进程清理结果；不提交模型缓存、数据库、凭据、原始 provider 日志或个人会话导出。本轮未执行 merge、rebase、cherry-pick、force push 或部署。

## 本机并行启动入口

Tester 在本机观察到原工作树已有 `8012` 服务，另有监听占用 `8013/8444` 与 `8014/8445`，本轮保留这些进程。当前产品 Vite 配置的 `/api` 与 `/media` 都固定代理到 `8012`；单独改变前端端口不会隔离后端。本机额外提供 [启动入口](start-local-frontend.mjs)，沿用当前 Vite plugins/config，仅在这次启动中把 frontend 设为 `127.0.0.1:8446`、两条代理设为 `127.0.0.1:8015`，产品源码不改。该对端口在本轮预检时空闲，后续启动仍以实际监听结果为准。

完成新工作树的独立模型配置，并具备真实 provider 执行条件后，在本工作树根目录使用 Node >=22.19.0，分别打开两个终端：

```bash
# 终端 A
(cd backend && ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8015)
```

```bash
# 终端 B
node work/local-cloud-integration/local-acceptance-20261008/start-local-frontend.mjs
```

浏览器打开 `http://localhost:8446`。此启动入口的本机检查与 run11 的受控 HTTPS fixture 是不同证据；不把启动脚本可用等同于真实模型或该 localhost 用户旅程已验收。若端口被别的进程占用，启动失败时保留该进程；不杀未知进程或接入原 `8012` 替代新后端。当前原始 Ubuntu 交接仍按其发布版本保留。
