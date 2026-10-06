# Ceres2 集成使用一个购物业务事实与事务边界

状态：部分保留／集成方式待复核（2026-10-05 11:27:40）。单一业务事实权威、可信 owner 和业务副作用/回执原子性原则保留；下述具体 Ceres 数据库复用方式随 Pi Agent runtime + LangGraph 服务契约审查复核，不以此冻结语言、sidecar 或存储适配。原决定正文保留作为历史取舍记录。

Ceres 模拟结算、购物车扣减、Mercury 订单/申请及业务回执共享 Ceres canonical owner 和同一业务数据库权威；Mercury 保留独立模块与确定性售后规则，checkpoint 只保存流程进度。拒绝把前端订单和 Mercury 演示订单做运行时双写：两个普通 SQLite commit 无法保证结算原子性或售后提交与回执一致，而本轮没有采用 outbox/分布式同步的业务必要。

原 Mercury 库仅作隔离演示或有明确 owner mapping 的迁移来源，不能未知用户回退到 demo owner。代价是调整 Mercury 的存储接缝及事务组合；收益是订单和申请只有一个可信结果，graph/checkpoint 故障后可以按 receipt 恢复。启用新确认后，代码回退不能恢复旧未授权写入口，必要时保留只读/hold。

## 集成落实：case 与人工责任同库（2026-10-05 15:21 UTC）

依照已批准规格的单一事务边界，P13 将 owner、order、选单版本、处理责任及 responsibility_generation 等 case 权威状态落实到 Ceres canonical SQLAlchemy 业务库。P15 人工工单责任 CAS 与后续 P14 售后提交必须在同一业务事务中验证该 generation；若把人工责任只留在 Mercury 的第二个 SQLite 库，则检查与业务提交之间无法原子阻止在途 Agent 写入。此为既有授权／事务要求的最小工程落实，不新增产品能力或分布式协调框架。

Mercury SQLite 继续保存 LangGraph checkpoint／流程引用，不作为订单、case 责任或业务授权权威。已有 query_cases 历史保留；只有明确可信 owner／order 映射的离线迁移可以导入 canonical case，不猜测用户或订单、不运行时双写。新增表采用现有 create_all 增量登记，身份／责任／版本的实际服务契约由 P13 唯一维护，P15 在该契约就绪后接入，不必等待整票验收。
