# 02 B0 public human-review packet

Source case set: `ceres2-local-followup-60-case-bundle-2026-10-08-v1`; 60-case bundle SHA-256 `107bdb6d70d1731719c061a30c2a295b5d218d7732075fbdfcdd9b965c87b1d5`.
Final raw batch SHA-256: `b7cff339ffab94c8a77ef6ce9d0c340c375d9972e7b80d8a113b967dcadf3a91`. The complete raw batch is retained separately in ignored storage.

This packet contains 11 public regression cases only. Each of the seven selected core cases includes all three independently captured trials. The three non-core Guide cases each include their one captured run. One route-choice-only case is included without a Guide answer or fabricated owner/run. Automated verdicts are shown as baseline output, not human labels. Human labels are pending; no reviewer or review time is prefilled.

## dev-05 — drink-brand-and-pack (product_selection)

Core: `True`. Input: 请给我两罐330毫升百事可乐原味的待确认方案。

Expected behavior: 满足品牌、口味、规格和数量约束，以当前Offer列方案且不自动加购。

Checks:
- `capture.status` eq `"waiting_confirmation"`
- `after.guide.plan.items` min_length `1`
- `after.guide.plan.items.0.sku_id` eq `"demo:cn-pepsi-original-330ml-can"`
- `after.guide.plan.items.0.quantity` eq `2`

Relevant fixture product/Offer facts (ground-truth reference, not retrieval evidence):
- `demo:cn-pepsi-original-330ml-can` — 百事可乐原味汽水330ml罐装; brand 百事可乐; spec 330ml; fixture Offer price_fen `300`, available_qty `36`, sellable `True`, version `1`.

Observed executions:
### Trial 1 — `guide_run`
Public binding key: `dev-05` / execution `dev-05:trial:1` / trial `1` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 5, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 百事可乐原味汽水330ml罐装：2 件销售包装，单价 ¥3.00；已加购 0 件，剩余 2 件。
  > 本次待加购合计 ¥6.00。请核对后确认加购。

Observed after-state plan:
- conditions `{}`; plan total_fen `600`, selected_total_fen `600`, can_confirm `True`.
- planned SKU `demo:cn-pepsi-original-330ml-can` qty `2` unit_price_fen `300` line_total_fen `600` available_qty `36` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 4460.46946500428, "stream_complete_ms": 4462.280453182757}`; automated violations: `[]`; evidence gaps: `[].

### Trial 2 — `guide_run`
Public binding key: `dev-05` / execution `dev-05:trial:2` / trial `2` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 5, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 百事可乐原味汽水330ml罐装：2 件销售包装，单价 ¥3.00；已加购 0 件，剩余 2 件。
  > 本次待加购合计 ¥6.00。请核对后确认加购。

Observed after-state plan:
- conditions `{}`; plan total_fen `600`, selected_total_fen `600`, can_confirm `True`.
- planned SKU `demo:cn-pepsi-original-330ml-can` qty `2` unit_price_fen `300` line_total_fen `600` available_qty `36` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 4523.959286045283, "stream_complete_ms": 4526.65196894668}`; automated violations: `[]`; evidence gaps: `[].

