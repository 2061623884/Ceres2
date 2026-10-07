# Ceres2 菜谱—食材—商品关系审计

调研时间：2026-10-07。代码基线：`b118dbea3852026c6a04c790b1e27df67c3c9c18`。本报告按 TASK05/06/07、GLOSSARY、当前 Python 代码、数据 fixtures 与测试定义做只读审计；没有运行测试、安装依赖或调用模型，也没有读取 `archive/` 或 `reference/`。

**结论：当前 TASK05—07 的采购闭环不需要 Knowledge-Graph RAG。** 现有菜谱→食材→SKU 是少量明确 ID 关系；人数换算、多菜合并、整包取整、库存和排除都是 Python 可解释的算术/确定性过滤。跨食材的可信替代、家庭 pantry 库存、营养/成分关系则是尚未提供的新事实源，不能靠 RAG 或模型推测补齐。商品/菜谱知识图谱 RAG 应作为独立产品提议评估，不改变本轮已确定的售后政策 hybrid/RRF 范围。

## 当前数据覆盖

以下计数来自直接读取当前 `data/fixtures/*.json` 文件，不是测试结果。

| 数据 | 当前覆盖 | 结论 |
|---|---:|---|
| 菜谱 | `recipes.json` v1 有 2 道菜；每道基准 2 人；4 条有量 required 项，6 条无量 pantry 项，0 optional 项 | 菜谱语料很小，pantry 项没有用量 |
| 菜谱食材关系 | 7 个 distinct `ingredient_id`，共 8 条食材→SKU 关系；7 种食材都有直接 SKU 候选，8 个映射 SKU 均有 Offer | 关系覆盖对当前两道菜是 100%，但仅是精确 ID 映射 |
| 当前候选数 | tomato 1、egg 2、rice 1；oil/salt/sugar/scallion 各 1 | 唯一多规格候选是 egg 的 6 枚与 10 枚包装，不是不同食材的替代 |
| 商品目录 | 70 SKU，均标记 `source=demo`、`review_status=approved`；59 个 SKU 有 `ingredient_ids`，覆盖 46 个不同 ID，11 个 SKU 没有食材关联 | `ingredient_ids` 是采购需求映射，不是配料/成分表 |
| Offer | 70 条 demo Offer，均属于 `store-demo-01` | 不代表其他门店或真实供给 |
| 食品属性 | 3 个商品有 `metadata.allergens`，全部 `status=unknown` 且 `evidence=null`；唯一带 `metadata.attribute_evidence` 的商品其值为空；没有 nutrition/nutrients 字段 | 当前 8 个菜谱候选 SKU 均没有可用的过敏/营养证据 |

计数依据：[recipes.json](../../../data/fixtures/recipes.json:1)、[products.json](../../../data/fixtures/products.json:1)、[offers.json](../../../data/fixtures/offers.json:1)。例如 recipe 候选商品是由 [DishService.candidates](../../../backend/app/services/dish_service.py:22) 按 `ingredient_id in product.ingredient_ids` 取出的；metadata 中的 `ingredient_mapping` 并未被这条运行路径读取。[CatalogProduct](../../../backend/app/models/catalog.py:7) 将 `ingredient_ids` 和 `metadata_json` 分开保存；[seed_service.py](../../../backend/app/services/seed_service.py:11) 从静态 fixture 导入它们。

## TASK 与当前实现对照

