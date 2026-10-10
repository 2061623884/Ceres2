# Kev 隔离启动器首个 RED

日期：2026-10-09。只执行新加入的隔离启动器公共 HTTP 测试；没有访问实际 Kev 8009、读取 `.env`、调用生产模型或启动主 Ceres 服务。

- 工作树 HEAD：`8c136eecf98cc4b37a2ffe7924c6f245a02315a1`。
- 测试：`backend/tests/test_local_followup_kev_launcher.py`，执行前 SHA-256 `5396c33ab1e375e9e397855867d38c1c92d0022355f4180efc2c482522c7066f`。
- 命令（backend cwd）：`env -i HOME=/home/amax PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_kev_launcher.py`。
- 结果：exit 1，`1 failed`。唯一首因是隔离子进程在公共 HTTP readiness 前退出：`ModuleNotFoundError: No module named 'serve_baseline'`；被测试导入的 `work/local-followup/04/kev-followup-20261009/serve_baseline.py` 当时不存在。这是预期 RED。
- 测试中的 fake Kev server 绑定自身分配的 loopback 随机端口；测试未触碰 8009。其 `finally` 调用了 `client.close()`、`kev_server.shutdown()`、`server_close()` 和线程 `join(timeout=5)`。子进程已在 readiness 阶段退出，未发送信号或 kill。
- `pytest.fail` 从 readiness 循环传播，因此 `finally` 之后的 `thread.is_alive()` 与 synthetic DB/checkpoint 哨兵相等断言没有执行；本记录不把这些断言称为通过。RED 堆栈确认子进程已退出，未留下由该测试继续运行的 API 服务。
- 本次没有修改源码、测试或配置；未读取真实 `.env`，没有读取私有评测集或旧运行状态。
