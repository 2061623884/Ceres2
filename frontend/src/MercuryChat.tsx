import type { BeforeText, Handoff } from './lib/chatNavigation'
import { useState, useEffect, useRef, useCallback, type ReactNode } from 'react'
import { MomoAvatar } from './components/MomoToast'
import { AfterSalesPanel } from './AfterSalesPanel'
import { HumanCasePanel } from './HumanCasePanel'
import { KekeAvatar } from './components/KekeAvatar'
import { RoleChatFrame, composerKekeGuideChipClass, composerToolChipClass, type ComposerPlusAction, type RoleChatNavigationProps } from './RoleChatFrame'
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
  text: '您好！我是墨墨 🍞\n一般政策无需选择订单。我也可以帮您查询模拟订单、物流和售后资格。查询不会提交申请；退款或退货会先展示具体提案，确认后才提交模拟申请。',
}

type MercurySheet = 'order' | 'aftersales' | 'human' | null

function formatText(text: string) {
  return text.split('\n').map((line, i, arr) => (
    <span key={i}>
      {line}
      {i < arr.length - 1 && <br />}
    </span>
  ))
}

function MercuryFloatingSheet({ children, onClose }: { children: ReactNode; onClose: () => void }) {
  return (
    <div className="guide-sheet-enter absolute inset-x-0 bottom-full z-10 mb-2">
      <div className="relative flex max-h-[min(52vh,420px)] flex-col overflow-hidden rounded-[24px] bg-[#fcfbf8] shadow-lg">
        <button
          type="button"
          onClick={onClose}
          aria-label="关闭"
          className="absolute right-3 top-3 z-10 grid h-[22px] w-[22px] place-items-center rounded-full bg-black/[0.06] text-black/40"
        >
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
        <div className="guide-sheet-scroll overflow-y-auto p-4 pt-10">{children}</div>
      </div>
    </div>
  )
}

interface MercuryChatProps {
  beforeText?: BeforeText
  handoff?: Handoff | null
  onHandoffDone?: () => void
  initialOrderId?: string
  entrySequence?: number
  onOrderEntryConsumed?: (entrySequence: number) => void
  visible?: boolean
  navigation?: RoleChatNavigationProps
}

