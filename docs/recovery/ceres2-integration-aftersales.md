# 售后照片与事件时刻增量恢复

适用：本轮 T07；来源售后实现 `6734c7fe79e670df2dae12b065dcc49c0b10a307`，基线 `37c98400e7152b89e4a58f02fff3bceaa73b0eac`。不迁入任何旧业务库、session、checkpoint、索引或凭据。

## 升级

现有初始化入口 `app.core.database.init_db` 在独立业务库事务内创建新 `aftersales_photos` 表，追加迁移标记 `integration_aftersales_photos_v1`。照片仅存 MIME、内容、owner/case/order 与选单版本；不改写现有申请/回执/订单 JSON。新增 nullable 外键 aftersales_applications.human_ticket_id 明确关联实际工单，确认时与工单/回执同事务提交；标记 integration_ticket_application_link_v1。旧申请保持 NULL，不根据订单或责任代次猜测回填，仍保留在用户售后历史。人工照片仅来自该票关联申请的已确认回执 photo_ids，并额外校验作用域与责任代次。

T04 所需 `guide_run_events.recorded_at_ms` 为 nullable FLOAT；旧事件保持 NULL，新增字段标记 `optimization_run_event_time_v1`。消费者由 T04 单独接入；本迁移不生成时间戳。重复初始化不重复标记或重写历史。

测试/本轮演示只创建临时模拟库。未来若维护已运行实例，先停止全部业务写入者和服务，通过 SQLite backup API 创建一致备份并验证备份可读，再由专职 Tester/授权维护流程执行初始化与验收。不要直接复制仍处于 WAL 写入状态的单个数据库文件。

## 回滚和恢复

- 若升级后尚无新写入：保持服务停止，可回到旧程序与升级前一致备份；先确认确实没有需要保留的新申请、照片或订单状态。
- 若已有任何新写入：不能用旧备份覆盖当前库，也不删除照片表、回执或新增列。停止写入并保存当前完整一致备份；只读查看保留的订单/申请/照片，修复后以前向升级恢复。
- 旧程序可能无法理解 quality/fulfillment 回执，不能仅因 schema 是 additive 就宣称旧程序可安全继续写入。人工确认恢复策略前保持维护只读。
- checkpoint 丢失不构成重新提交依据：以持久 proposal/application/receipt 为权威，已有确认 key 重放返回原回执。图片是人工参考，申请不表示审批、退款到账或真实履约。

可重复证据入口：`backend/tests/test_merge_business_migration.py`（合成旧 schema、两次初始化、旧 JSON/金额保留、未知时间为 NULL）以及 `test_merge_aftersales_evidence_public.py`（公开 HTTP 权限与确认/重放）。实际执行与验收记录由 Tester 独立提供。
