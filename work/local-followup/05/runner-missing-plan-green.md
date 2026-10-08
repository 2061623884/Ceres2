# Baseline runner 缺失 plan GREEN 记录

针对 [RED 记录](runner-missing-plan-red.md) 的最小 runner 修复，执行了指定 loopback CLI 用例。未更改测试或实现。

- Git HEAD：`fbb44854a412da8d77a7ec30426d240756a9d261`
- runner `backend/app/evaluation/run_baseline.py` SHA-256：`0e0aa5e24708d53ce0e1354fb48c6e0f3776e3462b294120e6a0709677da8530`
- 测试 `backend/tests/test_local_followup_baseline.py` SHA-256：`b2ba745e60ada8afacba4f7727f571c3a4e9ab2c52e000fa889daf029d26285a`

工作目录为 `backend/`，实际命令：

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py::test_baseline_cli_records_missing_plan_before_confirm_without_http_side_effects
```

退出码 0，`1 passed, 1 warning in 0.97s`。warning 是禁用插件自动加载时 pytest 提示配置项 `asyncio_mode` 未知。测试的 loopback fixture 按其 `finally` 清理。

完整 stdout/stderr：`work/local-followup/05/tmp/runner-missing-plan-green.log`，SHA-256 `e77f62cea774395fc269262a4395d87d8ce2bdd71b1ad5fc978078c1f61a5700`。该日志位于 `.gitignore` 匹配的 `work/**/tmp/` 下。没有读取私有验收数据，也没有真实 provider、模型或服务调用。