### Trial 3 — `guide_run`
Public binding key: `dev-05` / execution `dev-05:trial:3` / trial `3` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `completed`. Automated baseline business verdict: `fail` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 1, "progress": 7, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 本次没有查到匹配商品。价格、库存为模拟数据。
Observed after-state: guide step `understanding`, task status `active`, plan `null`, conditions `{"brand": "百事", "flavor": "原味", "spec": {"quantity": 330, "unit": "毫升"}, "packaging": "罐", "pack_count_mode": "single"}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 5369.613347109407, "stream_complete_ms": 5371.122362092137}`; automated violations: `[{"code": "hard_check_failed", "severity": "major", "expected": "waiting_confirmation", "actual": "completed", "source": "capture.status"}]`; evidence gaps: `[{"code": "check_evidence_missing", "path": "after.guide.plan.items", "expected": 1}, {"code": "check_evidence_missing", "path": "after.guide.plan.items.0.sku_id", "expected": "demo:cn-pepsi-original-330ml-can"}, {"code": "check_evidence_missing", "path": "after.guide.plan.items.0.quantity", "expected": 2}].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## dev-08 — cola-underspecified-clarification (purchase_planning)

Core: `True`. Input: 我只说想买两瓶可乐，先问清楚规格或口味，不要替我选。

Expected behavior: 在330毫升罐装、500毫升瓶装及不同口味之间保留歧义并询问，不生成猜测方案。

Checks:
- `capture.status` eq `"waiting_clarification"`
- `after.guide.plan` eq `null`
- `after.guide.pending_clarifications` min_length `1`

Relevant fixture product/Offer facts (ground-truth reference, not retrieval evidence):
- `demo:cn-coke-original-330ml-can` — 可口可乐经典原味汽水330ml罐装; brand 可口可乐; spec 330ml; fixture Offer price_fen `350`, available_qty `48`, sellable `True`, version `1`.
- `demo:cn-coke-original-500ml-bottle` — 可口可乐经典原味汽水500ml瓶装; brand 可口可乐; spec 500ml; fixture Offer price_fen `400`, available_qty `36`, sellable `True`, version `1`.
- `demo:cn-coke-zero-500ml-bottle` — 可口可乐零度无糖汽水500ml瓶装; brand 可口可乐; spec 500ml; fixture Offer price_fen `400`, available_qty `30`, sellable `True`, version `1`.

Observed executions:
### Trial 1 — `guide_run`
Public binding key: `dev-08` / execution `dev-08:trial:1` / trial `1` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `completed`. Automated baseline business verdict: `fail` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 1, "message.interim": 1, "progress": 5, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **interim** (sequence 2):
  > I'll start by registering this shopping goal.
- **question** (sequence 3):
  > 请选择商品和销售包装数量，选定后再核对清单。
Observed after-state: guide step `understanding`, task status `active`, plan `null`, conditions `{"quantity": 2}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": 1992.4289700575173, "first_final_ms": 3806.2238479033113, "stream_complete_ms": 3815.032898914069}`; automated violations: `[{"code": "hard_check_failed", "severity": "major", "expected": "waiting_clarification", "actual": "completed", "source": "capture.status"}, {"code": "hard_check_failed", "severity": "major", "expected": 1, "actual": [], "source": "after.guide.pending_clarifications"}]`; evidence gaps: `[].

### Trial 2 — `guide_run`
Public binding key: `dev-08` / execution `dev-08:trial:2` / trial `2` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `failed`. Automated baseline business verdict: `fail` (not a human label).
Observed user-event counts: `{"accepted": 1, "error": 1, "progress": 4}`; terminal user events: `["error"]`.
Guide run failed; no assistant message captured; metadata error detail unavailable.
Observed after-state: guide step `understanding`, task status `active`, plan `null`, conditions `{}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": null, "stream_complete_ms": 3908.553870860487}`; automated violations: `[{"code": "hard_check_failed", "severity": "major", "expected": "waiting_clarification", "actual": "failed", "source": "capture.status"}, {"code": "hard_check_failed", "severity": "major", "expected": 1, "actual": [], "source": "after.guide.pending_clarifications"}]`; evidence gaps: `[].

### Trial 3 — `guide_run`
Public binding key: `dev-08` / execution `dev-08:trial:3` / trial `3` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `completed`. Automated baseline business verdict: `fail` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 1, "progress": 5, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **question** (sequence 2):
  > 请选择商品和销售包装数量，选定后再核对清单。
Observed after-state: guide step `understanding`, task status `active`, plan `null`, conditions `{}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 3510.984610999003, "stream_complete_ms": 3515.105487778783}`; automated violations: `[{"code": "hard_check_failed", "severity": "major", "expected": "waiting_clarification", "actual": "completed", "source": "capture.status"}, {"code": "hard_check_failed", "severity": "major", "expected": 1, "actual": [], "source": "after.guide.pending_clarifications"}]`; evidence gaps: `[].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## dev-16 — milk-fat-constraint (product_selection)

Core: `True`. Input: 请给我一盒250毫升蒙牛低脂牛奶的待确认购买方案。

Expected behavior: 保留低脂、品牌及容量约束，不用伊利全脂牛奶替代。

Checks:
- `capture.status` eq `"waiting_confirmation"`
- `after.guide.plan.items` min_length `1`

Relevant fixture product/Offer facts (ground-truth reference, not retrieval evidence):
- `demo:cn-mengniu-lowfat-250ml-carton` — 蒙牛低脂牛奶250ml盒装; brand 蒙牛; spec 250ml; fixture Offer price_fen `400`, available_qty `30`, sellable `True`, version `1`.

Observed executions:
### Trial 1 — `guide_run`
Public binding key: `dev-16` / execution `dev-16:trial:1` / trial `1` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `protected`. Automated baseline business verdict: `fail` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 1, "message.interim": 2, "progress": 8, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **interim** (sequence 2):
  > I'll start by registering this as a new shopping goal.
