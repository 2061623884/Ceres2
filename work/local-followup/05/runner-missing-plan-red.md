# Baseline runner 缺失 plan RED 记录

本记录只覆盖一个公开 loopback CLI 用例；没有访问真实服务、provider、模型、正式 batch 或 ignored/private acceptance 数据。当前 Git HEAD 为 `fbb44854a412da8d77a7ec30426d240756a9d261`。

## 执行

工作目录：`backend/`

命令：

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py::test_baseline_cli_records_missing_plan_before_confirm_without_http_side_effects
```

进程退出码为 1，结果 `1 failed, 1 warning in 1.13s`。测试使用自身拥有的 `ThreadingHTTPServer`，监听 `127.0.0.1` 临时端口；用例 `finally` 调用了 `shutdown()`、`server_close()` 和 `thread.join(timeout=2)`。pytest 的单条 warning 是禁用插件自动加载后出现的 `Unknown config option: asyncio_mode`，与断言失败无关。

测试源码 SHA-256：`b2ba745e60ada8afacba4f7727f571c3a4e9ab2c52e000fa889daf029d26285a`。执行时 `backend/app/evaluation/run_baseline.py` SHA-256：`cdda0026e00531cff82cfb1fdd0559d067d1184610055d207fadf46cf7e52b29`。

## RED 根因

合成输入声明一个 `confirm_plan` 步骤，测试期望第一轮请求后若 plan 缺失就记录明确的 runner failure。该用例已断言行结果为 `runner_failed`；接下来的首个断言要求错误类型和原因如下：

```text
assert failed['error'] == {
    'type': 'ValueError',
    'reason': 'confirm_plan requires a current plan',
}

actual: {'type': 'TypeError', 'reason': "'NoneType' object is not subscriptable"}
```

因此 runner 在缺失 plan 时对 `None` 解引用，没有生成契约要求的明确错误。测试随后还会验证 before/after cart 与 orders 不变、没有 confirm POST 或 cart POST；本次执行在错误信封断言处先失败，这些后续断言没有执行，不能将它们报告为本次通过。
