# Casefold 修复后的四模块组合回归

同一冻结源码下执行 baseline、evaluation、controlled app 和 real-harness 四个工具测试模块。Git HEAD：`fbb44854a412da8d77a7ec30426d240756a9d261`。

工作目录为 `backend/`，命令：

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py tests/test_local_followup_evaluation.py tests/test_local_followup_app.py tests/test_local_followup_real_harness.py
```

退出码 0：`35 passed, 1 warning in 14.03s`。唯一 warning 是禁用 pytest 插件自动加载后 `asyncio_mode` 配置项未知。未覆盖 `HOME`；测试使用 loopback/controlled fixtures 和 synthetic env，没有读取原 `.env`、ignored 真实输出、私有验收题或真实 batch，也没有调用真实模型/provider/正式服务。

本轮逐文件源码哈希见 [REAL-HARNESS-CASEFOLD-SOURCE-HASHES.sha256](../04/real-model-20261008/REAL-HARNESS-CASEFOLD-SOURCE-HASHES.sha256)。完整 stdout/stderr 在 ignored `work/local-followup/05/tmp/tool-combined-after-real-harness-casefold-fix.log`，SHA-256 `48edf14797ee4edc7717d970245ea0c38a90c349e487ec6bdde40bdce87c4e44`。旧 `REAL-HARNESS-SOURCE-HASHES.sha256` 与既有 35-pass 报告未覆盖。