export function MercuryChat({
  initialOrderId,
  entrySequence = 0,
  onOrderEntryConsumed,
  visible = true,
  beforeText,
  handoff,
  onHandoffDone,
  navigation,
}: MercuryChatProps) {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [msgs, setMsgs] = useState<MercuryMsg[]>([WELCOME_MSG])
  const [orders, setOrders] = useState<MercuryOrder[]>([])
  const [selectedOrder, setSelectedOrder] = useState('')
  const [selectionVersion, setSelectionVersion] = useState(0)
  const [selecting, setSelecting] = useState(false)
  const [caseRefresh, setCaseRefresh] = useState(0)
  const [openSheet, setOpenSheet] = useState<MercurySheet>(null)
  const generationRef = useRef(0)
  const readyGenerationRef = useRef<number | null>(null)
  const [interactionVersion, setInteractionVersion] = useState(0)
  const [input, setInput] = useState('')
  const [typing, setTyping] = useState(false)
  const [restoring, setRestoring] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const appliedEntryRef = useRef<string | null>(null)
  const requestedEntry = initialOrderId ? `${entrySequence}:${initialOrderId}` : null
  const initializationEntry = requestedEntry ?? appliedEntryRef.current

  useEffect(() => {
    if (visible) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [msgs, typing, visible])

  const initSession = useCallback(async (fresh = false, targetOrderId?: string, orderEntry?: string) => {
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
      if (targetOrderId && restored && restored.order_id !== targetOrderId) {
        restored = await selectMercuryOrder(sid, targetOrderId, restored.selection_version)
      }
      if (generation !== generationRef.current) return
      const availableOrders = await listMercuryOrders()
      if (generation !== generationRef.current) return
      localStorage.setItem('ceres-mercury-case', sid)
      setSessionId(sid)
      setSelectedOrder(restored?.order_id ?? '')
      setSelectionVersion(restored?.selection_version ?? 0)
      setMsgs(
        restored?.messages.length
          ? restored.messages.map((message, index) => ({
              id: `restored-${index}`,
              role: message.role === 'assistant' ? 'ai' : 'user',
              text: message.content,
            }))
          : [WELCOME_MSG],
      )
      setOrders(availableOrders)
      if (orderEntry) appliedEntryRef.current = orderEntry
      readyGenerationRef.current = generation
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
    const target = initializationEntry !== appliedEntryRef.current ? initialOrderId : undefined
    void initSession(false, target, requestedEntry ?? undefined).then(restored => {
      if (restored && target) onOrderEntryConsumed?.(entrySequence)
    })
    return () => {
      generationRef.current += 1
    }
  }, [initSession, initializationEntry, initialOrderId, entrySequence, onOrderEntryConsumed, requestedEntry, visible])

  const send = useCallback(
    async (text: string, routedRequestId?: string) => {
      if (!text.trim() || !sessionId || typing || restoring || selecting || readyGenerationRef.current !== generationRef.current) return
      setInteractionVersion(value => value + 1)
      const generation = generationRef.current
      const trimmed = text.trim()
      const requestId = routedRequestId ?? crypto.randomUUID()
      const routeId =
        routedRequestId ?? (beforeText ? await beforeText('momo', trimmed, requestId, selectedOrder, sessionId) : requestId)
      if (!routeId || generation !== generationRef.current) return
      setMsgs(p => [...p, { id: `u-${Date.now()}`, role: 'user', text: trimmed }])
      setInput('')
      setTyping(true)
      setError(null)

      const assistantId = `a-${Date.now()}`
      let assistantText = ''
      setMsgs(p => [...p, { id: assistantId, role: 'ai', text: '' }])

      try {
        await sendMercuryTurn(
          sessionId,
          trimmed,
          {
            onAnswerDelta: chunk => {
              if (generation !== generationRef.current) return
              assistantText += chunk
              setMsgs(p => p.map(m => (m.id === assistantId ? { ...m, text: assistantText } : m)))
            },
            onCompleted: finalText => {
              if (generation !== generationRef.current) return
              setCaseRefresh(value => value + 1)
              setMsgs(p => p.map(m => (m.id === assistantId ? { ...m, text: finalText || assistantText } : m)))
            },
            onError: err => {
              if (generation !== generationRef.current) return
              setError(err)
              setMsgs(p =>
                p.map(m =>
                  m.id === assistantId
                    ? { ...m, text: m.text.trim() ? m.text : '抱歉，没有收到回复，请稍后再试。' }
                    : m,
                ),
              )
            },
          },
          routeId,
        )
      } catch (e) {
        if (generation !== generationRef.current) return
        const message = e instanceof Error ? e.message : '发送失败'
        setError(message)
        setMsgs(p =>
          p.map(m =>
            m.id === assistantId ? { ...m, text: m.text.trim() ? m.text : '抱歉，没有收到回复，请稍后再试。' } : m,
          ),
        )
      } finally {
        if (generation === generationRef.current) setTyping(false)
      }
    },
    [sessionId, typing, restoring, selecting, selectedOrder, beforeText],
  )

  const resumedHandoff = useRef<string | null>(null)
  useEffect(() => {
    if (!handoff) {
      resumedHandoff.current = null
      return
    }
    if (
      !visible ||
      restoring ||
      !sessionId ||
      selecting ||
      readyGenerationRef.current !== generationRef.current ||
      resumedHandoff.current === handoff.routing_request_id
    )
      return
    resumedHandoff.current = handoff.routing_request_id
    void send(handoff.original_message, handoff.routing_request_id).finally(() => onHandoffDone?.())
  }, [handoff, visible, restoring, sessionId, selecting, send, onHandoffDone])

  async function handleNewChat() {
    setInteractionVersion(value => value + 1)
    setMsgs([WELCOME_MSG])
    setSessionId(null)
    setOpenSheet(null)
    await initSession(true)
  }

  async function chooseOrder(orderId: string) {
    if (!sessionId || selecting || typing || restoring) return
    setInteractionVersion(value => value + 1)
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

  const momoPlusActions: ComposerPlusAction[] = [
    {
      label: '发起新对话',
      onClick: () => void handleNewChat(),
      ariaLabel: '发起新对话',
    },
  ]

  return (
    <RoleChatFrame
      activeRole="momo"
      agentAvatar={<MomoAvatar size={40} animated />}
      agentName="墨墨"
      statusLine={typing ? <p>墨墨正在输入…</p> : undefined}
      navigation={navigation}
      bottomRef={bottomRef}
      composerPlusActions={momoPlusActions}
      toolRow={
        <div className="scrollbar-hide mb-2 flex gap-2 overflow-x-auto pb-0.5">
          <button type="button" onClick={() => setOpenSheet(prev => (prev === 'order' ? null : 'order'))} className={composerToolChipClass(openSheet === 'order')}>
            当前订单
          </button>
          <button type="button" onClick={() => setOpenSheet(prev => (prev === 'aftersales' ? null : 'aftersales'))} className={composerToolChipClass(openSheet === 'aftersales')}>
            售后申请
          </button>
          <button type="button" onClick={() => setOpenSheet(prev => (prev === 'human' ? null : 'human'))} className={composerToolChipClass(openSheet === 'human')}>
            人工工单
          </button>
          {navigation && (
            <button
              type="button"
              aria-label="继续选购，联系可可"
              disabled={navigation.navigationBusy || !navigation.navigationReady}
              onClick={() => navigation.onSwitchRole('keke')}
              className={composerKekeGuideChipClass()}
            >
              <KekeAvatar size={20} />
              继续选购
            </button>
          )}
        </div>
      }
      sheetSlot={
        openSheet ? (
          <MercuryFloatingSheet onClose={() => setOpenSheet(null)}>
            {openSheet === 'order' && (
              <div>
                <h3 className="mb-2 text-sm font-semibold text-[#191817]">模拟订单 · 查询与售后</h3>
                <label className="text-xs text-black/50" htmlFor="mercury-order">选择订单</label>
                <select
                  id="mercury-order"
                  aria-label="选择模拟订单"
                  value={selectedOrder}
                  disabled={restoring || typing || selecting}
                  onChange={event => void chooseOrder(event.target.value)}
                  className="mt-1 block w-full rounded-xl bg-white px-3 py-2 text-xs"
                >
                  <option value="">{orders.length ? '请选择要查询的模拟订单' : '当前身份暂无模拟订单'}</option>
                  {orders.map(order => (
                    <option key={order.order_id} value={order.order_id}>
                      {order.order_id} · {order.status_text} · ¥{order.total}
                    </option>
                  ))}
                </select>
                {activeOrder && (
                  <p data-selected-order-id={activeOrder.order_id} className="mt-2 break-all text-xs text-black/50">
                    {activeOrder.products.join(' · ')} · {activeOrder.store_id ?? '门店未知'} · 订单版本 {activeOrder.version}
                  </p>
                )}
              </div>
            )}
            {openSheet === 'aftersales' && sessionId && !restoring && (
              <AfterSalesPanel
                caseId={sessionId}
                orderId={selectedOrder}
                selectionVersion={selectionVersion}
                refreshKey={caseRefresh}
                disabled={typing || selecting}
                interactionVersion={interactionVersion}
              />
            )}
            {openSheet === 'human' && sessionId && !restoring && (
              <HumanCasePanel key={sessionId} caseId={sessionId} refreshKey={caseRefresh} variant="sheet" />
            )}
          </MercuryFloatingSheet>
        ) : null
      }
      composer={{
        value: input,
        onChange: setInput,
        onSend: () => void send(input),
        placeholder: '问问墨墨吧…',
        disabled: restoring || selecting,
        sendDisabled: !input.trim() || !sessionId || typing || restoring || selecting,
      }}
    >
      {restoring && <p className="text-center text-sm text-black/40">正在连接墨墨…</p>}
      {error && <p className="text-center text-xs text-red-600">{error}</p>}

      {msgs.map(msg => (
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
                    key={`${msg.id}-${i}`}
                    type="button"
                    onClick={() => void send(s)}
                    className="rounded-full bg-[#f5f4f0] px-4 py-2.5 text-left text-[12px] font-medium text-black/55 transition hover:bg-[#eceae4] active:scale-[.98]"
                  >
                    <span className="mr-2 text-[10px] font-semibold text-[#d79b58]">✦</span>
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </RoleChatFrame>
  )
}
