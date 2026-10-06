# 干净重建记录

授权时间：2026-10-05 15:42 UTC。初始脚手架已提交为 49ce5111bcf296a567e8fbfad2422621ffe334db；现已进入 01／02／12 选择性实现及专职 Tester 验证。无推送。

## 路径映射

- 原 `/workspace/scratch/0c1b4cfa2ef3/Ceres2` → [完整只读归档](../../../archive/ceres2-before-clean-20261005/)；同文件系统 rename，完整 Git、dirty 源码、ignored 依赖及证据保留。
- [原始 Ceres](../../../reference/Ceres/)：提交 `e24debf670db02a86cb79c40933b901827db8a55` 的 git archive 源码；凭据/cookie/运行状态路径不提取，详见 [来源记录](../../../reference/CERES-ORIGIN.md)。
- [外部参考索引](../../../reference/README.md) 与 vendor：复制原参考目录，保留 Git、许可证和固定 SHA；不安装依赖、不作为应用依赖。完整原参考仍在归档。
- 当前工程：[Ceres2](../..)。全新 Git，无 remote；只复制 frontend 源码/assets/config/tests 与批准规划文件。

## 选择性迁移与来源

[逐文件 allowlist／来源 SHA256](provenance.json)；[重建基线文件 hash](baseline-files.json)；[归档验证](../../../migration-records/rename-verification.json)；[归档前源码 hash](../../../migration-records/before-source-sha256.json)；[归档前 Git 状态](../../../migration-records/before-status.txt)。不含凭据内容。旧源码后续迁入必须逐票记录 origin/hash/reason；不能整包引入旧业务模块。

## 新工程验收

01／02／12 进行中；整票技术 0／16、用户本人 0／16。前端复制只表示 UI 文件连续性，不表示新后端集成通过。Tester 在新工程隔离数据上重新执行公共接缝红绿、两次独立行为验证与回归；真实 SDK/框架、真实 provider、真实页面及本人验收分别记录。旧 02／12 通过与旧失败均只作历史参考。依赖 DAG 未变。

## 静态数据集成

65 个静态商品与 65 个模拟 Offer 已选择性复制至 data/fixtures，显式幂等 seed 只插入缺失记录。33 个商品原图已恢复为与旧 LFS OID 一致的本地 JPEG。其余菜谱按后续切片导入。未复制任何旧数据库、索引、session、cart、order 或 checkpoint。详情见 [迁移账本](migration-ledger.md)。
