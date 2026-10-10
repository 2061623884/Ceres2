# Scorer 首纵切测试版本说明

首轮 RED 测试文件 SHA-256 为 `0ee7bb76b14be900a0ed7cd04544cd611a9feaab5f99ca5f13f1652175cf710f`，失败为缺少 `app.evaluation.score_batch`。
随后主会话发布明确的 plan/trial/execution_id 合同，实施者在夹具加入两个计划行及对应 execution_id 断言；GREEN 测试文件 SHA-256 为 `18e2577d975e37c49bb865f5fb2a1367bb8106d1c7e95e3ccd47794e873228a9`。

因此 [RED](score-batch-red.md) 与 [GREEN](score-batch-green.md) 不是同一冻结测试源码，不能写为同版红绿。它们分别保留原版本和实际结果；不回退实现或制造事后 RED。
错误 Offer 价、预算未知及计划分母的实际 GREEN 结论适用于后一个夹具。新增的空证据/等待/缺行合同用另一个公共 CLI 测试先记录当前实现失败，再修复并复验。
