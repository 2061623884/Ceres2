# Runner 缺失 plan 修复后的工具组合回归

执行范围为 baseline、evaluation、受控 app 三个工具测试模块；没有运行产品全量测试，也没有读取私有 20 题或 ignored 真实批次。

- Git HEAD：`fbb44854a412da8d77a7ec30426d240756a9d261`
- `backend/app/evaluation/run_baseline.py` SHA-256：`0e0aa5e24708d53ce0e1354fb48c6e0f3776e3462b294120e6a0709677da8530`
- `backend/tests/test_local_followup_baseline.py` SHA-256：`b2ba745e60ada8afacba4f7727f571c3a4e9ab2c52e000fa889daf029d26285a`
- `backend/tests/test_local_followup_evaluation.py` SHA-256：`4f218062ff96fcd87c01da59d61bd83b2a9c9dd3aadeda5a20fdbffb6208dbe7`
- `backend/tests/test_local_followup_app.py` SHA-256：`cc5b310f81252772aaf19396b007043e6ad942ad97932ae545c019af68b5ccd8`

工作目录为 `backend/`，实际命令：

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py tests/test_local_followup_evaluation.py tests/test_local_followup_app.py
```

退出码 0，`30 passed, 1 warning in 13.76s`。唯一 warning 是禁用 pytest 插件自动加载后配置项 `asyncio_mode` 未知。执行期间未覆盖 `HOME`；测试只使用各自 loopback/controlled fixture，没有真实模型、provider 或正式服务调用。

完整 stdout/stderr：`work/local-followup/05/tmp/tool-combined-after-real-runner-fix.log`，SHA-256 `898e94e16d2d6d1c3134a1aaaf8140c0cb495714fa0bd64e9fccee7fd328f310`。日志位于 `.gitignore` 匹配的 `work/**/tmp/` 下。
