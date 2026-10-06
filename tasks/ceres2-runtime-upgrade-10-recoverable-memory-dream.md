# Ceres2 Runtime 10：可恢复提取与 Dream

状态：**待验收**。
负责人：**implement_clean_memory_dream（TASK10 唯一实现负责人）**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过（主会话 2026-10-05 18:43 UTC 释放；受控技术范围）**。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户得到主回复后自动提取/整理记忆，重启后未完工作可恢复；途中显式更正或删除不会被迟到后台结果覆盖。

## 阻塞关系

[09 聊天显式记忆与共享边界](ceres2-runtime-upgrade-09-explicit-role-memory.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [x] 保留四类来源规则、自动 TTL、10 条/24 小时 Dream 门槛、独立模型和主回复不等待；不启用购物监测或通知。
- [x] 最小持久后台状态/唯一来源/租约和删除 fence 迁移、固定时钟 fixture 与通过聊天查询观察结果的 UI 旅程随票。
- [ ] 验证中断恢复、重复来源、模型失败不伪报保存、显式保护/不复活、不变内容不续期及真实模型耗时与后台分离。

- [ ] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [ ] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [ ] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开聊天完成结果与后续记忆查询，后台中断/重启后重新观察；模型故障通过已有模型边界注入。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

受控技术已释放，交接到后续切片及 TASK16 验收；主会话稍后协调本地提交，不推送。真实 qwen3.8-27b 采样／耗时、真实浏览器及用户本人验收仍待条件，不与受控通过混同。Mercury 超过 8,000 字符的自动提取明确记为整条失败，不支持静默前缀提取。

## 证据

当前实现、RED→GREEN、重启／租约／模型故障／显式删除与跨角色回归说明见 [执行证据](../work/clean-rebuild/10/README.md)；原始 Tester 输出见 `work/ceres2-runtime-upgrade/10/test-runs/`。历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-10-recoverable-memory-dream.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。

2026-10-05 17:54 UTC：TASK09 主会话技术释放后接手记忆模块；自动提取接缝为已提交 Pi/Mercury 回复事务 → 持久 job → 后续聊天 list。新公共测试已交 Tester，尚未实现。共享入口／配置／migration 由 foundation owner 接入；guide 由 TASK04→05 唯一 owner 接入。

2026-10-05 18:29 UTC：完成独立 extraction/Dream 模型、最小持久来源 job、租约恢复、30 天 TTL、10 条/24 小时 Dream、显式更正/删除聚合 fence、完整 8,000 字符源处理及 SQL 发布故障恢复。实际 Pi/LangGraph、安装的 OpenAI SDK＋本机受控 HTTP、生命周期与后续聊天查询已分轮验证。两轴发现的角色标签／完整来源／异常分类问题均有公共 RED 与定向 GREEN；最后补充显式阴影/墓碑前驱不得进入 Dream 模型上下文的有效 winner 过滤，待 Tester 复验。未改购物监测/推送，未接触旧数据库/凭据，未提交/推送。

## 2026-10-05 18:43 UTC 主会话技术释放

- 最终两次独立 Tester 验证分别 **109 passed / 109 passed**（116.69s / 113.91s），覆盖 TASK10、09、03 恢复、Mercury 14/15 与 foundation。
- 四次前后快照所消费的 backend/Pi/config/schema/tests 完全一致，指纹 `65f02da9b92bef9ed56c6bdec659522746087d6f2497aa0bdf91d011cf62f0f1`；仅无关 TASK06 UI/tests 改动排除在外。
- Standards / Spec 均关闭于最终 `memory_background.py` SHA `2faffdf6f725acdf2b01f444eefd6345c5c2dabc895fadb7e853026e0f839f36`、`memory_service.py` SHA `ff86cf0f152957a716b1ba7ccded84b705b5ba551b9d72304074aa8e4259bcd7`。
- 最终证据：`work/ceres2-runtime-upgrade/10/test-runs/final-memory-background-01/`、`final-memory-background-02/` 与 `final-background-source-comparison.json`。
- [释放源码清单](../work/clean-rebuild/10/release-source-manifest.json)；[TASK16 交接](../work/clean-rebuild/10/HANDOFF-P16.md)。真实模型/页面/用户本人验收未完成，不写整体已验收。