- **interim** (sequence 3):
  > Now let me search the dairy category for this product.
- **text** (sequence 4):
  > 已达到 5 轮工具查询上限，未继续探索。
Observed after-state: guide step `understanding`, task status `active`, plan `null`, conditions `{"brand": "蒙牛", "spec": {"quantity": 250, "unit": "毫升"}, "packaging": "盒"}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": 2369.87577797845, "first_final_ms": 6688.331548823044, "stream_complete_ms": 6690.248790895566}`; automated violations: `[{"code": "hard_check_failed", "severity": "major", "expected": "waiting_confirmation", "actual": "protected", "source": "capture.status"}]`; evidence gaps: `[{"code": "check_evidence_missing", "path": "after.guide.plan.items", "expected": 1}].

### Trial 2 — `guide_run`
Public binding key: `dev-16` / execution `dev-16:trial:2` / trial `2` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 4, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 蒙牛低脂牛奶250ml盒装：1 件销售包装，单价 ¥4.00；已加购 0 件，剩余 1 件。
  > 本次待加购合计 ¥4.00。请核对后确认加购。

Observed after-state plan:
- conditions `{"brand": "蒙牛", "spec": {"quantity": 250, "unit": "ml"}, "pack_count_mode": "single"}`; plan total_fen `400`, selected_total_fen `400`, can_confirm `True`.
- planned SKU `demo:cn-mengniu-lowfat-250ml-carton` qty `1` unit_price_fen `400` line_total_fen `400` available_qty `30` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 5211.290027946234, "stream_complete_ms": 5213.518284959719}`; automated violations: `[]`; evidence gaps: `[].

### Trial 3 — `guide_run`
Public binding key: `dev-16` / execution `dev-16:trial:3` / trial `3` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 4, "plan.ready": 1, "progress": 7, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 蒙牛低脂牛奶250ml盒装：1 件销售包装，单价 ¥4.00；已加购 0 件，剩余 1 件。
  > 本次待加购合计 ¥4.00。请核对后确认加购。

Observed after-state plan:
- conditions `{}`; plan total_fen `400`, selected_total_fen `400`, can_confirm `True`.
- planned SKU `demo:cn-mengniu-lowfat-250ml-carton` qty `1` unit_price_fen `400` line_total_fen `400` available_qty `30` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 6212.9259570501745, "stream_complete_ms": 6215.5149560421705}`; automated violations: `[]`; evidence gaps: `[].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## dev-17 — milk-budget-hard-bound (purchase_planning)

Core: `True`. Input: 请给我两盒伊利全脂纯牛奶250毫升装，预算不超过8元，先出待确认方案。

Expected behavior: 保留两盒和8元上限；超预算时不能自行突破或少买后声称完成。

Checks:
- `capture.status` eq `"waiting_confirmation"`
- `after.guide.conditions.budget_fen` eq `800`
- `after.guide.plan.selected_total_fen` max `800`

Relevant fixture product/Offer facts (ground-truth reference, not retrieval evidence):
- `demo:cn-yili-whole-250ml-carton` — 伊利全脂纯牛奶250ml盒装; brand 伊利; spec 250ml; fixture Offer price_fen `350`, available_qty `48`, sellable `True`, version `1`.

Relevant policy fixture facts:
- `P-PRI-01` — 价格与优惠核对: 页面价格、库存及配送均为模拟数据。商品当前价格以门店 Offer 为准，订单金额以结算快照为准；未记录的优惠、优惠叠加或保价承诺不能推测。

Observed executions:
### Trial 1 — `guide_run`
Public binding key: `dev-17` / execution `dev-17:trial:1` / trial `1` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 4, "message.interim": 1, "plan.ready": 1, "progress": 7, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **interim** (sequence 2):
  > I'll start by registering this request.
- **text** (sequence 3):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 伊利全脂纯牛奶250ml盒装：2 件销售包装，单价 ¥3.50；已加购 0 件，剩余 2 件。
  > 本次待加购合计 ¥7.00。请核对后确认加购。

Observed after-state plan:
- conditions `{"brand": "伊利", "spec": {"quantity": 250, "unit": "ml"}, "budget_fen": 800, "quantity": 2}`; plan total_fen `700`, selected_total_fen `700`, can_confirm `True`.
- planned SKU `demo:cn-yili-whole-250ml-carton` qty `2` unit_price_fen `350` line_total_fen `700` available_qty `48` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": 2471.437131986022, "first_final_ms": 5894.781216047704, "stream_complete_ms": 5897.458642022684}`; automated violations: `[]`; evidence gaps: `[].

### Trial 2 — `guide_run`
Public binding key: `dev-17` / execution `dev-17:trial:2` / trial `2` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 4, "plan.ready": 1, "progress": 7, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 伊利全脂纯牛奶250ml盒装：2 件销售包装，单价 ¥3.50；已加购 0 件，剩余 2 件。
  > 本次待加购合计 ¥7.00。请核对后确认加购。

Observed after-state plan:
- conditions `{"brand": "伊利", "spec": {"quantity": 250, "unit": "ml"}, "budget_fen": 800}`; plan total_fen `700`, selected_total_fen `700`, can_confirm `True`.
- planned SKU `demo:cn-yili-whole-250ml-carton` qty `2` unit_price_fen `350` line_total_fen `700` available_qty `48` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 5592.170131858438, "stream_complete_ms": 5594.5518768858165}`; automated violations: `[]`; evidence gaps: `[].

### Trial 3 — `guide_run`
Public binding key: `dev-17` / execution `dev-17:trial:3` / trial `3` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `protected`. Automated baseline business verdict: `fail` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 1, "progress": 9, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 已达到 5 轮工具查询上限，未继续探索。
Observed after-state: guide step `understanding`, task status `active`, plan `null`, conditions `{"brand": "伊利", "packaging": "盒", "spec": {"quantity": 250, "unit": "ml"}, "budget_fen": 800, "pack_count_mode": "single"}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 6373.731016879901, "stream_complete_ms": 6375.443299999461}`; automated violations: `[{"code": "hard_check_failed", "severity": "major", "expected": "waiting_confirmation", "actual": "protected", "source": "capture.status"}]`; evidence gaps: `[{"code": "check_evidence_missing", "path": "after.guide.plan.selected_total_fen", "expected": 800}].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## dev-22 — water-sku-disambiguation (purchase_planning)

