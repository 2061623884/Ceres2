# 真实评测交付分支发布回执

2026-10-08 16:55:38 UTC（北京时间2026-10-09 00:55:38），主会话按用户“真实执行测评、补报告、最后推送”的授权完成首次普通push及远端读回。

| 项目 | 已核实值 |
| --- | --- |
| 仓库 | https://github.com/2061623884/Ceres2 |
| 分支 | `codex/ceres2-local-followup-20261008` |
| 首次发布的源码/报告候选完整SHA | `3cc8d804bb3fbd7f405bfb73f4f44c65b3550205` |
| 候选tree | `07118095d8fd4b801e8a8401b98887f1d1f56d56` |
| 已知起点 | `170fac0bc75fcc855897b073337ba218abeb5b7d` |
| 最终driver/harness源码 | `cbca5d15bd40bd200f542d0eeaa1bc8192af9424` |
| 实际100次执行HEAD/工具源码 | `00b397443bd7258d2166c6445ac4ac066cefd21d` / `739f13ead0c53ce9d82519efc30f51263e29ab45` |

实际命令由主会话在交付工作树执行，均exit 0：

```text
GIT_TERMINAL_PROMPT=0 git push --set-upstream origin HEAD:refs/heads/codex/ceres2-local-followup-20261008
GIT_TERMINAL_PROMPT=0 git ls-remote --heads origin refs/heads/codex/ceres2-local-followup-20261008
```

远端读回行为 `3cc8d804bb3fbd7f405bfb73f4f44c65b3550205 refs/heads/codex/ceres2-local-followup-20261008`，与本地候选完整SHA一致。没有merge/rebase/cherry-pick/force push或部署。只读工作树元数据显示原main仍为`b118dbea3852026c6a04c790b1e27df67c3c9c18`、旧优化分支仍为`6734c7fe79e670df2dae12b065dcc49c0b10a307`；未清理原现场。

本回执记录上述已经核实的候选。其后仅补本回执、交付状态文字及Tester检查记录；这些文档后继的最终完整SHA由主会话再次普通push、读回后回报，避免在提交中写入尚不存在的自身SHA。真实100原轨迹与66/30/4判分保持原版，没有新增模型采样或重评分；整体及本人验收仍开放。
