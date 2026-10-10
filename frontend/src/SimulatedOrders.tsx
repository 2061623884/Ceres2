import { useEffect, useRef, useState } from 'react'
import { MomoAvatar } from './components/MomoToast'
import { ApiError, getCart, yuan, type Cart } from './lib/saleGuide'
import { confirmCheckout, getOrder, listOrders, previewCheckout, type CheckoutPreview, type SimulatedOrder } from './lib/orders'

const button = 'rounded-full bg-[#171716] px-5 py-3 text-sm font-semibold text-white disabled:opacity-40'
const panelCard =
  'rounded-[28px] border border-black/[0.06] bg-white shadow-[0_8px_28px_rgba(40,36,29,0.06)]'

function orderStatusLabel(status: string) {
  return status === 'submitted' ? '已提交' : status
}

export function SimulatedCheckout({ onClose, onCartChange, onViewOrders }: {
  onClose: () => void
  onCartChange: (cart: Cart) => void
  onViewOrders: () => void
}) {
  const [preview, setPreview] = useState<CheckoutPreview | null>(null)
  const [order, setOrder] = useState<SimulatedOrder | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const key = useRef('')
  const previewRequest = useRef(0)

  async function refresh() {
    const requestId = ++previewRequest.current
    setBusy(true)
    setPreview(null)
    setError(null)
    try {
      const current = await getCart()
      if (requestId !== previewRequest.current) return
      onCartChange(current)
      const next = await previewCheckout(current.version)
      if (requestId !== previewRequest.current) return
      key.current = crypto.randomUUID()
      setPreview(next)
    } catch (err) {
      if (requestId === previewRequest.current) setError(err instanceof Error ? err.message : '摘要加载失败')
    } finally { if (requestId === previewRequest.current) setBusy(false) }
  }
  useEffect(() => {
    void refresh()
    return () => { previewRequest.current += 1 }
  }, [])

  async function confirm() {
    if (!preview || busy) return
    setBusy(true)
    setError(null)
    try {
      const receipt = await confirmCheckout(preview.preview_id, key.current)
      setOrder(receipt.order)
      try { onCartChange(await getCart()) }
      catch { setError('订单已保存，购物车同步失败，请刷新页面') }
    } catch (err) {
      if (err instanceof ApiError && ['STALE_STATE', 'CHECKOUT_UNAVAILABLE'].includes(err.code)) setPreview(null)
      setError(err instanceof Error ? err.message : '结算失败，请重试')
    } finally { setBusy(false) }
  }
  return <section role="dialog" aria-label="模拟结算" className="absolute inset-0 z-40 flex flex-col bg-[#fcfbf8] p-5">
    <header className="mb-4 flex items-center justify-between">
      <h2 className="text-lg font-semibold">{order ? '模拟订单已保存' : '模拟结算'}</h2>
      <button disabled={busy} onClick={onClose} aria-label="关闭模拟结算">关闭</button>
    </header>
    <p className="mb-4 text-xs text-black/50">仅为模拟，不会付款或真实配送</p>
    {error && <p role="alert" className="mb-3 text-sm text-red-700">{error}</p>}
    {order ? <div className="space-y-5 break-all">
      <p>{order.order_id}</p><p className="text-xl font-semibold">{yuan(order.total_fen)}</p>
      <button className={button} onClick={onViewOrders}>查看订单</button>
    </div> : <>
      <div className="flex-1 space-y-3 overflow-y-auto">
        {preview?.items.map(item => <article key={item.sku_id} className="rounded-2xl bg-white p-4">
          <p>{item.name} × {item.quantity}</p><p className="mt-1 text-sm">{yuan(item.unit_price_fen)} / 件 · {yuan(item.line_total_fen)}</p>
        </article>)}
        {busy && !preview && <p role="status">正在读取结算摘要…</p>}
      </div>
      {preview ? <footer className="space-y-3 pt-4">
        <p className="text-xs text-black/45">购物车版本 {preview.cart_version}</p>
        <p className="text-xl font-semibold">合计 {yuan(preview.total_fen)}</p>
        <button className={`${button} w-full`} disabled={busy} onClick={confirm}>{busy ? '正在保存…' : '确认模拟结算'}</button>
      </footer> : <button className={button} disabled={busy} onClick={refresh}>刷新结算摘要</button>}
    </>}
  </section>
}