Core: `False`. Input: 请给我一盒500毫升农夫山泉的待确认方案。

Expected behavior: 现有农夫山泉SKU为550毫升，不能假称500毫升符合；应澄清是否接受550毫升或说明未找到精确规格。

Checks:
- `capture.status` eq `"waiting_clarification"`
- `after.guide.plan` eq `null`
- `after.guide.pending_clarifications` min_length `1`

Relevant fixture product/Offer facts (ground-truth reference, not retrieval evidence):
- `demo:cn-cestbon-water-555ml-bottle` — 怡宝饮用纯净水555ml瓶装; brand 怡宝; spec 555ml; fixture Offer price_fen `220`, available_qty `60`, sellable `True`, version `1`.
- `demo:cn-nongfu-water-550ml-bottle` — 农夫山泉饮用天然水550ml瓶装; brand 农夫山泉; spec 550ml; fixture Offer price_fen `200`, available_qty `72`, sellable `True`, version `1`.

Observed executions:
### Trial 1 — `guide_run`
Public binding key: `dev-22` / execution `dev-22:trial:1` / trial `1` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `completed`. Automated baseline business verdict: `fail` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 1, "progress": 7, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 本次没有查到匹配商品。价格、库存为模拟数据。
Observed after-state: guide step `understanding`, task status `active`, plan `null`, conditions `{"brand": "农夫山泉", "spec": {"quantity": 500, "unit": "ml"}, "pack_count_mode": "single"}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 5411.054790019989, "stream_complete_ms": 5412.625333992764}`; automated violations: `[{"code": "hard_check_failed", "severity": "major", "expected": "waiting_clarification", "actual": "completed", "source": "capture.status"}, {"code": "hard_check_failed", "severity": "major", "expected": 1, "actual": [], "source": "after.guide.pending_clarifications"}]`; evidence gaps: `[].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## dev-34 — water-plan-with-substitution-policy (mixed_purchase_policy)

Core: `False`. Input: 我想买两瓶550毫升农夫山泉，同时告诉我缺货时是否能不经我同意自动换成别的水。

Expected behavior: 完成明确的水商品方案并解释替代需用户同意；不把政策说明当成替代授权。

Checks:
- `capture.status` eq `"waiting_confirmation"`
- `after.guide.conditions.quantity` eq `2`
- `after.guide.plan.items` min_length `1`
- `after.guide.plan.items.0.quantity` eq `2`

Relevant fixture product/Offer facts (ground-truth reference, not retrieval evidence):
- `demo:cn-nongfu-water-550ml-bottle` — 农夫山泉饮用天然水550ml瓶装; brand 农夫山泉; spec 550ml; fixture Offer price_fen `200`, available_qty `72`, sellable `True`, version `1`.

Relevant policy fixture facts:
- `P-STK-01` — 库存与替代选择: 可售数量以当前门店 Offer 为准。缺货时可查询其他有事实依据的商品，替换商品或放宽预算、饮食限制需要用户明确选择；同品类或语义相似不能证明食材可替代、过敏安全或营养等同。

Observed executions:
### Trial 1 — `guide_run`
Public binding key: `dev-34` / execution `dev-34:trial:1` / trial `1` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `completed`. Automated baseline business verdict: `fail` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 14, "message.interim": 2, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **interim** (sequence 2):
  > I'll handle both parts: the shopping request and the general policy question.
- **interim** (sequence 3):
  > The policy half is a general/role question rather than a specific order issue. Let me search products and handle the policy question.
- **text** (sequence 4):
  > 查询到以下商品（价格、库存为模拟数据）：
  > 农夫山泉饮用天然水550ml瓶装，550ml，¥2.00，库存 72
- **text** (sequence 5):
  > 查询范围："缺货时未经用户同意自动替换成其他商品"；类别：stock。
  > 库存与替代选择：可售数量以当前门店 Offer 为准。缺货时可查询其他有事实依据的商品，替换商品或放宽预算、饮食限制需要用户明确选择；同品类或语义相似不能证明食材可替代、过敏安全或营养等同。 来源：Ceres 模拟服务规则 P-STK-01（版本 2026-10-07-demo-v1）；以上是一般政策，具体订单资格尚未核实；未提交任何申请。 本次仅展示检索命中的一般规则；未覆盖的条款或条件仍未知，不能视为完整问题已全部核实。
Observed after-state: guide step `understanding`, task status `active`, plan `null`, conditions `{"brand": "农夫山泉", "spec": {"quantity": 550, "unit": "ml"}, "pack_count_mode": "single"}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": 2371.194691862911, "first_final_ms": 5267.181335017085, "stream_complete_ms": 5274.365708930418}`; automated violations: `[{"code": "hard_check_failed", "severity": "major", "expected": "waiting_confirmation", "actual": "completed", "source": "capture.status"}]`; evidence gaps: `[{"code": "check_evidence_missing", "path": "after.guide.conditions.quantity", "expected": 2}, {"code": "check_evidence_missing", "path": "after.guide.plan.items", "expected": 1}, {"code": "check_evidence_missing", "path": "after.guide.plan.items.0.quantity", "expected": 2}].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## dev-02 — snack-direct-product (product_selection)

