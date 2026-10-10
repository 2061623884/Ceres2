# Real harness casefold GREEN

针对 [casefold RED](real-harness-casefold-red.md) 的 helper 修复，执行了同一 synthetic Settings 用例。Git HEAD：`fbb44854a412da8d77a7ec30426d240756a9d261`。

工作目录为 `backend/`，命令：

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_real_harness.py::test_provider_serve_drops_inherited_operator_settings_before_settings_load
```

退出码 0，`1 passed, 1 warning in 0.26s`。warning 是禁用插件自动加载后 pytest 提示 `asyncio_mode` 未知。测试使用 synthetic env/host values，并在 finally 恢复环境；没有读取原 `.env`、ignored 真实运行数据或私有验收集，也没有真实模型/provider/server调用。

关键源码 SHA-256：`harness_config.py` `769d64ff43b83eef546fe3fbf1c8de3a920f065b63e36ec93718528b728b18d0`；`test_local_followup_real_harness.py` `123b494e18903d034e47c6a6ae2fe34d094aeb13e614c968fda43d6f28f73d2c`。四个相关测试与本次 harness 源码逐文件哈希见新增清单 [REAL-HARNESS-CASEFOLD-SOURCE-HASHES.sha256](../04/real-model-20261008/REAL-HARNESS-CASEFOLD-SOURCE-HASHES.sha256)，未覆盖历史 source manifest。

完整 stdout/stderr 在 ignored `work/local-followup/05/tmp/real-harness-casefold-green.log`，SHA-256 `a6c925ad83145dff9921d8429da8be41d2f23f1324c8dd06d8aefa947e728fc2`。
