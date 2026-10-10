# Kev 启动器 Memory 配置增量 GREEN

日期：2026-10-09。launcher 对 Memory 必填配置增加读取/检查后，仅重跑其隔离公共 HTTP 行为测试；保留原 [首个 GREEN](./LAUNCHER-GREEN.md) 作为前一 launcher 版本证据。

- 工作树 HEAD：`8c136eecf98cc4b37a2ffe7924c6f245a02315a1`。
- 命令（backend cwd）：`PATH=/data/amax/Documents/projects/Agent/Agent产品/Ceres2-integration-20261008/.venv/bin:/usr/bin:/bin python -m pytest tests/test_local_followup_kev_launcher.py -q`。
- 结果：exit 0，`1 passed in 3.43s`。
- 测试 SHA-256：`f676bb091aeb6f938ce359438a10199f261274ff89d0f765b70753130dab7fe6`；当前 launcher SHA-256：`af65cd78c7045da48d186fdedf27e9306b1a41194e71b9e351a7d6a89f7dc3d8`。
- 测试仅创建合成 source env、随机 loopback API 端口、随机 loopback fake Kev 端口与临时 runtime。fake Kev 收到 1 次受控 `service` 请求；全部服务/配置值为 synthetic。测试清理断言通过：隔离子进程退出、fake server 线程结束、synthetic keys 未输出、sentinel DB/checkpoint 未变化。
- 本次没有读取原 `.env`，没有访问实际 Kev 8009、私有评测集或旧运行状态，也没有调用主模型。
