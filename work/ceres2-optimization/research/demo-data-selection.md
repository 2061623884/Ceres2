# Ceres2 demo 菜谱与 SKU 选择审计

## 建议结论

保留 Ceres2 当前 `data/fixtures/recipes.json` 的 2 道菜，再从只读参考源 `chinese-dishes-v1.json`（`version: v1`，105 道菜）增加以下 6 道，组成 8 道的演示子集。原菜谱 `base_people` 均为 2。选择覆盖鸡蛋、蔬菜、猪/鸡肉、米饭，并刻意重复猪肉、青椒、鸡蛋和米饭关系；不把 105 道全部灌入演示数据。

| 原始 `dish_id` / 菜名 | 必需食材（原始数量/单位） | Ceres2 当前同单位 SKU 覆盖 | 选择价值 / 约束 |
|---|---|---|---|
| `dish-qingjiao-rousi` 青椒肉丝（别名：尖椒肉丝） | `pork` 200g；`bell_pepper` 200g | `demo:pork-500g`（500g）；`demo:bell-pepper-300g`（300g） | 与回锅肉共享猪肉、青椒；支持组合采购和多菜去重。 |
| `dish-gongbao-jiding` 宫保鸡丁 | `chicken_breast` 250g；`peanut` 50g；`bell_pepper` 100g | `demo:chicken-breast-500g`（500g）；`demo:peanut-200g`（200g）；`demo:bell-pepper-300g`（300g） | 将 `peanut` 设为明确排除项时，验证硬约束冲突；不得静默删掉菜谱花生或换一道相似菜。此用例不代表过敏原判定或安全保证。 |
| `dish-huiguo-rou` 回锅肉 | `pork` 300g；`bell_pepper` 100g；`cabbage` 100g | `demo:pork-500g`；`demo:bell-pepper-300g`；`demo:cabbage-500g`（500g） | 与青椒肉丝共享猪肉、青椒，补充卷心菜关系。 |
| `dish-jiajiao-chaodan` 尖椒炒蛋 | `bell_pepper` 200g；`egg` 3pc | `demo:bell-pepper-300g`；`demo:eggs-fresh-6pack`（6pc）或 `demo:eggs-10pack`（10pc） | 与现有番茄炒蛋、蛋炒饭共享鸡蛋，也与肉菜共享青椒。 |
| `dish-suanla-tudousi` 酸辣土豆丝（别名：醋溜土豆丝） | `potato` 350g | `demo:potato-500g`（500g） | 增加单主料蔬菜和别名检索样本。此菜 `required_items` 只有土豆；`pantry_items` 列有 `chili_sauce`，没有花生。 |
| `dish-yangzhou-chao-fan` 扬州炒饭（别名：什锦炒饭） | `rice` 350g；`egg` 2pc；`shrimp` 80g；`green_pea` 50g | 大米 `demo:rice-2kg`（2000g）；鸡蛋 6/10pc；青豌豆 `demo:green-pea-300g`（300g）；`shrimp` 无 SKU | 与现有蛋炒饭共享米、蛋，同时加入一个真实缺项。只需新增一个 `source=demo`、`ingredient_ids=["shrimp"]`、规格单位 `g` 的虾仁 SKU（例如 300g 演示装）；不要把青豌豆重复造数。 |

原始菜谱的行号分别为：扬州炒饭 55–83、青椒肉丝 86–107、宫保鸡丁 138–162、酸辣土豆丝 293–310、回锅肉 621–644、尖椒炒蛋 969–987。当前两道保留菜及分量见 Ceres2 `recipes.json` 10–52 行：番茄炒蛋、蛋炒饭，均为 `base_people=2`。因此这组新增 6 道的 15 个必需食材出现项中，14 项已有相同计量单位的 SKU 关系；按去重食材 ID 计为 9/10，唯一缺 `shrimp`。这是静态关系覆盖计数，不是可履约、库存、营养或口味验证。

## 数据质量边界

- 当前 `products.json`（Ceres2 基线 `b118dbe`，fixture `version: v1`，70 SKU）中的大米、猪肉、鸡胸肉、花生、卷心菜、青椒、鸡蛋、青豌豆和鲜土豆均有同单位映射，均标记 `source=demo`、`review_status=approved`。对应 SKU ID 见上表；主要行号：米 372–386、蛋 348–365、青椒 231–244、鸡胸 288–300、花生 496–506、猪肉 211–220、卷心菜 681–694、鲜土豆 701–714、青豌豆 1031–1044。
- 当前 `potato` 关系还命中两袋薯片：`demo:snack-original-potato-chips-70g-bag` 与 `demo:snack-original-potato-chips-35g-bag`（分别在 1554–1578、1679–1703 行标为 `product_type=potato_chips`、商品名“薯片”）。它们不能作为菜谱鲜土豆的 SKU 候选；这只是现有 `ingredient_ids` 的宽泛关联，不足以证明食材可替代。选菜/导入时应将原料土豆候选限定到鲜土豆 SKU，或先修订这两条 demo 映射。
- 当前蛋炒饭只要求米和蛋；新增扬州炒饭才要求虾仁、青豌豆。所有数量来自原始 demo 菜谱，不能据此推断营养、过敏、交叉污染、健康或真实商品规格。