export function SimulatedOrdersScreen({ onContactOrder }: { onContactOrder: (orderId: string) => void }) {
  const [orders, setOrders] = useState<SimulatedOrder[]>([])
  const [selected, setSelected] = useState<SimulatedOrder | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  async function load() {
    setLoading(true)
    setError(null)
    try { setOrders((await listOrders()).items) }
    catch (err) { setError(err instanceof Error ? err.message : '订单加载失败') }
    finally { setLoading(false) }
  }
  useEffect(() => { void load() }, [])
  async function open(orderId: string) {
    setError(null)
    try { setSelected(await getOrder(orderId)) }
    catch (err) { setError(err instanceof Error ? err.message : '订单加载失败') }
  }

  const summaryLine = (order: SimulatedOrder) =>
    order.items.map(i => `${i.name} × ${i.quantity}`).join(' · ')

  return (
    <section className="flex h-full min-h-0 flex-col bg-[#F5F5F7] px-5 pb-4 pt-6">
      <header className={`${panelCard} mb-4 shrink-0 p-4`}>
        <h2 className="text-[20px] font-semibold tracking-[-0.03em] text-[#191817]">我的订单</h2>
      </header>

      {error && (
        <p role="alert" className="mb-3 rounded-2xl border border-red-200/80 bg-white px-4 py-3 text-sm text-red-700">
          {error}{' '}
          <button type="button" className="font-semibold underline" onClick={load}>重试</button>
        </p>
      )}

      {selected ? (
        <article
          data-order-id={selected.order_id}
          className={`${panelCard} flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-5`}
        >
          <button
            type="button"
            className="self-start text-[13px] font-medium text-black/50 transition hover:text-black/70"
            onClick={() => setSelected(null)}
          >
            ← 返回订单列表
          </button>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-[#fff0c2] px-3 py-1 text-[11px] font-semibold text-[#6b5420]">
              {orderStatusLabel(selected.status)}
            </span>
            <span className="text-[11px] text-black/40">{new Date(selected.created_at).toLocaleString()}</span>
          </div>
          <p className="break-all text-[11px] text-black/35">{selected.order_id}</p>
          <div className="space-y-3 border-t border-black/[0.05] pt-3">
            {selected.items.map(item => (
              <div key={item.sku_id} className="flex items-start justify-between gap-3 text-sm">
                <p className="min-w-0 font-medium text-[#1d1c1a]">{item.name} × {item.quantity}</p>
                <p className="shrink-0 text-black/55">{yuan(item.line_total_fen)}</p>
              </div>
            ))}
          </div>
          <p className="border-t border-black/[0.05] pt-3 text-lg font-semibold tracking-[-0.02em] text-[#191817]">
            合计 {yuan(selected.total_fen)}
          </p>
          <button
            type="button"
            className={`${button} mt-auto inline-flex w-full items-center justify-center gap-2`}
            data-contact-order-id={selected.order_id}
            onClick={() => onContactOrder(selected.order_id)}
          >
            <MomoAvatar size={22} />
            联系墨墨
          </button>
        </article>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col">
          {loading && (
            <p role="status" className="py-8 text-center text-sm text-black/45">正在读取订单…</p>
          )}
          {!loading && !error && orders.length === 0 && (
            <p className="flex flex-1 items-center justify-center text-[14px] text-black/45">暂无订单</p>
          )}
          {!loading && orders.length > 0 && (
            <div className="scrollbar-hide space-y-3 overflow-y-auto pb-2">
              {orders.map(order => (
                <button
                  key={order.order_id}
                  type="button"
                  aria-label={`查看订单 ${order.order_id}`}
                  onClick={() => open(order.order_id)}
                  className={`${panelCard} w-full p-4 text-left transition active:scale-[0.99]`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="line-clamp-2 text-[14px] font-medium leading-snug text-[#1d1c1a]">
                        {summaryLine(order)}
                      </p>
                      <p className="mt-2 break-all text-[10px] text-black/35">{order.order_id}</p>
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-2">
                      <span className="text-[15px] font-semibold tracking-[-0.02em] text-[#191817]">
                        {yuan(order.total_fen)}
                      </span>
                      <span className="rounded-full bg-[#e8f4e0] px-2.5 py-0.5 text-[10px] font-semibold text-[#2a5038]">
                        {orderStatusLabel(order.status)}
                      </span>
                    </div>
                  </div>
                  <p className="mt-3 text-[11px] font-medium text-black/40">查看订单详情 →</p>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
