# Harness 修复后的四模块组合回归

本轮在同一当前源码上依序运行 baseline、evaluation、controlled app 与 real-harness 四个测试模块。Git HEAD：`fbb44854a412da8d77a7ec30426d240756a9d261`。

工作目录为 `backend/`，实际命令：

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py tests/test_local_followup_evaluation.py tests/test_local_followup_app.py tests/test_local_followup_real_harness.py
```

退出码 0：`35 passed, 1 warning in 13.98s`。唯一 warning 是禁用 pytest 插件自动加载后 pytest 报 `asyncio_mode` 配置项未知。未覆盖 `HOME`；测试使用 loopback/controlled fixtures 与 synthetic 配置，没有读取原 `.env`、ignored 真实输出、私有验收题或真实 batch，也没有调用真实模型/provider/正式服务。

本轮 runner、baseline/evaluation/app/real-harness 测试以及六个 harness 脚本的源码 SHA-256 见 [REAL-HARNESS-SOURCE-HASHES.sha256](../04/real-model-20261008/REAL-HARNESS-SOURCE-HASHES.sha256)。

完整 stdout/stderr 位于 ignored 文件 `work/local-followup/05/tmp/tool-combined-after-real-harness-fix.log`，SHA-256 `693c3574c047bf24406308f966d129126363d9536674514f8150e627d314978a`。本报告是窄工具回归证据，不替代此前真实 100-run 报告，也未重跑产品全量套件。