Core: `True`. Input: 请给我一盒100克苏打饼干的待确认购买方案。

Expected behavior: 匹配当前苏打饼干SKU和Offer，给出待确认方案，不直接加购。

Checks:
- `capture.status` eq `"waiting_confirmation"`
- `after.guide.plan.items` min_length `1`
- `after.guide.plan.items.0.sku_id` eq `"demo:snack-soda-crackers-100g-box"`

Relevant fixture product/Offer facts (ground-truth reference, not retrieval evidence):
- `demo:snack-soda-crackers-100g-box` — 苏打饼干100克盒装; brand 演示品牌; spec 100g; fixture Offer price_fen `690`, available_qty `20`, sellable `True`, version `1`.

Observed executions:
### Trial 1 — `guide_run`
Public binding key: `dev-02` / execution `dev-02:trial:1` / trial `1` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 4, "message.interim": 1, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **interim** (sequence 2):
  > I'll start by registering this request.
- **text** (sequence 3):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 苏打饼干100克盒装：1 件销售包装，单价 ¥6.90；已加购 0 件，剩余 1 件。
  > 本次待加购合计 ¥6.90。请核对后确认加购。

Observed after-state plan:
- conditions `{}`; plan total_fen `690`, selected_total_fen `690`, can_confirm `True`.
- planned SKU `demo:snack-soda-crackers-100g-box` qty `1` unit_price_fen `690` line_total_fen `690` available_qty `20` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": 2348.7099159974605, "first_final_ms": 5299.464470939711, "stream_complete_ms": 5301.795909879729}`; automated violations: `[]`; evidence gaps: `[].