## 可迁移的检索组织方式

1. **确定命中优先，再做混合召回。** 参考实现先匹配稳定 ID、规范菜名和注册别名，冲突时明确返回，不把用户点名内容交给相似度“纠正”；其它查询再并行走 sparse/dense 并按 RRF 合并。见参考 `retrieval_service.py` 516–560、613–632、569–609、798–813。CJK sparse 可借鉴冻结词典最长匹配、未登记连续文本的二元切分及 FTS5 BM25；源实现的 tokenize/query 逻辑见 `retrieval_projection.py` 149–277、301–317，BM25 查询见 `retrieval_index.py` 592–637。dense 分支必须使用真实 embedding；不能用假向量或只把稠密路线当接口占位。
2. **候选与业务实体分开。** 参考 projection 把菜和 SKU 建成不同 kind，带稳定 `doc_id`、`target_id`、静态 payload/hash（`retrieval_projection.py` 56–79、354–403、427–471）。可借鉴“检索只给候选 ref；命中后由 Python 业务层按稳定 ID 重读菜谱/商品，并再次核对当前可建计划和商品事实”的边界：`retrieval_service.py` 884–905、907–990。回答或写购物车时，数据库/业务行仍是事实来源，不能把索引片段当当前状态。
3. **让索引版本可复现。** 参考 manifest 记录索引 schema、语料 snapshot/content hashes、词典与文本模板版本、每文档 hash，以及完整 embedding contract；契约至少包含模型、revision、维度、dtype、归一化、query/document instruction 和 text-template 版本。见 `retrieval_index.py` 37–53、133–179。Ceres2 可把 embedding/model metadata 放在索引 manifest，不必为了研究结论增加行级字段。
4. **仅迁移结构，不迁移未校准旋钮和旧向量。** 参考 `retrieval_service.py` 78–82 明确 cosine 0.35 未由真实向量和标注集校准；同文件 67–74 的 route top-N/fuzzy 常数也只是原实现参数。一个历史 manifest（`../reference/origins/Ceres/data/retrieval_index-langgraph/idx-de582fe93b19659a/manifest.json`，manifest id `sha256:bf2c5eae881e32f77301a778275cfe1a4ffe0ec0833d9ddb71862ecaf9bc0c99`）报告 101 菜、307 SKU、408 个向量，模型标识为 `Qwen/Qwen3-Embedding-0.6B`、1024 维，但 embedding revision 为空且 audit-only 记录 handoff projection hash 不匹配。源码注释与历史索引产物的来源并不构成可复现实测，所以不能把该索引当本轮 8 道菜/70 SKU 的质量或性能证据。保留 exact/alias、稀疏和稠密两路、RRF、来源 refs、manifest 版本这些组织思想；参数与向量需由 Ceres2 当前语料和评测集重新定，当前无性能结论。

## 版本与核查范围

- 选菜源：参考快照 `../reference/origins/Ceres/data/fixtures/chinese-dishes-v1.json`，声明 `version: v1`、105 道菜；未将旧数据导入 Ceres2。
- 目标现状：`/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007` 基线 `b118dbe`；菜谱及商品 fixture 均声明 `version: v1`，当前分别 2 道菜、70 SKU。
- 参考检索源码路径均在 `../reference/origins/Ceres/backend/app/services/`：`retrieval_projection.py` 的 projection schema `1`、文本模板 `v1`、词典 tokenizer `zh-dict-v1`（30–45 行）；`retrieval_index.py` 的 index schema `3`（37–53 行）；`retrieval_service.py` 的版本由该源码树的接口与代码行引用限定。参考目录无 Git 元数据，因此不把这些代码标记冒充为 Git commit。历史 manifest 只用于说明它自己的 schema/embedding contract 和 provenance 限制。
- 本轮只读浏览指定静态源、当前 fixtures 和参考检索文件；未运行测试、安装、构建、embedding、索引重建或性能测量。上述覆盖计数是由 fixture 字段核对所得，仍需专职 tester 在实现后按任务验收。
