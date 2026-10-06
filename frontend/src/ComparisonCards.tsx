import type { ProductComparisonCard } from './lib/saleGuide'

interface Props {
  cards: ProductComparisonCard[]
  disabled: boolean
  onSelect: (text: string) => void
}

/** Display only source-backed attributes. A selection prepares a separate plan. */
export default function ComparisonCards({ cards, disabled, onSelect }: Props) {
  if (!cards.length) return null
  return <section aria-label="商品候选比较" className="flex w-full flex-col gap-2">
    {cards.map(card => {
      const packageNames: Record<string, string> = {can:'罐', bottle:'瓶', box:'盒', carton:'纸盒', bag:'袋'}
      const packageName = card.packaging == null ? null : packageNames[card.packaging] ?? card.packaging
      return <div key={card.ref} className="guide-glass-bubble rounded-2xl px-4 py-3">
        <p className="text-[12px] font-semibold leading-5">{card.name}</p>
        <p className="mt-1 text-[11px] text-black/55">品牌：{card.brand ?? '未知'} · 包装：{packageName ?? '未知'}</p>
        <p className="mt-1 text-[11px] text-black/55">
          单件容量：{card.item_volume_ml == null ? '未知' : `${card.item_volume_ml}ml`}
          {' · '}件数：{card.pack_count == null ? '未知' : `${card.pack_count}件/包`}
          {' · '}整包规格：{card.spec_quantity == null || card.spec_unit == null ? '未知' : `${card.spec_quantity}${card.spec_unit}`}
        </p>
        <p className="mt-1 text-[12px] font-semibold">
          {card.price_fen == null ? '报价未知' : `¥${(card.price_fen / 100).toFixed(2)}/包`}
          <span className="font-normal text-black/55"> · {card.price_per_litre_yuan == null ? '每升价格未知／不适用' : `${card.price_per_litre_yuan.toFixed(2)} 元/升`}</span>
        </p>
        <button disabled={disabled} onClick={() => onSelect(`选择「${card.name}」（候选 ${card.ref}）生成采购清单`)} className="mt-2 rounded-full bg-[#eac867] px-3 py-1.5 text-[11px] font-medium disabled:opacity-40">选这款，生成清单</button>
      </div>
    })}
    <div className="flex flex-wrap gap-1.5">
      {[...new Set(cards.flatMap(card => card.brand ? [`只看${card.brand}品牌`] : [])), '只看罐装', '只看瓶装', '只看单件装', '只看多件装', '取消品牌和包装筛选'].map(label => (
        <button key={label} disabled={disabled} onClick={() => onSelect(`${label}，保留当前品类、预算和排除条件，重新比较`)} className="guide-glass-chip rounded-full px-3 py-2 text-[11px] text-black/60 disabled:opacity-40">{label}</button>
      ))}
    </div>
    <p className="text-[10px] text-black/45">模拟门店报价；选择后生成清单，明确确认才加购。</p>
  </section>
}