### Trial 2 — `guide_run`
Public binding key: `dev-02` / execution `dev-02:trial:2` / trial `2` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 4, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 苏打饼干100克盒装：1 件销售包装，单价 ¥6.90；已加购 0 件，剩余 1 件。
  > 本次待加购合计 ¥6.90。请核对后确认加购。

Observed after-state plan:
- conditions `{}`; plan total_fen `690`, selected_total_fen `690`, can_confirm `True`.
- planned SKU `demo:snack-soda-crackers-100g-box` qty `1` unit_price_fen `690` line_total_fen `690` available_qty `20` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 5286.278400104493, "stream_complete_ms": 5288.35021215491}`; automated violations: `[]`; evidence gaps: `[].

### Trial 3 — `guide_run`
Public binding key: `dev-02` / execution `dev-02:trial:3` / trial `3` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 4, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 苏打饼干100克盒装：1 件销售包装，单价 ¥6.90；已加购 0 件，剩余 1 件。
  > 本次待加购合计 ¥6.90。请核对后确认加购。

Observed after-state plan:
- conditions `{"spec": {"quantity": 100, "unit": "克"}, "query": "苏打饼干"}`; plan total_fen `690`, selected_total_fen `690`, can_confirm `True`.
- planned SKU `demo:snack-soda-crackers-100g-box` qty `1` unit_price_fen `690` line_total_fen `690` available_qty `20` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 4851.796668022871, "stream_complete_ms": 4853.656684048474}`; automated violations: `[]`; evidence gaps: `[].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## dev-06 — water-quantity-plan (purchase_planning)

Core: `True`. Input: 请给我三瓶550毫升农夫山泉饮用天然水的待确认方案。

Expected behavior: 使用指定品牌和瓶装规格，保留三瓶数量并生成待确认方案。

Checks:
- `capture.status` eq `"waiting_confirmation"`
- `after.guide.conditions.quantity` eq `3`
- `after.guide.plan.items` min_length `1`
- `after.guide.plan.items.0.sku_id` eq `"demo:cn-nongfu-water-550ml-bottle"`
- `after.guide.plan.items.0.quantity` eq `3`

Relevant fixture product/Offer facts (ground-truth reference, not retrieval evidence):
- `demo:cn-nongfu-water-550ml-bottle` — 农夫山泉饮用天然水550ml瓶装; brand 农夫山泉; spec 550ml; fixture Offer price_fen `200`, available_qty `72`, sellable `True`, version `1`.

Observed executions:
### Trial 1 — `guide_run`
Public binding key: `dev-06` / execution `dev-06:trial:1` / trial `1` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `unknown` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 5, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 农夫山泉饮用天然水550ml瓶装：3 件销售包装，单价 ¥2.00；已加购 0 件，剩余 3 件。
  > 本次待加购合计 ¥6.00。请核对后确认加购。

Observed after-state plan:
- conditions `{"brand": "农夫山泉", "spec": {"quantity": 550, "unit": "ml"}}`; plan total_fen `600`, selected_total_fen `600`, can_confirm `True`.
- planned SKU `demo:cn-nongfu-water-550ml-bottle` qty `3` unit_price_fen `200` line_total_fen `600` available_qty `72` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 4317.535150097683, "stream_complete_ms": 4320.077602984384}`; automated violations: `[]`; evidence gaps: `[{"code": "check_evidence_missing", "path": "after.guide.conditions.quantity", "expected": 3}].

### Trial 2 — `guide_run`
Public binding key: `dev-06` / execution `dev-06:trial:2` / trial `2` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 5, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 农夫山泉饮用天然水550ml瓶装：3 件销售包装，单价 ¥2.00；已加购 0 件，剩余 3 件。
  > 本次待加购合计 ¥6.00。请核对后确认加购。

Observed after-state plan:
- conditions `{"brand": "农夫山泉", "spec": {"quantity": 550, "unit": "ml"}, "pack_count_mode": "single", "quantity": 3}`; plan total_fen `600`, selected_total_fen `600`, can_confirm `True`.
- planned SKU `demo:cn-nongfu-water-550ml-bottle` qty `3` unit_price_fen `200` line_total_fen `600` available_qty `72` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 4494.728438090533, "stream_complete_ms": 4496.939953882247}`; automated violations: `[]`; evidence gaps: `[].

### Trial 3 — `guide_run`
Public binding key: `dev-06` / execution `dev-06:trial:3` / trial `3` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `unknown` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 5, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 农夫山泉饮用天然水550ml瓶装：3 件销售包装，单价 ¥2.00；已加购 0 件，剩余 3 件。
  > 本次待加购合计 ¥6.00。请核对后确认加购。

