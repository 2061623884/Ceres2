/**
 * 墨墨售后 — 与 ChatScreen 同结构的奶油色 Grok 面板
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { MomoAvatar, MomoToastHero } from './components/MomoToast'
import { AfterSalesPanel } from './AfterSalesPanel'
import { HumanCasePanel } from './HumanCasePanel'
import { createMercurySession, sendMercuryTurn, readMercurySession, listMercuryOrders, selectMercuryOrder } from './lib/mercury'
import type { MercuryOrder } from './lib/mercury'

interface MercuryMsg {
  id: string
  role: 'user' | 'ai'
  text: string
  suggestions?: string[]
}

const WELCOME_MSG: MercuryMsg = {
  id: 'welcome',
  role: 'ai',
  text: '您好！我是墨墨 🍞\n可以帮您查询模拟订单、物流、售后资格和政策。查询不会提交申请；退款或退货会先展示具体提案，确认后才提交模拟申请。',
  suggestions: ['我想查看我的订单', '帮我查询物流信息', '我想查询退款资格', '我想查询退货资格'],
}

const QUICK_LABELS = ['📦 查订单', '🚚 查物流', '💰 退款', '🔄 退货']

function formatText(text: string) {
  return text.split('\n').map((line, i, arr) => (
    <span key={i}>
      {line}
      {i < arr.length - 1 && <br />}
    </span>
  ))
}

interface MercuryChatProps {
  initialOrderId?: string
  entrySequence?: number
  onOrderEntryConsumed?: (entrySequence: number) => void
  visible?: boolean
}

export function MercuryChat({ initialOrderId, entrySequence = 0, onOrderEntryConsumed, visible = true }: MercuryChatProps) {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [msgs, setMsgs] = useState<MercuryMsg[]>([WELCOME_MSG])
  const [orders, setOrders] = useState<MercuryOrder[]>([])
  const [selectedOrder, setSelectedOrder] = useState('')
  const [selectionVersion, setSelectionVersion] = useState(0)
  const [selecting, setSelecting] = useState(false)
  const [caseRefresh, setCaseRefresh] = useState(0)
  const generationRef = useRef(0)
  const [input, setInput] = useState('')
  const [typing, setTyping] = useState(false)
  const [restoring, setRestoring] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const appliedEntryRef = useRef<string | null>(null)

  useEffect(() => {
    if (visible) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [msgs, typing, visible])

  const initSession = useCallback(async (fresh = false, targetOrderId?: string) => {
    const generation = ++generationRef.current
    setTyping(false)
    setSelecting(false)
    setRestoring(true)
    setError(null)
    try {
      const saved = fresh ? null : localStorage.getItem('ceres-mercury-case')
      let restored = saved ? await readMercurySession(saved) : null
      if (generation !== generationRef.current) return
      const sid = restored?.session_id ?? await createMercurySession()
      if (generation !== generationRef.current) return
      if (!restored) restored = await readMercurySession(sid)
      if (generation !== generationRef.current) return
      if (targetOrderId && restored) {
        restored = await selectMercuryOrder(sid, targetOrderId, restored.selection_version)
      }
      if (generation !== generationRef.current) return
      const availableOrders = await listMercuryOrders()
      if (generation !== generationRef.current) return
      localStorage.setItem('ceres-mercury-case', sid)
      setSessionId(sid)
      setSelectedOrder(restored?.order_id ?? '')
      setSelectionVersion(restored?.selection_version ?? 0)
      setMsgs(restored?.messages.length ? restored.messages.map((message, index) => ({
        id: `restored-${index}`, role: message.role === 'assistant' ? 'ai' : 'user', text: message.content,
      })) : [WELCOME_MSG])
      setOrders(availableOrders)
      return true
    } catch (error) {
      if (generation !== generationRef.current) return
      setSessionId(null)
      setSelectedOrder('')
      setOrders([])
      setError(error instanceof Error ? error.message : '会话连接失败，请稍后再试')
    } finally {
      if (generation === generationRef.current) setRestoring(false)
    }
  }, [])

  useEffect(() => {
    if (!visible) return
    const entry = initialOrderId ? `${entrySequence}:${initialOrderId}` : null
    const target = entry !== appliedEntryRef.current ? initialOrderId : undefined
    void initSession(false, target).then(restored => {
      if (restored) {
        appliedEntryRef.current = entry
        if (target) onOrderEntryConsumed?.(entrySequence)
      }
    })
    return () => { generationRef.current += 1 }
  }, [initSession, initialOrderId, entrySequence, onOrderEntryConsumed, visible])

  const send = useCallback(
    async (text: string) => {
      if (!text.trim() || !sessionId || typing || restoring || selecting) return
      const generation = generationRef.current
      const trimmed = text.trim()
      setMsgs((p) => [...p, { id: `u-${Date.now()}`, role: 'user', text: trimmed }])
      setInput('')
      setTyping(true)
      setError(null)

      const assistantId = `a-${Date.now()}`
      let assistantText = ''
      setMsgs((p) => [...p, { id: assistantId, role: 'ai', text: '' }])

      try {
        await sendMercuryTurn(sessionId, trimmed, {
          onAnswerDelta: (chunk) => {
            if (generation !== generationRef.current) return
            assistantText += chunk
            setMsgs((p) => p.map((m) => (m.id === assistantId ? { ...m, text: assistantText } : m)))
          },
          onCompleted: (finalText) => {
            if (generation !== generationRef.current) return
            setCaseRefresh(value => value + 1)
            setMsgs((p) =>
              p.map((m) => (m.id === assistantId ? { ...m, text: finalText || assistantText } : m)),
            )
          },
          onError: (err) => {
            if (generation !== generationRef.current) return
            setError(err)
            setMsgs((p) =>
              p.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      text: m.text.trim()
                        ? m.text
                        : '抱歉，没有收到回复，请稍后再试。',
                    }
                  : m,
              ),
            )
          },
        })
      } catch (e) {
        if (generation !== generationRef.current) return
        const message = e instanceof Error ? e.message : '发送失败'
        setError(message)
        setMsgs((p) =>
          p.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  text: m.text.trim()
                    ? m.text
                    : '抱歉，没有收到回复，请稍后再试。',
                }
              : m,
          ),
        )
      } finally {
        if (generation === generationRef.current) setTyping(false)
      }
    },
    [sessionId, typing, restoring, selecting],
  )

  async function handleNewChat() {
    setMsgs([WELCOME_MSG])
    setSessionId(null)
    await initSession(true)
  }

  async function chooseOrder(orderId: string) {
    if (!sessionId || !orderId || selecting || typing || restoring) return
    const generation = generationRef.current
    setSelecting(true)
    setError(null)
    try {
      const selected = await selectMercuryOrder(sessionId, orderId, selectionVersion)
      if (generation !== generationRef.current) return
      setSelectedOrder(selected.order_id ?? '')
      setSelectionVersion(selected.selection_version)
      setCaseRefresh(value => value + 1)
    } catch (error) {
      if (generation !== generationRef.current) return
      setError(error instanceof Error ? error.message : '选择订单失败')
    } finally {
      if (generation === generationRef.current) setSelecting(false)
    }
  }

  if (!visible) return null

  const activeOrder = orders.find(order => order.order_id === selectedOrder)
  const showWelcomeHero = msgs.length === 1 && msgs[0].id === 'welcome'

  return (
    <section
      className="chat-panel-enter relative flex h-[min(71vh,650px)] min-h-[500px] flex-col overflow-hidden rounded-t-[38px] bg-[#fcfbf8] font-sans shadow-[0_-20px_60px_rgba(40,36,29,0.12)]"
    >
      <div className="flex justify-center bg-[#f7f5f0] pt-3 pb-1.5" aria-hidden="true">
        <span className="h-1 w-10 rounded-full bg-black/[.12]" />
      </div>
      <div className="flex flex-shrink-0 items-center gap-3 bg-[#f7f5f0] px-6 pt-2 pb-5">
        <MomoAvatar size={40} animated />
        <div>
          <p className="text-[15px] font-semibold tracking-[-0.04em] text-[#191817]">墨墨</p>
          {typing && <p className="text-[10px] text-black/40">墨墨正在输入…</p>}
        </div>
        <button
          type="button"
          onClick={handleNewChat}
          className="ml-auto grid h-9 w-9 place-items-center rounded-full bg-white/70 text-black/48 transition hover:bg-white active:scale-95"
          aria-label="发起新对话"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </button>
      </div>

      <div className="bg-[#f7f5f0] px-6 pb-3">
        <label className="text-xs text-black/50" htmlFor="mercury-order">模拟订单 · 查询与售后</label>
        <select id="mercury-order" aria-label="选择模拟订单" value={selectedOrder}
          disabled={restoring || typing || selecting} onChange={(event) => chooseOrder(event.target.value)}
          className="mt-1 block w-full rounded-xl bg-white px-3 py-2 text-xs">
          <option value="">{orders.length ? '请选择要查询的模拟订单' : '当前身份暂无模拟订单'}</option>
          {orders.map((order) => <option key={order.order_id} value={order.order_id}>
            {order.order_id} · {order.status_text} · ¥{order.total}
          </option>)}
        </select>
        {activeOrder && <p data-selected-order-id={activeOrder.order_id} className="mt-2 break-all text-xs text-black/50">
          {activeOrder.products.join(' · ')} · {activeOrder.store_id ?? '门店未知'} · 订单版本 {activeOrder.version}
        </p>}
      </div>

      <div className="scrollbar-hide flex-1 space-y-5 overflow-y-auto px-6 py-5">
        {restoring && <p className="text-center text-sm text-black/40">正在连接墨墨…</p>}
        {error && <p className="text-center text-xs text-red-600">{error}</p>}

        {sessionId && !restoring && <AfterSalesPanel caseId={sessionId} orderId={selectedOrder} selectionVersion={selectionVersion} refreshKey={caseRefresh} disabled={typing || selecting} />}

        {sessionId && !restoring && <HumanCasePanel key={sessionId} caseId={sessionId} refreshKey={caseRefresh} />}

        {showWelcomeHero && (
          <div className="flex flex-col items-center gap-3 pb-2">
            <MomoToastHero size={120} mood="happy" animated />
          </div>
        )}

        {msgs.map((msg) => (
          <div key={msg.id} className={`flex items-end gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            {msg.role === 'ai' && <MomoAvatar size={26} />}
            <div className={`flex max-w-[82%] flex-col gap-2.5 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              {msg.text ? (
                <div
                  className="px-4 py-3 text-[13px] font-medium leading-[1.7] tracking-[-0.015em]"
                  style={{
                    borderRadius: msg.role === 'user' ? '24px 24px 8px 24px' : '24px 24px 24px 8px',
                    background: msg.role === 'user' ? '#171716' : '#f2f1ed',
                    color: msg.role === 'user' ? '#fff' : '#292825',
                  }}
                >
                  {formatText(msg.text)}
                </div>
              ) : msg.role === 'ai' && typing ? (
                <div
                  className="ai-loading-bubble px-4 py-3 text-[13px] font-medium leading-[1.7] tracking-[-0.015em]"
                  style={{
                    borderRadius: '24px 24px 24px 8px',
                    background: '#f2f1ed',
                    color: '#292825',
                  }}
                >
                  <span className="ai-loading-ellipsis" aria-label="墨墨正在输入">
                    <span className="ai-loading-ellipsis__dot" aria-hidden="true">.</span>
                    <span className="ai-loading-ellipsis__dot" aria-hidden="true">.</span>
                    <span className="ai-loading-ellipsis__dot" aria-hidden="true">.</span>
                  </span>
                </div>
              ) : null}
              {msg.suggestions && msg.role === 'ai' && !typing && (
                <div className="flex w-full flex-col gap-1.5">
                  {msg.suggestions.map((s, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => send(s)}
                      className="rounded-full bg-[#f5f4f0] px-4 py-2.5 text-left text-[12px] font-medium text-black/55 transition hover:bg-[#eceae4] active:scale-[.98]"
                    >
                      <span className="mr-2 text-[10px] font-semibold text-[#d79b58]">✦</span>
                      {QUICK_LABELS[i] ?? s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="relative flex-shrink-0 bg-[#f7f5f0]/75 px-5 pb-4 pt-2">
        <div className="flex items-center gap-2 rounded-[28px] bg-white/85 px-4 py-2.5 backdrop-blur-sm">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') send(input)
            }}
            placeholder="问问墨墨吧…"
            disabled={restoring || selecting}
            className="min-w-0 flex-1 bg-transparent text-[13px] font-medium text-[#1d1c1a] outline-none placeholder:text-black/30"
          />
          <button
            type="button"
            onClick={() => send(input)}
            disabled={!input.trim() || !sessionId || typing || restoring || selecting}
            className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full transition-all active:scale-90 ${
              input.trim() && !typing && !restoring ? 'bg-[#171716]' : 'bg-[#eeece7]'
            }`}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="white">
              <path d="M2 21L23 12 2 3v7l15 2-15 2z" />
            </svg>
          </button>
        </div>
      </div>
    </section>
  )
}
