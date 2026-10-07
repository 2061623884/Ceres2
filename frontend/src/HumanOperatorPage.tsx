import { useRef, useState } from 'react'
import { actOnHumanTicket, listOperatorTickets, type HumanTicket } from './lib/humanCases'
import { humanStatus } from './HumanCasePanel'
import HumanPhotos from './HumanPhotos'

export function HumanOperatorPage() {
  const [token, setToken] = useState('')
  const [tickets, setTickets] = useState<HumanTicket[]>([])
  const [selected, setSelected] = useState<HumanTicket | null>(null)
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const generation = useRef(0)
  const draftVersion = useRef(0)
  async function load() {
    const current = ++generation.current
    setBusy(true); setError('')
    try { const result = await listOperatorTickets(token); if (current === generation.current) { setTickets(result); setSelected(null) } }
    catch (err) { if (current === generation.current) setError(err instanceof Error ? err.message : '无法读取工单') }
    finally { if (current === generation.current) setBusy(false) }
  }
  async function act(action: 'reply' | 'ask' | 'resolve' | 'close') {
    if (!selected || !text.trim() || busy) return
    const current = generation.current
    const submittedDraftVersion = draftVersion.current
    setBusy(true); setError('')
    try {
      const result = await actOnHumanTicket(token, selected, action, text)
      if (current === generation.current) {
        setSelected(result); setTickets(items => items.map(item => item.ticket_id === result.ticket_id ? result : item))
        if (draftVersion.current === submittedDraftVersion) setText('')
      }
    } catch (err) { if (current === generation.current) setError(err instanceof Error ? err.message : '操作失败') }
    finally { if (current === generation.current) setBusy(false) }
  }
  return <main className="mx-auto max-w-4xl space-y-4 p-6 text-sm">
    <h1 className="text-xl font-semibold">模拟售后 · 异步人工工单</h1>
    <p>仅处理消息与工单状态。不能直接退款、绕过资格或替代用户确认。</p>
    <form onSubmit={event => { event.preventDefault(); void load() }} className="flex flex-wrap gap-2">
      <label>处理者凭据 <input type="password" autoComplete="off" value={token} onChange={event => {
        generation.current += 1; setToken(event.target.value); setTickets([]); setSelected(null); setBusy(false)
      }} className="rounded border p-2" /></label>
      <button disabled={busy || !token} className="rounded border px-4 disabled:opacity-40">读取 / 刷新工单</button>
    </form>
    <p className="text-xs text-black/50">使用已配置的内部处理者凭据，仅保留在当前页面内存中。</p>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <div className="grid gap-5 md:grid-cols-2">
      <section aria-label="工单列表" className="space-y-2">
        {tickets.map(ticket => <button key={ticket.ticket_id} disabled={busy} onClick={() => { setSelected(ticket); setText(''); draftVersion.current += 1 }} className="block w-full rounded-xl border p-3 text-left">
          <p>{ticket.summary}</p><p className="text-xs">{humanStatus[ticket.status]}</p>
        </button>)}
      </section>
      {selected && <section aria-label="工单详情" className="space-y-3 rounded-xl border p-4">
        <h2 className="font-semibold">{selected.summary}</h2>
        <p className="break-all text-xs">工单 {selected.ticket_id}<br />事项 {selected.case_id}<br />用户 {selected.owner_id}<br />订单 {selected.order_id || '尚未选择'}</p>
        <p>{humanStatus[selected.status]}</p>
        {selected.applications.map(application=><div key={application.receipt_id} className="rounded-2xl bg-[#fcfbf8] p-3"><p>模拟申请：{{quality:'质量问题登记',fulfillment:'履约异常登记',refund:'整单退款',return:'无理由退货'}[application.kind]}</p>{application.items.map(item=><p key={item.item_id}>{item.name} · {application.kind==='quality' || application.kind==='fulfillment'?'问题销售包装数':'申请包装数'} {item.quantity}</p>)}<p>{application.reason}</p><p className="text-xs text-black/50">{application.message}</p></div>)}
        <HumanPhotos ticket={selected} token={token} />
        {selected.order_summary && <div className="rounded-lg bg-black/5 p-2"><p>模拟订单 · {selected.order_summary.status} · ¥{(selected.order_summary.total_fen / 100).toFixed(2)}</p>{selected.order_summary.items.map((item, index) => <p key={index}>{item.name} × {item.quantity}</p>)}</div>}
        <h3 className="font-semibold">必要对话历史</h3>
        {selected.history.map((message, index) => <p key={index}>{message.role === 'user' ? '用户' : '墨墨'}：{message.content}</p>)}
        <h3 className="font-semibold">工单消息</h3>
        {selected.messages.map(message => <p key={message.message_id}>{message.author === 'operator' ? '处理者' : '用户'}：{message.content}</p>)}
        {['open', 'waiting_user'].includes(selected.status) && <>
          <label className="block">回复 / 处理说明<textarea maxLength={2000} value={text} onChange={event => { draftVersion.current += 1; setText(event.target.value) }} className="mt-2 w-full rounded border p-2" /></label>
          <div className="flex flex-wrap gap-2">{(['reply', 'ask', 'resolve', 'close'] as const).map((action, index) => <button key={action} disabled={busy || !text.trim()} onClick={() => void act(action)} className="rounded border px-3 py-2 disabled:opacity-40">{['回复', '追问', '解决', '关闭'][index]}</button>)}</div>
        </>}
      </section>}
    </div>
  </main>
}