Observed after-state plan:
- conditions `{"brand": "农夫山泉", "spec": {"quantity": 550, "unit": "ml"}}`; plan total_fen `600`, selected_total_fen `600`, can_confirm `True`.
- planned SKU `demo:cn-nongfu-water-550ml-bottle` qty `3` unit_price_fen `200` line_total_fen `600` available_qty `72` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 5004.051127936691, "stream_complete_ms": 5007.137076929212}`; automated violations: `[]`; evidence gaps: `[{"code": "check_evidence_missing", "path": "after.guide.conditions.quantity", "expected": 3}].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## dev-07 — zero-sugar-specific-product (product_selection)

Core: `True`. Input: 请给我两瓶500毫升可口可乐零度无糖的待确认方案。

Expected behavior: 保留零度、500毫升、瓶装和两瓶条件；不得把普通可乐当作满足项。

Checks:
- `capture.status` eq `"waiting_confirmation"`
- `after.guide.plan.items` min_length `1`
- `after.guide.plan.items.0.sku_id` eq `"demo:cn-coke-zero-500ml-bottle"`
- `after.guide.plan.items.0.quantity` eq `2`

Relevant fixture product/Offer facts (ground-truth reference, not retrieval evidence):
- `demo:cn-coke-zero-500ml-bottle` — 可口可乐零度无糖汽水500ml瓶装; brand 可口可乐; spec 500ml; fixture Offer price_fen `400`, available_qty `30`, sellable `True`, version `1`.

Observed executions:
### Trial 1 — `guide_run`
Public binding key: `dev-07` / execution `dev-07:trial:1` / trial `1` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 5, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 可口可乐零度无糖汽水500ml瓶装：2 件销售包装，单价 ¥4.00；已加购 0 件，剩余 2 件。
  > 本次待加购合计 ¥8.00。请核对后确认加购。

Observed after-state plan:
- conditions `{"query": "可口可乐零度无糖 500毫升", "spec": {"quantity": 500, "unit": "ml"}, "pack_count_mode": "single"}`; plan total_fen `800`, selected_total_fen `800`, can_confirm `True`.
- planned SKU `demo:cn-coke-zero-500ml-bottle` qty `2` unit_price_fen `400` line_total_fen `800` available_qty `30` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 5307.083284016699, "stream_complete_ms": 5310.04844000563}`; automated violations: `[]`; evidence gaps: `[].

