# 下一阶段执行来源与基线

2026-10-06：从公开仓库 https://github.com/2061623884/Ceres2 新建独立 checkout；开始时工作树干净。

- Source commit：`64ca7b6b9a7aa113aa42d54270604913f6c19d58`
- Source tree：`4b39354b25076ed25b34083769909c6efbc68197`
- Integration：`ceres2/next-experience-20261006`
- 新 checkout 与原 dirty 工程分离；未覆盖原源码／配置，未读取或复制凭据、旧数据库、session、cart、order、checkpoint、私有 holdout。
- 最新 Ceres 视觉／业务参考：[ee7ce104885f731bc48bc8c6338c00d802ba0619](https://github.com/2061623884/Ceres/commit/ee7ce104885f731bc48bc8c6338c00d802ba0619)，仅来源参考，不允许运行时引用旧目录。

## 经批准输入

以下文档由 07:58 方案批准形成；后续用户消息 `Sentinel_8fc34df15f788191a593e0c1e46dde89` 批准正式十票及持续实施。仓库适用副本增加当前阶段说明并调整相对链接；以下是原输入 SHA256，不能当作调整后文件哈希。

- `ceres2-next-experience-spec.md`：`55dcb74c599248db91b4a84f2f8a4fcd74c8aa5594fec26879968a0ed016663e`；仓库副本 [ceres2-next-experience-spec.md](ceres2-next-experience-spec.md)。
- `ticket-proposal.md`：`c039a3cfd7f4845be393366ebbbcb367b171a3481960215eb35bb6e4010ae650`；仓库副本 [ceres2-next-experience-ticket-proposal.md](ceres2-next-experience-ticket-proposal.md)。
- `decisions.md`：`d292ea3e0e9f392ba174ac91d43fb1a86aa7967a10a7af2a767b3c0cf29781a1`；仓库副本 [ceres2-next-experience-decisions.md](ceres2-next-experience-decisions.md)。

来源要求 S01–S13 的完整映射已包含在批准拆分末节；完整行为与验收以规格为准。原规划的审计底稿不导入仓库，旧成绩不成为新候选证据。最新自然介绍／先结果后流式的决定保留在当前决定副本 R10／R11。

## 本次准备验证

已核对公开 HEAD、tree、初始 status、原规划哈希，读取根与 frontend AGENTS、tracker、领域词汇和两条 ADR、repo implement-spec／to-tickets 技能。尚未安装依赖或执行任何测试、构建、lint、typecheck、模型或页面验证；这些由专职 Tester 负责。
