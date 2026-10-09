# 02 B0 user-confirmed annotation receipt

日期：2026-10-09。仅将用户明确确认的 public run annotation v2 写入新的 ignored annotated batch。原始 B0、machine score/report 和冻结 public review packet 均未修改；没有重采样、调用模型/API、修改源码或运行 `failure_intake`。

## 精确标注

- Case / trial / execution：`dev-22` / 1 / `dev-22:trial:1`。
- Owner / run：`owner-1cf4ba9d3bdf4acf88d267db0dc8a44e` / `run-c9770d8268d94ff993bf16f46340abdb`。映射来自冻结的 public-only review packet。
- Annotation schema：`ceres-run-annotation-v2`。
- Verdict / error_type / severity：`pass` / `none` / `none`。
- Expected behavior：无精确 500 毫升 SKU 时，如实说明未匹配即可；不强制追问，不将 550 毫升说成精确匹配，也不擅自替换或写入购物车。
- Rationale：用户明确接受如实说明无精确匹配；本次未生成商品方案，购物车为空，也未出现虚假的 SKU 匹配。
- Reviewer：`项目用户（本会话）`。
- `reviewed_at`：`2026-10-09T06:54:10Z`，这是确认记录时间，不宣称是用户点击的精确时刻。

## 执行与证据

- 使用现有 `backend/app/evaluation/annotate_batch.py`，SHA-256 `0e44aecfeceba5ae1c49c6f10bd2bd4e08d327c6ed5e61ac9f5bdf27a9ef46bf`。CLI 退出码 0，返回 `cases=100`、`annotated=1`。
- 原始输入 batch SHA-256：`b7cff339ffab94c8a77ef6ce9d0c340c375d9972e7b80d8a113b967dcadf3a91`。原 machine score SHA-256 `f13999f215cb0e82a90ad988e75d7971e38a1c50c6fd1a7b9d5bb8bffb164d92`；原 report SHA-256 `95c0864939ad121a1c6a81ea8ce572ee661d55552f03b6083b2f1e466e57aacf`。
- 新的 ignored annotated batch：`work/local-followup/tmp/independent-acceptance/kev-20261009/02-baseline-human-annotated.json`，SHA-256 `b82cedbf2395f211326785c9b7f01abf14ceb9f8e3ac99a0ee8db869c50eaaa6`。独立 annotation JSONL SHA-256 `f919cdc3c051ddf55789d665764edac30c6a0edfb0982549a690995765100005`。
- 离线核对确认：annotated batch 中只有一个 unique owner/run 被标注，且仅为 `dev-22` trial 1；移除新增 annotation 并恢复原始 labels 字段后，新 batch 与原始 batch 逐字段相同。原 machine verdict 仍为 fail；未改写原始 score/report，也没有对 annotated batch 重评分。
- public review packet 中共 24 个实际 Guide run；本次确认 1 个，其他 23 个仍 pending。无标签写给其他运行；无标签用于 route-choice-only 行。

新增/未改动文件均未提交。原始模型证据和新的 annotated batch 均处于 ignored `work/local-followup/tmp/independent-acceptance/kev-20261009/`。