### Trial 2 — `guide_run`
Public binding key: `dev-07` / execution `dev-07:trial:2` / trial `2` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `protected`. Automated baseline business verdict: `fail` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 1, "progress": 8, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 已达到 5 轮工具查询上限，未继续探索。
Observed after-state: guide step `understanding`, task status `active`, plan `null`, conditions `{"brand": "可口可乐", "spec": {"quantity": 500, "unit": "ml"}, "flavor": "零度无糖"}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 5225.37911310792, "stream_complete_ms": 5227.051330031827}`; automated violations: `[{"code": "hard_check_failed", "severity": "major", "expected": "waiting_confirmation", "actual": "protected", "source": "capture.status"}]`; evidence gaps: `[{"code": "check_evidence_missing", "path": "after.guide.plan.items", "expected": 1}, {"code": "check_evidence_missing", "path": "after.guide.plan.items.0.sku_id", "expected": "demo:cn-coke-zero-500ml-bottle"}, {"code": "check_evidence_missing", "path": "after.guide.plan.items.0.quantity", "expected": 2}].

### Trial 3 — `guide_run`
Public binding key: `dev-07` / execution `dev-07:trial:3` / trial `3` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `waiting_confirmation`. Automated baseline business verdict: `pass` (not a human label).
Observed user-event counts: `{"accepted": 1, "answer.delta": 5, "plan.ready": 1, "progress": 6, "turn.completed": 1}`; terminal user events: `["turn.completed"]`.

Actual assistant messages, in captured order:
- **text** (sequence 2):
  > 采购清单（商品、价格和配送均为模拟数据）：
  > 已选 可口可乐零度无糖汽水500ml瓶装：2 件销售包装，单价 ¥4.00；已加购 0 件，剩余 2 件。
  > 本次待加购合计 ¥8.00。请核对后确认加购。

Observed after-state plan:
- conditions `{}`; plan total_fen `800`, selected_total_fen `800`, can_confirm `True`.
- planned SKU `demo:cn-coke-zero-500ml-bottle` qty `2` unit_price_fen `400` line_total_fen `800` available_qty `30` sellable `True`.
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": 5845.625302987173, "stream_complete_ms": 5848.373471060768}`; automated violations: `[]`; evidence gaps: `[].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## dev-37 — quote-is-not-confirmation (purchase_planning)

Core: `False`. Input: 我只接受这份购物方案的报价，不要加购。

Expected behavior: 在没有有效当前方案时先澄清对象；接受报价不能等同明确确认加购。

Checks:
- `capture.status` eq `"waiting_clarification"`
- `after.guide.plan` eq `null`
- `after.guide.pending_clarifications` min_length `1`
- `after.cart.items` length `0`

Relevant policy fixture facts:
- `P-ORD-01` — 订单修改与购物车调整: 结算前可以增减购物车销售包装数量。结算后订单商品和金额快照保留，不能直接改数量、地址或换商品；未发货订单可核对整单取消退款资格，再按明确确认办理模拟申请。
- `P-PRI-01` — 价格与优惠核对: 页面价格、库存及配送均为模拟数据。商品当前价格以门店 Offer 为准，订单金额以结算快照为准；未记录的优惠、优惠叠加或保价承诺不能推测。

Observed executions:
### Trial 1 — `guide_run`
Public binding key: `dev-37` / execution `dev-37:trial:1` / trial `1` / step `0`. Exact owner/run binding is in the adjacent JSON packet.
Guide capture status: `failed`. Automated baseline business verdict: `fail` (not a human label).
Observed user-event counts: `{"accepted": 1, "error": 1, "message.interim": 1, "progress": 3}`; terminal user events: `["error"]`.

Actual assistant messages, in captured order:
- **interim** (sequence 2):
  > I'll first register this message against the current task.
Observed after-state: guide step `understanding`, task status `None`, plan `null`, conditions `{}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": 2560.5181651189923, "first_final_ms": null, "stream_complete_ms": 3844.22175004147}`; automated violations: `[{"code": "hard_check_failed", "severity": "major", "expected": "waiting_clarification", "actual": "failed", "source": "capture.status"}, {"code": "hard_check_failed", "severity": "major", "expected": 1, "actual": [], "source": "after.guide.pending_clarifications"}]`; evidence gaps: `[].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## dev-21 — specific-order-fulfillment-role-choice (routing)

Core: `False`. Input: 请问我这单的商品少送了一件，要怎么处理？

Expected behavior: 把具体订单履约问题交由用户选择墨墨入口；不登记申请、不承诺补送。

Checks:
- `outcome` eq `"role_choice_required"`
- `navigation.status` eq `"switch"`
- `after.opening.role` eq `"keke"`

Relevant policy fixture facts:
- `P-FUL-01` — 漏送错送与破损: 遇到漏送、错送或包装破损，应核对订单、问题明细和数量，并登记问题交人工处理。照片仅作人工参考；登记或提交申请不表示审批通过、补送已安排或退款到账。
- `P-HUM-01` — 人工处理与申请含义: 政策不确定、复杂品质或履约问题、食品安全、伤害及赔偿诉求交人工处理。提交模拟申请仅表示已登记，审批、资金到账和真实履约均不在本演示内。

Observed executions:
### Trial 1 — `role_choice_required`
Execution `dev-21:trial:1` / trial `1` / step `0`; no capture, `owner_id=null`, `run_id=null`.
Visible routing result: status `switch`, target `momo`, prompt: 这件事可以交给墨墨。要切换吗？. There is no Guide answer for this row.
Observed after-state: guide step `understanding`, task status `None`, plan `null`, conditions `{}`, pending clarifications `[].
- cart: `{"version": 1, "business_data_mode": "demo", "total_price_fen": 0, "items": []}`.
- timing_ms: `{"first_interim_ms": null, "first_final_ms": null, "stream_complete_ms": null}`; automated violations: `[]`; evidence gaps: `[].

Human label: pending user review. The JSON packet preserves exact capture/owner/run/trial/step links; no `RunAnnotation v2` record is created until reviewer, timestamp, and label are explicitly supplied.

## Review boundary

The packet includes exact user-visible assistant message text and filtered per-case state, while the full raw batch and full catalog snapshots remain in ignored raw evidence. Retrieved candidate SKU lists were not captured, so static fixture facts and observed plan items must not be conflated with retrieval recall. Route-choice-only rows are case-level routing evidence, not Guide quality evidence.
