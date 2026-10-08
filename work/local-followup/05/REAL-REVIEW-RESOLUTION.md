# 真实执行交付审查修复

初始真实报告候选`fbb44854a412da8d77a7ec30426d240756a9d261`；实际100执行HEAD为`00b397443bd7258d2166c6445ac4ac066cefd21d`、工具/产品源码739。本文记录修复依据，不代签独立复审或本人验收。

| 来源 | 发现与处理 | 证据 |
| --- | --- | --- |
| Spec、真实公开dev-01 trial3 | 缺plan确认意外TypeError；新增明确ValueError诊断，仍用原runner_failed envelope，保留已有capture/steps/state、不发确认HTTP；普通无plan问答正常 | runner-missing-plan-red/green.md；三模块30项 |
| Standards | 未观测Graph calls/facts/usage/time被当0/空集合；现失败audit为not_evaluated且指标null，成功按必需字段访问；合法已观测空集/0保留原值 | real-harness-contract-red/green.md |
| Standards | serve合并环境保留未授权Settings；共享窄helper清除当前Settings别名后施加选定值，保留原HOME和明确TLS/proxy配置 | 同上；两个serve入口共用helper |
| 主会话复核 | Settings环境变量大小写不敏感，须一并移除小写/混合别名；新增实际RED，再casefold清理，移除没有当前生产调用的可选mapping参数 | real-harness-casefold-red/green.md |
| Standards判断性重复 | 三个dotenv来源/字段声明重复；收敛至harness_config，供preflight/provider/Dream实际调用 | 仅窄配置reader/环境应用，不搭配置平台 |

最终受控fixture验证为四模块35 passed/14.03s，1条禁用pytest插件后asyncio_mode警告，见[最终回归](../01/tool-combined-after-real-harness-casefold-fix.md)。最新11项修复源码清单为[REAL-HARNESS-CASEFOLD-SOURCE-HASHES.sha256](../04/real-model-20261008/REAL-HARNESS-CASEFOLD-SOURCE-HASHES.sha256)。此前30项、首次35项与中间RED保留各自版本，数目不加总。

实际100轨迹/判分/模型输入与原41项SOURCE-HASHES未修改，没有新真实模型/browser/service调用。实测66/30/4和TypeError原记录仍适用于旧执行版本；后续driver诊断修复不算原模型任务变成功。新harness修复是受控合同回归，尚未重新真实采样，不能把旧41清单当新代码清单。
