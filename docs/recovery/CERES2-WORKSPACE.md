> Recovery backup of the cloud Agent workspace-root entry, captured 2026-10-07. Paths below are relative to the Agent workspace root, not this repository. This copy is not a second task status tracker.

# Ceres2 云端工作区恢复入口

更新：2026-10-07。用户要求把工程位置、参考项目和交付约定写在云端 Agent 根目录。本文件是定位入口；实时任务状态仅由仓库 `tasks/` 维护。

## 从这里接手

1. 当前工程：`ceres2_rebuild_20261007/Ceres2/`。远程为 https://github.com/2061623884/Ceres2 。重建基线为 `4bed9c891261e382122d424825b649989ea92c92`，实际分支 `ceres2/judge-prefetch-rebuild-20261007`。
2. 进入工程读取 `AGENTS.md`、`PROJECT.md`、`docs/plans/ceres2-judge-prefetch-spec.md`、`tasks/ceres2-judge-prefetch.md` 及每票文件。新规则以本次重建决定和最新用户指令为准，旧阶段的“未授权／无 remote”不覆盖本次明确授权。
3. 执行 `git status`、检查当前提交与远端分支。记录未提交改动并保护它们。源码缺失时先定位原仓库或已验证备份，不用旧版或重新生成的代码冒充丢失的版本。

## 本轮已确认范围

- 可可新自由文本的 Kev 只判断是否转墨墨；切换仍需用户选择。墨墨不走入口 Kev，返回可可使用明确按钮。
- 可可内部政策判断与预检索，将完整请求和实际证据交给同一个 Pi；同请求相同范围与有效版本复用，新问题、证据缺口或失败允许补查。
- 商品检索仍由 Pi 调用现有业务工具，本轮不加入商品预检索或向量 RAG。
- 选择性引入官方 DeepSeek 主机的 thinking 关闭适配；模型选择和提高输出额度不属于本次修改。
- Prompt 参考 learn-claude-code 与 mu 的源码组织方式，按实际职责和证据适配，不机械复制禁止规则。
- 前端实现交给用户在本地调整；云端提供稳定的后端交互契约和交接，前端及真实浏览器验收保留为开放项。
- 本地验收中的偏好回应被拦、商品条件映射、无糖属性、Kev 续接和记忆／Dream 问题写入 `docs/JUDGE-PREFETCH-HANDOFF.md`，不把这些历史失败冒称已修复。

## 参考项目位置与用途

与工程并列的只读参考目录为 `ceres2_rebuild_20261007/reference/`；实际拉取完成情况、来源 URL 与固定 commit 以其中 `README.md` 和仓库 `docs/references/ceres2-rebuild-reference-sources.md` 为准。

必须包括原始 https://github.com/2061623884/Ceres 作为业务与历史代码参照，以及本轮需要的 Pi、mu、learn-claude-code、Hermes 和两份售后参考。不能用原 Ceres 覆盖 Ceres2 主线；参考目录不参与 runtime import、构建或业务数据库加载。公开仓库只保存可复现的参考清单，不打包外部项目整仓。

## 执行与保存要求

按 Matt Pocock `implement-spec` 依赖图执行，功能顺序 01 → 02 → 03 → 04；只并行无共享写入冲突的工作。实现者按 TDD 写测试和实现，专职 Tester 执行验证，共享接口单一负责人，最后 Standards 与 Spec 分别独立审查。

每个可交付阶段形成真实本地 commit，审查提交内容后发布至上述独立远端分支，并核实远端 head 与源码树。若发布渠道产生不同 commit SHA，记录本地／远端 SHA 和一致的 tree SHA，保证用户能 checkout 远端版本。不要仅凭本地 commit 宣布代码已交付。

源代码、规范与必要的脱敏证据进入可追踪提交；密钥、`.env`、运行数据库、依赖与构建目录不发布。最终交付提供可拉取的分支／commit、验证范围及未测项。真实模型、浏览器、本人验收分开记录；历史通过不继承。

## 可用输入与历史边界

- 用户原 Spec／TASK 包：`ceres2_rebuild_20261007/planning-input/Ceres2-Kev-policy-review/`，归档 SHA-256 为 `52ae72e56ac0da2109aa02d07051689c4699c6a43fd084387614bdcd1d95d739`。
- 本地旧基线补丁及审查：`review_local_20261007/`；补充交接为 `review_local_20261007/delivery/JUDGE-PREFETCH-HANDOFF.addendum.md`。
- 历史云端 `f45c4ff92f96f535d156a2f88053ae10e8486fa1` 当前无法读取、未发布；本轮是用户明确授权的新实现，不能宣称恢复了相同源码或继承当时测试成绩。
- 本文件也应随仓库交付保存一份恢复副本；恢复副本仅供重建根目录入口，实时状态仍查仓库 TASK。