- **TASK05 单菜与人数**要求按人数缩放食材量、显示整包数量/余量、可选 pantry 默认不选；未选 pantry 不代表用户家中已有。[TASK05 范围与验收](../../../tasks/ceres2-runtime-upgrade-05-single-dish-servings.md:11) · [GLOSSARY 的采购清单边界](../../../GLOSSARY.md:41)。代码按 `原始用量 × 人数 / 基准人数` 计算；枚举数量单位为 `pc` 时向上取整，再按销售包装取整，不做 g/ml/pc 换算。没有用量的 pantry 项需求、coverage、余量为 null，默认不选；选择后以一个销售包装处理。[dish_service.py](../../../backend/app/services/dish_service.py:27) · [TASK05 handoff](../../../work/clean-rebuild/05/HANDOFF.md:7)
- **TASK06 多菜**是用户明确追加另一菜后，按兼容食材合并需求、保留每道菜贡献及已购 ledger；改/删一组不破坏其他组。[TASK06 范围与验收](../../../tasks/ceres2-runtime-upgrade-06-multi-dish-demand.md:11) · [dish_service.py](../../../backend/app/services/dish_service.py:80)。合并按 SKU key，只有 `ingredient_id`、数量和单位相同才合并数量再取整；没有跨 ingredient ID 的语义归并。[recalculate_contribution_demand](../../../backend/app/services/dish_service.py:97)
- **TASK07 供给处理**是同一食材候选规格缺货/库存不足时，比较可售包装组合、价格与余量，用户显式选替代规格或部分采购后再确认。[TASK07 范围与验收](../../../tasks/ceres2-runtime-upgrade-07-supply-partial-purchase.md:11)。候选来自该食材已有的 `available_specs`；算法只在其中枚举销售包装，不会创造另一种食材关系。[supply_service.py](../../../backend/app/services/supply_service.py:48) · [TASK07 验收](../../../tasks/ceres2-runtime-upgrade-07-supply-partial-purchase.md:21)
- 当前购物车数量和本任务 PurchaseLedger 分开读取；菜谱 pantry 标记不是用户 pantry 库存。[supply_service.py](../../../backend/app/services/supply_service.py:9) · [GLOSSARY](../../../GLOSSARY.md:41-53)。TASK05 测试定义验证默认人数、pantry 未选及数量未知；TASK06 验证共享鸡蛋用量和 pantry contribution 未知；TASK07 验证同食材的 6/10 枚包装替换、混装和部分采购。[test_dish_public.py](../../../backend/tests/test_dish_public.py:56) · [test_multidish_public.py](../../../backend/tests/test_multidish_public.py:141) · [test_supply_public.py](../../../backend/tests/test_supply_public.py:11) · [混装规格案例](../../../backend/tests/test_supply_public.py:97)。这些是代码中测试定义，本轮没有重跑。
- **排除/安全属性**不是语义关系检索。普通 exclusions 用 SKU/name/brand/ingredient ID/usage tag 的精确相等匹配；TASK07 规格候选同样按这些精确字段过滤。[PurchaseService.facts](../../../backend/app/services/purchase_service.py:71) · [supply_service.py](../../../backend/app/services/supply_service.py:53)。饮食/过敏约束要求商品 `metadata.attribute_evidence` 同时有 source 和 value，缺失时 fail-closed；代码明确禁止从 `ingredient_id` 推断过敏安全。[product_constraints.py](../../../backend/app/services/product_constraints.py:1)。测试通过受控 fixture 注入标签证据并验证未知证据不满足约束；那不是当前商品数据来源。[test_final_review_constraints_public.py](../../../backend/tests/test_final_review_constraints_public.py:11) · [未知过敏证据测试定义](../../../backend/tests/test_next_snack_public.py:146)

GLOSSARY 将“食材”定义为原料概念、“商品/SKU”定义为具体销售包装；“食材关联”仅表示某商品可满足该采购需求，不代表完整配料表或成分表。[GLOSSARY 食材与关联定义](../../../GLOSSARY.md:70-91)。因此同 ID 的包装互换、基于已知字段的过滤与营养/过敏成分推断是不同问题。

商品品类是货架分类，`usage_tags` 是商品使用标签；两者都不是不同食材间的等价/替代关系，不能把类别当作替代关系的中介。[GLOSSARY 商品品类与食材关联](../../../GLOSSARY.md:70-87)

## 来源版本与证据限制

