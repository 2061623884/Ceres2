# Kev 隔离启动器公共 HTTP GREEN

日期：2026-10-09。只运行隔离启动器的单个公共 HTTP 行为测试；没有访问实际 Kev 8009、读取原 `.env`、调用生产模型或旧运行状态。

- 工作树 HEAD：`8c136eecf98cc4b37a2ffe7924c6f245a02315a1`。
- 命令（backend cwd）：`PATH=/data/amax/Documents/projects/Agent/Agent产品/Ceres2-integration-20261008/.venv/bin:/usr/bin:/bin python -m pytest tests/test_local_followup_kev_launcher.py -q`。
- 结果：exit 0，`1 passed in 2.85s`。
- 测试 SHA-256：`f676bb091aeb6f938ce359438a10199f261274ff89d0f765b70753130dab7fe6`。隔离启动器 [`serve_baseline.py`](./serve_baseline.py) SHA-256：`96ff1e8955d3a73b046a7983316acd97e3c2f3a829fb093f53a9e35fc66a351f`。
- 测试只读取自己创建的合成 source env，启动一次隔离子进程，并将其 Kev URL 覆盖到测试创建的 loopback fake server 随机端口；Ceres 测试 API 也绑定临时随机端口。fake Kev 收到 1 次 `service` 判断请求并返回受控 yes。未连接真实 8009。
- 验证通过：`/health` 与 bootstrap 使用 synthetic provider 配置；demo catalog 可读；继承的人工操作 token 无法访问 operator API；公共导航 route 返回 switch，并将请求原文交给 fake Kev。
- finally 中的清理断言全部执行并通过：隔离服务子进程收到 SIGINT 且退出；fake Kev server shutdown/close/thread join 完成；输出中不存在两种 synthetic API key；临时 sentinel 数据库和 checkpoint 字节未变化。
- 测试保留真实 HOME；子进程源配置与继承变量均为合成值。launcher 在服务环境加载时关闭工作树 dotenv 加载。本次启动的是随机 loopback 端口上的隔离 FastAPI 子进程（正常 lifespan）；未发 Guide 生成请求，主模型 URL 指向 synthetic 不可用端口，因此没有实际主模型调用。测试没有访问生产 Ceres API、真实 Kev 服务、旧 DB 或执行完整业务旅程。
