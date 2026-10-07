import { useCallback, useEffect, useRef, useState } from 'react'
import { runReceiptIntroduction } from './lib/resultIntroduction'
import { readAftersales, readAftersalesOrder, proposeAftersales, confirmAftersales, uploadAftersalesPhoto, photoUrl } from './lib/aftersales'
import type { AfterSalesState, AfterSalesOrder } from './lib/aftersales'

export function AfterSalesPanel({ caseId, orderId, selectionVersion, refreshKey, disabled, interactionVersion = 0, onCaseChange }: {
  caseId: string; orderId: string; selectionVersion: number; refreshKey: number; disabled: boolean; interactionVersion?: number; onCaseChange: () => void
}) {
  const [state, setState] = useState<AfterSalesState>({ proposal: null, receipts: [] })
  const [order, setOrder] = useState<AfterSalesOrder | null>(null)
  const [kind, setKind] = useState<'refund' | 'return' | 'quality' | 'fulfillment'>('refund')
  const problemApplication = kind === 'quality' || kind === 'fulfillment'
  const [problemQuantity, setProblemQuantity] = useState('')
  const [photos, setPhotos] = useState<string[]>([])
  const [itemId, setItemId] = useState('')
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const generation = useRef(0)
  const [introductionSource, setIntroductionSource] = useState<string | null>(null)
  const [introduction, setIntroduction] = useState('')
  const [introducing, setIntroducing] = useState(false)
  const [introductionNotice, setIntroductionNotice] = useState('')
  const introductionEpoch = useRef(0)
  const introductionController = useRef<AbortController | null>(null)
  const cancelIntroduction = useCallback((clear = false) => {
    introductionEpoch.current++
    introductionController.current?.abort()
    introductionController.current = null
    setIntroductionSource(null); setIntroducing(false); setIntroductionNotice('')
    if (clear) setIntroduction('')
  }, [])
  useEffect(() => {
    cancelIntroduction(true)
  }, [caseId, orderId, selectionVersion, refreshKey, interactionVersion, cancelIntroduction])
  useEffect(() => { if (disabled) cancelIntroduction(true) }, [disabled, cancelIntroduction])
  useEffect(() => {
    if (!introductionSource || busy || disabled) return
    const epoch = ++introductionEpoch.current
    const controller = new AbortController()
    introductionController.current = controller
    let finished = false
    setIntroducing(true); setIntroduction(''); setIntroductionNotice('')
    // Effects run after the immutable receipt has committed to the DOM.
    void runReceiptIntroduction(caseId, introductionSource, {
      signal: controller.signal,
      onDelta: (text, _messageId, replace) => { if (epoch === introductionEpoch.current && !controller.signal.aborted) setIntroduction(previous => replace ? text : previous + text) },
    }).then(result => {
      if (epoch !== introductionEpoch.current || controller.signal.aborted) return
      const status = (result as {expression_status?:string} | undefined)?.expression_status
      if (status && status !== 'completed') setIntroductionNotice('介绍未完成，申请回执已保留。')
    }).catch(() => {
      if (epoch === introductionEpoch.current && !controller.signal.aborted) setIntroductionNotice('介绍未完成，申请回执已保留。')
    }).finally(() => {
      finished = true
      if (epoch === introductionEpoch.current) {
        introductionController.current = null
        setIntroducing(false); setIntroductionSource(null)
      }
    })
    return () => { if (!finished) controller.abort() }
  }, [introductionSource, busy, disabled, caseId])

  useEffect(() => {
    const token = ++generation.current
    setState({ proposal: null, receipts: [] }); setOrder(null); setError(''); setBusy(true)
    setPhotos([]); setProblemQuantity('')
    void Promise.all([readAftersales(caseId), orderId ? readAftersalesOrder(orderId) : Promise.resolve(null)])
      .then(([next, selected]) => { if (token === generation.current) { setState(next); setOrder(selected); setItemId('') } })
      .catch((e: Error) => { if (token === generation.current) setError(e.message) })
      .finally(() => { if (token === generation.current) setBusy(false) })
    return () => { generation.current++ }
  }, [caseId, orderId, selectionVersion, refreshKey])

  async function reconcileAfterFailure(error: unknown, token: number) {
    if (token !== generation.current) return
    const message = (error as Error).message
    setError(message)
    // A lost response can follow a committed application, while a rejected
    // replacement can invalidate a proposal. Re-read; never infer or resubmit.
    try {
      const current = await readAftersales(caseId)
      if (token === generation.current) setState(current)
    } catch {
      if (token === generation.current) setError(`${message}；当前状态读取失败，请刷新后查看回执，勿重复提交。`)
    }
  }

  async function prepare() {
    if (busy || disabled || !orderId || !reason.trim() || (kind !== 'refund' && !itemId) || (problemApplication && !problemQuantity)) return
    cancelIntroduction(true)
    const token = generation.current
    setBusy(true); setError('')
    try {
      const proposal = await proposeAftersales(caseId, { kind, item_id: kind !== 'refund' ? itemId : null, reason: reason.trim(), selection_version: selectionVersion, ...(problemApplication?{problem_quantity:Number(problemQuantity),photo_ids:photos}:{}) })
      if (token === generation.current) setState(previous => ({ ...previous, proposal }))
    } catch (e) { await reconcileAfterFailure(e, token) }
    finally { if (token === generation.current) setBusy(false) }
  }
  async function confirm() {
    if (busy || disabled || !state.proposal) return
    const token = generation.current
    cancelIntroduction(true)
    const proposalId = state.proposal.proposal_id
    setBusy(true); setError('')
    try {
      const receipt = await confirmAftersales(caseId, proposalId)
      if (token === generation.current) {
        setState(previous => ({ proposal: null, receipts: [...previous.receipts.filter(item => item.receipt_id !== receipt.receipt_id), receipt] }))
        if(receipt.kind==='quality' || receipt.kind==='fulfillment') onCaseChange()
        else setIntroductionSource(receipt.receipt_id)
      }
    } catch (e) { await reconcileAfterFailure(e, token) }
    finally { if (token === generation.current) setBusy(false) }
  }
  async function upload(file: File | undefined) {
    if(!file || busy || disabled || photos.length>=3) return
    const token = generation.current
    setBusy(true); setError('')
    try {
      const result = await uploadAftersalesPhoto(caseId, selectionVersion, file)
      if(token===generation.current) { setPhotos(previous=>[...previous,result.photo_id]); setState(previous=>({...previous,proposal:null})) }
    } catch(error) { if(token===generation.current) setError(error instanceof Error ? error.message : '照片上传失败') }
    finally { if(token===generation.current) setBusy(false) }
  }
  return <section aria-label="模拟售后申请" className="space-y-2 rounded-2xl border border-black/10 p-3 text-xs">
    <p>模拟售后 · 先查看提案，再确认提交</p>
    {orderId && <div className="flex flex-wrap gap-2">
      <select aria-label="售后类型" value={kind} disabled={busy || disabled} onChange={event => { cancelIntroduction(true); setKind(event.target.value as 'refund' | 'return' | 'quality' | 'fulfillment'); setState(previous => ({ ...previous, proposal: null })) }}>
        <option value="refund">未发货整单退款</option><option value="return">签收商品无理由整行退货</option><option value="quality">签收商品质量问题登记</option><option value="fulfillment">签收订单漏送、错送或包装破损</option>
      </select>
      {kind !== 'refund' && <select aria-label="退货商品" value={itemId} disabled={busy || disabled} onChange={event => { cancelIntroduction(true); setItemId(event.target.value); setState(previous => ({ ...previous, proposal: null })) }}>
        <option value="">选择问题商品</option>{order?.items.map(item => <option key={item.sku_id} value={item.sku_id}>{item.name} × {item.quantity}</option>)}
      </select>}
      {problemApplication && <>
        <label>问题销售包装数<input aria-label="问题销售包装数" type="number" min={1} max={order?.items.find(item=>item.sku_id===itemId)?.quantity} step={1} value={problemQuantity} disabled={busy || disabled} onChange={event=>{setProblemQuantity(event.target.value);setState(previous=>({...previous,proposal:null}))}} /></label>
        <label>照片（最多3张，每张4MB）<input aria-label="质量问题照片" type="file" accept="image/jpeg,image/png,image/webp" disabled={busy || disabled || photos.length>=3} onChange={event=>{void upload(event.target.files?.[0]);event.target.value=''}} /></label>
        {photos.map(id=><img key={id} className="h-20 w-20 rounded-xl object-cover" alt="待人工核对的照片" src={photoUrl(caseId,id)} />)}
        <p>照片供人工核对。</p>
      </>}
      <input aria-label="售后原因" placeholder="申请原因" value={reason} disabled={busy || disabled} onChange={event => { cancelIntroduction(true); setReason(event.target.value); setState(previous => ({ ...previous, proposal: null })) }} />
      <button type="button" onClick={prepare} disabled={busy || disabled || !reason.trim() || (kind !== 'refund' && !itemId) || (problemApplication && !problemQuantity)}>查看申请提案</button>
    </div>}
    {error && <p role="alert" className="text-red-600">{error}</p>}
    {state.proposal && <div data-proposal-id={state.proposal.proposal_id} className="space-y-1 rounded-xl bg-white p-3">
      <p>待确认：{{refund:'整单退款',return:'无理由整行退货',quality:'质量问题登记',fulfillment:'履约异常登记'}[state.proposal.kind]} · {state.proposal.order_id}</p>
      {state.proposal.items.map(item => <p key={item.item_id}>{item.name} × {item.quantity} · ¥{(item.amount_fen / 100).toFixed(2)}</p>)}
      {state.proposal.photo_ids?.map(id=><img key={id} className="h-20 w-20 rounded-xl object-cover" alt="此提案关联的待核对照片" src={photoUrl(caseId,id)} />)}
      <p>预计模拟金额 ¥{(state.proposal.amount_fen / 100).toFixed(2)} · 原因：{state.proposal.reason}</p>
      <p>{state.proposal.policy_id}：{state.proposal.policy}</p>
      <button type="button" disabled={busy || disabled} onClick={confirm}>确认提交此模拟申请</button>
    </div>}
    {state.receipts.map(receipt => <div key={receipt.receipt_id} data-receipt-id={receipt.receipt_id} className="rounded-xl bg-white p-3">
      <p>模拟申请已提交 · {receipt.order_id} · ¥{(receipt.amount_fen / 100).toFixed(2)}</p>
      <p>{receipt.message}</p><p className="break-all">回执：{receipt.receipt_id}</p>
    </div>)}
    {introduction && <p aria-label="申请结果介绍">{introduction}</p>}
    {introducing && <p role="status">正在补充介绍… <button type="button" onClick={() => cancelIntroduction()}>停止介绍</button></p>}
    {introductionNotice && <p role="status">{introductionNotice}</p>}
  </section>
}