当前菜谱和商品 fixtures 各自标为 `v1`；当前文件 SHA-256 为：`recipes.json` `7875530ea65e196e24a34dee98b1e8e648c4754ccd4cbc416b25a973ad6bb23c`、`products.json` `2a51486e885818ee1bd66fcd55dd8de4e165a84905487aac8cde6b47a2172d84`、`offers.json` `2425c593fccf19283b31c1d2bff5968852f685e3593a18c8deebc5a8098b6d66`。这些哈希标识当前 fixture 字节，不证明食材映射或商品属性的外部权威性。

TASK05 指向 `work/clean-rebuild/05/recipe-provenance.json` 作为菜谱来源 SHA 与选择依据；当前目标树中该文件不存在。[TASK05 evidence](../../../tasks/ceres2-runtime-upgrade-05-single-dish-servings.md:41)。保留的导入脚本则声明从 staging 的 `chinese-dishes-v1.json` 按两个 dish ID 选取，并将 provenance 写往 `work/clean-rebuild/06/recipe-provenance.json`；该输出文件在当前树也不存在。[import_recipes.py](../../../work/clean-rebuild/06/import_recipes.py:6)。按项目只读边界，本轮没有读取 staging 来源，故不能验证上游 recipe SHA。

商品 fixture 全部标记为 demo；目前三条 `ingredient_mapping` 元数据为 `demo_declared`，运行时也不读取它们。TASK05—07 的任务文件记录了受控技术验证结果，但状态仍为“待验收/用户本人验收待完成”；本审计不把历史测试结果当作本轮验证。[TASK05 状态](../../../tasks/ceres2-runtime-upgrade-05-single-dish-servings.md:3) · [TASK06 状态](../../../tasks/ceres2-runtime-upgrade-06-multi-dish-demand.md:3) · [TASK07 状态](../../../tasks/ceres2-runtime-upgrade-07-supply-partial-purchase.md:3)

## 哪些新问题会用到新关系

| 可能的用户场景 | 相对当前缺少的事实/查询 | 是否因此需要 Graph-RAG |
|---|---|---|
| 用户明确询问某食材缺货时，是否存在跨 `ingredient_id` 的替代，并要求解释在当前菜品/做法下的适用条件 | 需要经审核、有来源、能表达菜品/烹调条件和用量关系的“替代”边；当前只有相同 ID 的 SKU 包装候选 | 这是确实的新关系类型；先建来源明确的结构化替代关系和拒答边界，再单独比较关系查询/RAG 是否带来收益。不能让模型自行认定食材等价 |
| 用户问“按我家现有食材能做哪些菜、还缺什么” | 当前有 recipe→ingredient→SKU，购物车/任务已购 ledger 可按 ID join；没有家庭 pantry 库存实体或读取入口 | 需要当前用户明确提供的食材事实和反向关系查询；可先使用会话内临时信息，数量未知保持未知，无需为试点新增家庭库存实体。精确 ID join + 数量计算即可，单独的 Graph-RAG 无明显必要 |
| 用户要求按过敏或营养目标筛选/修改菜谱，并说明影响 | 需要有来源和生效版本的配料/过敏原/营养属性，以及菜谱份量到商品/原料属性的可解释关联；当前营养字段为 0，过敏证据未知 | 需要补权威数据和关系查询；稳定字段应优先做确定性过滤/算术。只有必须从权威非结构化材料取证时，才评估 RAG 的引用收益 |

## 建议的独立评估门槛

KG-RAG 提议尚未决定实施；建议暂不以它替换商品检索，本轮候选验证由用户定案。独立实验优先评估“用已有食材反查菜谱、明确缺项”：先固定现有 recipe→ingredient→SKU 边和同一批输入，比较普通 SQLite 关系查询/集合计算与图表示查询能否正确列出可做菜谱、缺项和数量；保持关系数据不变，才可归因表示/查询方式的差异。再单独测明确的会话食材来源或新审核关系带来的覆盖变化，不能把补数据收益算作 Graph-RAG 收益。若评审后要做跨食材替代，必须单独提供来源和适用边；类别或标签不能充当替代中介。补充来源数据本身不等于必须上图数据库或 RAG。
