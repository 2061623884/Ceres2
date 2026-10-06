import {useState} from 'react'
import type {GuideQuestion} from './lib/productQuestions'

interface Props {
  question: GuideQuestion
  disabled: boolean
  onAnswer: (optionIds: string[], quantities: Record<string, number>) => Promise<void> | void
}

/** A label is never a command: controls send only the displayed question/options. */
export default function QuestionChoices({question, disabled, onAnswer}: Props) {
  const [selected, setSelected] = useState<string[]>(question.kind === 'quantity' ? question.options.map(option=>option.option_id) : [])
  const [quantities, setQuantities] = useState<Record<string,string>>(Object.fromEntries(Object.entries(question.known_quantities ?? {}).map(([id,quantity])=>[id,String(quantity)])))
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inactive = disabled || submitting || question.status !== 'active'
  async function submit(ids: string[], counts: Record<string,number>) {
    setSubmitting(true);setError(null)
    try {await onAnswer(ids, counts)}
    catch (reason) {setError(reason instanceof Error ? reason.message : '选择未完成，请查看当前问题后重试。')}
    finally {setSubmitting(false)}
  }
  const selectedNow = question.status === 'answered' ? question.selected_option_ids : selected
  // A task total is unambiguous for one selected SKU only. Explicit edits,
  // including clearing an input, take precedence and survive selection changes.
  const shownQuantities = Object.fromEntries(question.options.map(option => [option.option_id, quantities[option.option_id] ?? (selected.length === 1 && selected[0] === option.option_id && question.known_total_quantity != null ? String(question.known_total_quantity) : '')]))
  const quantitiesValid = selected.length > 0 && selected.every(id => Number.isInteger(Number(shownQuantities[id])) && Number(shownQuantities[id]) > 0)
  return <section aria-label={question.question} className="my-2 space-y-2">
    {question.status !== 'active' && <p className="text-[11px] text-black/50">{question.status === 'answered' ? '已回答' : '此问题已失效，请查看当前条件重新选择'}</p>}
    {question.kind === 'products' && !!question.filter_options?.length && <div aria-label="按已知商品属性筛选" className="flex flex-wrap gap-2">{question.filter_options.map(option => <button key={option.option_id} type="button" disabled={inactive} aria-pressed={question.selected_option_ids.includes(option.option_id)} onClick={()=>void submit([option.option_id],{})} className="guide-glass-chip rounded-full px-3 py-2 text-[12px] disabled:opacity-50">{option.label}</button>)}</div>}
    {question.kind === 'category' ? <div className="flex flex-wrap gap-2">{question.options.map(option => <button key={option.option_id} type="button" disabled={inactive} aria-pressed={question.selected_option_ids.includes(option.option_id)} onClick={()=>void submit([option.option_id],{})} className="guide-glass-chip rounded-full px-3 py-2 text-[12px] disabled:opacity-50">{option.label}</button>)}</div> : <>
      {question.options.map(option => <div key={option.option_id} className="guide-glass-bubble rounded-2xl px-4 py-3">
        <label className="flex items-center gap-2 text-[12px] font-semibold"><input type="checkbox" aria-label={`选择 ${option.label}`} checked={selectedNow.includes(option.option_id)} disabled={inactive} onChange={event=>setSelected(ids=>event.target.checked?[...ids,option.option_id]:ids.filter(id=>id!==option.option_id))}/>{option.label}</label>
        {option.product && <>
          <p className="mt-1 text-[11px] text-black/55">品牌：{option.product.brand ?? '未知'} · 规格：{option.product.spec_quantity == null || !option.product.spec_unit ? '未知' : `${option.product.spec_quantity}${option.product.spec_unit}`}</p>
          <p className="mt-1 text-[11px] text-black/55">每销售包装：{option.product.price_fen == null ? '报价未知' : `¥${(option.product.price_fen/100).toFixed(2)}`} · 包装件数：{option.product.metadata.pack_count ?? '未知'}</p>
          <p className="mt-1 text-[11px] text-black/55">口味：{option.product.metadata.flavor ?? '未知'} · 包装：{({can:'罐装',bottle:'瓶装',bag:'袋装',box:'盒装'} as Record<string,string>)[option.product.metadata.packaging ?? ''] ?? option.product.metadata.packaging ?? '未知'} · 库存：{option.product.available_qty ?? '未知'}{option.product.available_qty == null ? '' : '件销售包装'}</p>
          <p className="mt-1 text-[10px] text-black/45">过敏原与饮食属性仅以已核实证据为准；未提供则未知。</p>
        </>}
        <label className="mt-2 flex items-center gap-2 text-[11px]">销售包装数量<input type="number" min="1" step="1" inputMode="numeric" aria-label={`数量 ${option.label}`} value={question.status === 'answered' ? (question.answered_quantities?.[option.option_id] ?? '') : shownQuantities[option.option_id]} disabled={inactive} onChange={event=>setQuantities({...quantities,[option.option_id]:event.target.value})} className="w-16 rounded border border-black/15 px-2 py-1"/></label>
      </div>)}
      {question.options.length > 0 && <button type="button" disabled={inactive || !quantitiesValid} onClick={()=>void submit(selected,Object.fromEntries(selected.map(id=>[id,Number(shownQuantities[id])])))} className="rounded-full bg-[#eac867] px-4 py-2 text-[12px] disabled:opacity-40">生成采购清单</button>}
    </>}
    {error && <p role="alert" className="text-[12px] text-red-700">{error}</p>}
    {submitting && <p role="status" className="text-[11px]">正在核对当前商品…</p>}
    <p className="text-[10px] text-black/45">模拟商品及门店报价。选定只生成清单，明确确认后才加购。</p>
  </section>
}
