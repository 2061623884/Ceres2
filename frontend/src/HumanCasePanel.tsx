import { useEffect, useRef, useState } from 'react'
import { readHumanTicket, requestHumanTicket, replyHumanTicket, type HumanTicket } from './lib/humanCases'
import HumanPhotos from './HumanPhotos'

export const humanStatus = { open: '等待人工处理', waiting_user: '等待您补充信息', resolved: '已解决', closed: '已关闭' }
const button = 'rounded-xl border border-black/15 px-3 py-2 text-xs disabled:opacity-40'

export function HumanCasePanel({ caseId, refreshKey = 0 }: { caseId: string; refreshKey?: number }) {
  const [ticket, setTicket] = useState<HumanTicket | null>(null)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const generation = useRef(0)
  const draftVersion = useRef(0)
  async function refresh() {
    const current = ++generation.current
    setBusy(true)
    setError('')
    try { const result = await readHumanTicket(caseId); if (generation.current === current) setTicket(result) }
    catch (err) { if (generation.current === current) setError(err instanceof Error ? err.message : '工单读取失败') }
    finally { if (generation.current === current) setBusy(false) }
  }
  useEffect(() => {
    setTicket(null); setText(''); draftVersion.current += 1
  }, [caseId])
  useEffect(() => {
    void refresh()
    return () => { generation.current += 1 }
  }, [caseId, refreshKey])
  async function submit() {
    if (!text.trim() || busy) return
    const current = generation.current
    const submittedDraftVersion = draftVersion.current
    setBusy(true); setError('')
    try {
      const result = ticket && ['open', 'waiting_user'].includes(ticket.status)
        ? await replyHumanTicket(caseId, ticket.ticket_id, text, ticket.version)
        : await requestHumanTicket(caseId, text)
      if (generation.current === current) {
        setTicket(result)
        if (draftVersion.current === submittedDraftVersion) setText('')
      }
    } catch (err) { if (generation.current === current) setError(err instanceof Error ? err.message : '工单提交失败') }
    finally { if (generation.current === current) setBusy(false) }
  }
  return <details className="rounded-2xl border border-black/10 bg-white/70 p-3 text-sm">
    <summary className="cursor-pointer">异步人工工单{ticket ? ` · ${humanStatus[ticket.status]}` : ''}</summary>
    <p className="my-2 text-xs text-black/55">模拟售后，非实时客服。人工处理也不会直接退款或代替您的确认。</p>
    {error && <p role="alert" className="text-xs text-red-700">{error}</p>}
    {ticket && <div className="space-y-2">
      <p>{ticket.summary}</p>
      <p className="break-all text-xs text-black/50">工单 {ticket.ticket_id}</p>
      <HumanPhotos ticket={ticket} />
      {ticket.messages.map(message => <p key={message.message_id} className="rounded-lg bg-black/5 p-2"><span className="text-xs text-black/50">{message.author === 'operator' ? '人工处理者' : '您'}：</span>{message.content}</p>)}
    </div>}
    <label className="mt-3 block text-xs">{ticket && ['open', 'waiting_user'].includes(ticket.status) ? '补充信息' : '描述需要人工帮助的问题'}
      <textarea value={text} onChange={event => { draftVersion.current += 1; setText(event.target.value) }} maxLength={2000} className="mt-1 w-full rounded-lg border border-black/15 p-2" />
    </label>
    <div className="mt-2 flex gap-2">
      <button className={button} disabled={busy || !text.trim()} onClick={() => void submit()}>{ticket && ['open', 'waiting_user'].includes(ticket.status) ? '发送补充信息' : '请求人工处理'}</button>
      <button className={button} disabled={busy} onClick={() => void refresh()}>刷新进度</button>
    </div>
  </details>
}
