# Real harness 最终必填参数签名 GREEN

在两处 required-source 签名均冻结后，只运行 `test_local_followup_real_harness.py` 五例；本轮没有执行四模块组合或任何额外测试。Git HEAD：`4008faacae169d18de80f6a444f59c47a93915b7`。

工作目录为 `backend/`，命令：

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_real_harness.py
```

退出码 0：`5 passed, 1 warning in 0.48s`。warning 是禁用 pytest 插件自动加载后 `asyncio_mode` 配置项未知。测试使用 synthetic env/fixtures，不读取原 `.env`、ignored 真实运行数据、私有验收集或真实 batch，也没有调用模型、provider 或 server；HOME 未覆盖。

最终必填签名为 `read_source_values(source: Path | str)` 与 `audit_graph_result(result, dishes, ingredient_records, manifest_sha256)`；两个参数均无默认值。源码 SHA-256 分别为 `harness_config.py` `9a5caa0ba6adbe62aa04b36b14eee5db09a678cb4074d9bc0e192704b21139c3` 与 `graph_audit.py` `ee86e9bc6e7d86ffaa8b373fc2ad7432ca32edbca1af0cbb112ac5d7e727edf3`。测试源码 `backend/tests/test_local_followup_real_harness.py` SHA-256 为 `123b494e18903d034e47c6a6ae2fe34d094aeb13e614c968fda43d6f28f73d2c`。

适用测试及 harness 源文件的完整 11 项哈希清单见 [REAL-HARNESS-FINAL-SOURCE-HASHES.sha256](../04/real-model-20261008/REAL-HARNESS-FINAL-SOURCE-HASHES.sha256)。旧 source manifests、casefold 证据和四模块 35-pass 报告均保留未覆盖。

完整 stdout/stderr 位于 ignored `work/local-followup/05/tmp/real-harness-final-signature-cleanup-green.log`，SHA-256 `4550be894c6d17f953753f8b224cd3924690682a562a44389e608287e1b47f3a`。该结果来自 helper 签名与 graph audit 签名都移除默认值后的最终快照；此前 graph audit 修改前的 5-pass 结果仅为中间证据。
