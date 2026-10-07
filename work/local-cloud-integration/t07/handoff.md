# T07 售后数量、照片与精确工单证据交接

实现源：incoming `6734c7fe79e670df2dae12b065dcc49c0b10a307` 的售后/模拟状态相关 diff，选择性移植至 cloud baseline `37c98400e7152b89e4a58f02fff3bceaa73b0eac`。不改前端、Pi、政策来源、静态 seed 或原数据库。

## 公共合同与修复

- POST `/api/v1/orders/{order_id}/demo-state`：`expected_version` 与 `status`（shipped/delivered）；仅按 submitted→shipped→delivered 推进，owner/version、购物暂停栅栏保留，订单明细和金额不改。
- 售后 proposal 支持 quality/fulfillment，明确 item_id 与正整数 problem_quantity，不能超过订单销售包装件数；签收且不可无理由退货商品仍可登记问题。其他退款/退货合同保留。
- POST `/api/v1/mercury/sessions/{id}/photos`：content_type、data_base64、selection_version。JPEG/PNG/WebP MIME 与实际格式一致、4MiB 限额，Pillow 12.3.0 结构验证与解码并拒绝超过内置像素安全阈值的图片；提案最多 photo_ids 三项，每张校验 owner/case/order/selection。
- 只有显式 confirmed:true 才将 application/receipt/human-ticket 在同一业务事务提交；故障回滚全部三者和责任代次，确认幂等返回原回执。
- 工单 applications 以 application.human_ticket_id == ticket.ticket_id 明确关联，并校验 proposal.responsibility_generation == ticket.generation - 1。photos 只来自这些已确认回执中明确关联的 photo_ids；列表与 operator GET 共用 ticket_evidence，关闭后新代次、同单无关照片不能进入旧票。
- GET `/api/v1/mercury/operator/tickets/{ticket_id}/photos/{photo_id}` 仍需独立人工凭据；用户图片 GET 保持 owner/case 私有。
- 公开测试证明 open ticket 阻止新提案/越权确认；关闭后同订单第二商品新申请只进入新工单；旧 key 可读取原回执而不新建申请。

## Schema 与恢复

`aftersales_photos` 是新 additive 表，模型显式注册；标记 integration_aftersales_photos_v1。T04 预先协调的 GuideRunEvent.recorded_at_ms 是 nullable Float；ALTER 仅在缺列时，旧事件保持 NULL，标记 optimization_run_event_time_v1。T04 消费者尚未由本票实现。完整维护/只读/前向恢复说明见 `docs/recovery/ceres2-integration-aftersales.md`；不允许恢复旧备份丢失升级后的照片/回执。

## Tester 证据与限制

实现者没有执行安装、测试、lint、typecheck、build、服务或模型调用。独立 Tester 回报：

- 照片 RED：2 failures（HTTP404缺路由）；首个 GREEN 34 passed（证据+原售后/人工）。
- demo-state RED：1 failure（缺路由）；GREEN 10 passed（3当前新增+checkout）。
- migration RED：缺 recorded_at_ms；GREEN 5 passed（合成旧库与原迁移）。
- 扩展安全：首次17 passed/2 test fixture NameError（缺json import）；保留原失败记录，test-only修复后19 passed，包含数量澄清、数量/MIME/大小/计数、owner/case/order/selection、代次、回滚与重试。

上述是分片受控结果；合并最新集成 tip 后最终 aggregate 必须由 Tester 重跑。没有真实模型、真实数据库、BGE/GraphRAG 或浏览器验收，不能据此宣称完整产品验收。独立 Standards/Spec 审查由主会话安排。

## 串行下一步

T01 落地政策接口后，本 owner 在 Mercury tools/graph 单独接线：policy.CATEGORIES 十域，execute 传递真实共同 deadline 至 search_policies。现有 Mercury graph 无可传 should_stop 回调，不伪造新取消机制。该后续接线不由 T01 并行改同一文件。共享 migrations/model registry 交接给后续票需主会话确认；T04 事件消费者可依本票 nullable 字段实现。

## 两轴发现后的修复与当前核心门槛

最初以相同 responsibility generation 推断工单申请仍不精确：先确认普通 return，再在同代次对另一行 quality 或手动转人工，会混入先前无关申请。公开 RED 两例已由 Tester 复现，随后 `8666c70` 新增 nullable `aftersales_applications.human_ticket_id`，在实际确认/工单创建事务中赋值；查询要求该精确关联。旧申请 NULL 不猜回填，用户自己的售后历史保留，升级反复执行与外键约束覆盖。

另一个 Spec 发现是仅检查图片签名会接受头部垃圾/截断文件。Tester 生成并解码真实 1×1 PNG/JPEG/WebP 作为固定合成输入；6 个无效输入 RED、3 个真实格式正例通过。`0a6e8fa83d14165844e81f3d8e8d1a016c35ece2` 使用 Pillow 12.3.0 格式白名单、MIME 一致、结构 verify、重新打开 load 像素，并拒绝内置解压安全警告/异常。4MiB 输入上限保留。依赖由 Tester 锁定、在本票新环境安装，pip check 与 WebP codec 验证通过。

当前产品固定 pin `0a6e8fa83d14165844e81f3d8e8d1a016c35ece2`：

- 独立 Tester 受影响聚合 **75 passed / 24.65s**，源码与 harness 无漂移；原失败和首次 fixture 错误均保留。
- 覆盖八个测试文件：本票 evidence/migration，加原 aftersales、human、checkout、aftersales_migration、aftersales_proposal_migration、guide_migration。
- Standards 两次修复 delta 独立只读复审无未解决发现。Spec 最终 delta 由主会话登记。
- 这仅允许核心业务暂存合并；T07 的 Mercury policy categories/deadline 接线仍待 T01 正式集成并单独验证。不得据此解除 T05 对完整 T07 的依赖，或声称最终整合/浏览器/本人验收通过。
