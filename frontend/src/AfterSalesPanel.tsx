import { useEffect, useRef, useState } from 'react'
import { readAftersales, readAftersalesOrder, proposeAftersales, confirmAftersales } from './lib/aftersales'
import type { AfterSalesState, AfterSalesOrder } from './lib/aftersales'

export function AfterSalesPanel({ caseId, orderId, selectionVersion, refreshKey, disabled }: {
  caseId: string; orderId: string; selectionVersion: number; refreshKey: number; disabled: boolean
}) {
  const [state, setState] = useState<AfterSalesState>({ proposal: null, receipts: [] })
  const [order, setOrder] = useState<AfterSalesOrder | null>(null)
  const [kind, setKind] = useState<'refund' | 'return'>('refund')
  const [itemId, setItemId] = useState('')
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const generation = useRef(0)
  useEffect(() => {
    const token = ++generation.current
    setState({ proposal: null, receipts: [] }); setOrder(null); setError(''); setBusy(true)
    void Promise.all([readAftersales(caseId), orderId ? readAftersalesOrder(orderId) : Promise.resolve(null)])
      .then(([next, selected]) => { if (token === generation.current) { setState(next); setOrder(selected); setItemId('') } })
      .catch((e: Error) => { if (token === generation.current) setError(e.message) })
      .finally(() => { if (token === generation.current) setBusy(false) })
    return () => { generation.current++ }
  }, [caseId, orderId, selectionVersion, refreshKey])

  async function prepare() {
    if (busy || disabled || !orderId || !reason.trim() || (kind === 'return' && !itemId)) return
    const token = generation.current
    setBusy(true); setError('')
    try {
      const proposal = await proposeAftersales(caseId, { kind, item_id: kind === 'return' ? itemId : null, reason: reason.trim(), selection_version: selectionVersion })
      if (token === generation.current) setState(previous => ({ ...previous, proposal }))
    } catch (e) { if (token === generation.current) setError((e as Error).message) }
    finally { if (token === generation.current) setBusy(false) }
  }
  async function confirm() {
    if (busy || disabled || !state.proposal) return
    const token = generation.current
    const proposalId = state.proposal.proposal_id
    setBusy(true); setError('')
    try {
      const receipt = await confirmAftersales(caseId, proposalId)
      if (token === generation.current) setState(previous => ({ proposal: null, receipts: [...previous.receipts.filter(item => item.receipt_id !== receipt.receipt_id), receipt] }))
    } catch (e) { if (token === generation.current) setError((e as Error).message) }
    finally { if (token === generation.current) setBusy(false) }
  }
  return <section aria-label="模拟售后申请" className="space-y-2 rounded-2xl border border-black/10 p-3 text-xs">
    <p>模拟售后 · 先查看提案，再确认提交</p>
    {orderId && <div className="flex flex-wrap gap-2">
      <select aria-label="售后类型" value={kind} disabled={busy || disabled} onChange={event => { setKind(event.target.value as 'refund' | 'return'); setState(previous => ({ ...previous, proposal: null })) }}>
        <option value="refund">未发货整单退款</option><option value="return">签收商品整行退货</option>
      </select>
      {kind === 'return' && <select aria-label="退货商品" value={itemId} disabled={busy || disabled} onChange={event => { setItemId(event.target.value); setState(previous => ({ ...previous, proposal: null })) }}>
        <option value="">选择整行商品</option>{order?.items.map(item => <option key={item.sku_id} value={item.sku_id}>{item.name} × {item.quantity}</option>)}
      </select>}
      <input aria-label="售后原因" placeholder="申请原因" value={reason} disabled={busy || disabled} onChange={event => { setReason(event.target.value); setState(previous => ({ ...previous, proposal: null })) }} />
      <button type="button" onClick={prepare} disabled={busy || disabled || !reason.trim() || (kind === 'return' && !itemId)}>查看申请提案</button>
    </div>}
    {error && <p role="alert" className="text-red-600">{error}</p>}
    {state.proposal && <div data-proposal-id={state.proposal.proposal_id} className="space-y-1 rounded-xl bg-white p-3">
      <p>待确认：{state.proposal.kind === 'refund' ? '整单退款' : '整行退货'} · {state.proposal.order_id}</p>
      {state.proposal.items.map(item => <p key={item.item_id}>{item.name} × {item.quantity} · ¥{(item.amount_fen / 100).toFixed(2)}</p>)}
      <p>预计模拟金额 ¥{(state.proposal.amount_fen / 100).toFixed(2)} · 原因：{state.proposal.reason}</p>
      <p>{state.proposal.policy_id}：{state.proposal.policy}</p>
      <button type="button" disabled={busy || disabled} onClick={confirm}>确认提交此模拟申请</button>
    </div>}
    {state.receipts.map(receipt => <div key={receipt.receipt_id} data-receipt-id={receipt.receipt_id} className="rounded-xl bg-white p-3">
      <p>模拟申请已提交 · {receipt.order_id} · ¥{(receipt.amount_fen / 100).toFixed(2)}</p>
      <p>{receipt.message}</p><p className="break-all">回执：{receipt.receipt_id}</p>
    </div>)}
  </section>
}
