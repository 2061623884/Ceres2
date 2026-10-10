# Real-execution Standards review

Fixed point `00b397443bd7258d2166c6445ac4ac066cefd21d`; reviewed candidate `fbb44854a412da8d77a7ec30426d240756a9d261` (single commit: “Record real-model evaluation, GraphRAG, memory and browser evidence”). I reviewed that commit’s 26-file delta and checked overall scope from `170fac0bc75fcc855897b073337ba218abeb5b7d`. Product and evaluation implementation files are unchanged in the new delta. This was read-only; I did not read `.env`, ignored/raw/private evaluation data, or runtime state, and ran no tests, scoring, model calls, installs, builds, or servers.

## Hard standards violations

- **Missing evidence is converted to zero/empty.** `provider_job.py:74–84` turns `calls=None` into zero calls and missing provider `total_tokens` into zero. The existing producer permits `usage=None` (`backend/app/knowledge/providers.py:_record`) and the graph supervisor explicitly returns `calls=None` on unobserved failures (`backend/app/knowledge/cli.py:42–47`). `graph_audit.py:12–15, 23, 38–40` similarly defaults absent graph facts to empty collections and absent duration to `0`; failure results can omit those fields. This conflicts with `AGENTS.md`’s “新增逻辑的依据” rule against unsupported defaults and the plan’s explicit rules that graph failure is not empty evidence and missing time/usage stays unknown ([spec](../../docs/plans/ceres2-local-followup-spec.md#3-检索菜谱与显式-graphrag), [reporting rules](../../docs/plans/ceres2-local-followup-spec.md#4-评测与反馈闭环)). Preserve unknown/unobserved states through these summaries.
- **The allowlisted server environment is not enforced.** `_configure()` constructs a narrow `env`, but `provider_job.py:192` and `serve_browser_smoke_api.py:21` merge it into the existing process environment. Disabling dotenv does not remove inherited settings; `Settings` also consumes values such as `HUMAN_OPERATOR_TOKEN` (`backend/app/core/config.py`). Thus server settings are not guaranteed to come only from the fields authorized in `AGENTS.md`’s current local-stage rule. No environment values were inspected.

## Judgemental smells

- **Duplicated Code (minor).** The dotenv source path and overlapping allowlisted field declarations recur in `config_preflight.py:15–20, 39`, `provider_job.py:15–25`, and `memory_dream_smoke.py:14–29`. Each command needs a different required subset, so this is not a hard violation; a shared allowlist/source reader could reduce drift if these harnesses remain in use.
- The earlier runner/scorer **Repeated Switches** trade-off is unchanged; see [the prior review](STANDARDS-FINAL-REVIEW.md).

The dedicated Tester’s curated component/task reports were reviewed as documentation only. This Standards review does not certify their execution or establish overall acceptance.
