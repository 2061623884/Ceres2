# Real harness contract GREEN

针对 [RED 记录](real-harness-contract-red.md) 的 harness 修复，执行了唯一新增 synthetic 测试模块。HEAD 为 `fbb44854a412da8d77a7ec30426d240756a9d261`。

工作目录为 `backend/`，命令：

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_real_harness.py
```

退出码 0：`5 passed, 1 warning in 0.47s`。warning 是禁用插件自动加载后 pytest 提示 `asyncio_mode` 未知。测试只使用 synthetic env/JSON、临时目录和本地审计脚本副本；没有读取原 `.env`、ignored 运行输出、私有验收集或真实 batch，也没有调用模型、provider、真实服务或 HTTP。

测试源码 `backend/tests/test_local_followup_real_harness.py` SHA-256：`e68821eab29d685e70f55b690b434e206218a3876a53ebc33b7b457cd35c42a3`。baseline runner、四个相关测试文件与六个 harness 脚本的逐文件 SHA-256 见新增清单 [REAL-HARNESS-SOURCE-HASHES.sha256](../04/real-model-20261008/REAL-HARNESS-SOURCE-HASHES.sha256)，没有覆盖历史 `SOURCE-HASHES.sha256`。

原始输出为 `work/local-followup/05/tmp/real-harness-contract-green.log`，SHA-256 `db4621c6e5e1544d01798a17fed7f6985b35746295a1c7648bad916bfe0a0623`；该路径由 `.gitignore` 忽略。
