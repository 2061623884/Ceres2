import { useEffect, useRef, useState } from 'react'
import { ApiError, getCart, yuan, type Cart } from './lib/saleGuide'
import { advanceDemoOrder, confirmCheckout, getOrder, listOrders, previewCheckout, type CheckoutPreview, type SimulatedOrder } from './lib/orders'

const button = 'rounded-full bg-[#171716] px-5 py-3 text-sm font-semibold text-white disabled:opacity-40'

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
  const [advancing, setAdvancing] = useState(false)
  const viewGeneration = useRef(0)
  const [error, setError] = useState<string | null>(null)
  async function load() {
    setLoading(true)
    setError(null)
    try { setOrders((await listOrders()).items) }
    catch (err) { setError(err instanceof Error ? err.message : '订单加载失败') }
    finally { setLoading(false) }
  }
  useEffect(() => { void load(); return () => { viewGeneration.current += 1 } }, [])
  async function open(orderId: string) {
    const generation = ++viewGeneration.current
    setError(null)
    try {
      const order = await getOrder(orderId)
      if (generation === viewGeneration.current) setSelected(order)
    }
    catch (err) { if (generation === viewGeneration.current) setError(err instanceof Error ? err.message : '订单加载失败') }
  }
  async function advance(status: 'shipped' | 'delivered') {
    if (!selected || advancing) return
    const generation = viewGeneration.current
    const orderId = selected.order_id
    setAdvancing(true); setError(null)
    try {
      const current = await advanceDemoOrder(selected, status)
      setOrders(rows => rows.map(row => row.order_id === current.order_id ? current : row))
      if (generation === viewGeneration.current) setSelected(shown => shown?.order_id === orderId ? current : shown)
    } catch (error) {
      if (generation === viewGeneration.current) {
        setError(error instanceof Error ? error.message : '模拟状态更新失败')
        setSelected(shown => shown?.order_id === orderId ? null : shown)
      }
    } finally { setAdvancing(false) }
  }
  return <section className="flex h-full flex-col bg-[#fcfbf8] p-5">
    <h2 className="mb-3 text-2xl font-semibold">我的模拟订单</h2>
    <p className="mb-4 text-xs text-black/45">模拟数据，不代表真实支付或配送</p>
    {error && <p role="alert" className="text-sm text-red-700">{error} <button onClick={load}>重试</button></p>}
    {selected ? <article data-order-id={selected.order_id} className="space-y-4 overflow-y-auto rounded-3xl bg-[#f7f6f2] p-4">
      <button onClick={() => { viewGeneration.current += 1; setSelected(null); setError(null) }}>← 返回订单列表</button>
      <p className="break-all font-semibold">{selected.order_id}</p>
      <p className="text-xs">{new Date(selected.created_at).toLocaleString()} · 模拟状态：{selected.status === 'submitted' ? '已提交' : selected.status}</p>
      {selected.items.map(item => <div key={item.sku_id} className="text-sm"><p>{item.name} × {item.quantity}</p><p>{yuan(item.unit_price_fen)} / 件 · {yuan(item.line_total_fen)}</p></div>)}
      <p className="text-lg font-semibold">合计 {yuan(selected.total_fen)}</p>
      {['submitted','shipped'].includes(selected.status) && <button className={button} disabled={advancing} onClick={()=>void advance(selected.status === 'submitted' ? 'shipped' : 'delivered')}>{selected.status === 'submitted' ? '模拟推进至配送中' : '模拟签收'}</button>}
      <button className={button} data-contact-order-id={selected.order_id} onClick={() => onContactOrder(selected.order_id)}>联系墨墨</button>
    </article> : <div className="space-y-3 overflow-y-auto">
      {loading && <p role="status">正在读取订单…</p>}
      {!loading && !error && orders.length === 0 && <p>还没有模拟订单。可从货架购物车独立结算。</p>}
      {orders.map(order => <button key={order.order_id} aria-label={`查看订单 ${order.order_id}`} onClick={() => open(order.order_id)} className="w-full space-y-2 rounded-3xl bg-[#f7f6f2] p-4 text-left">
        <p className="break-all text-sm font-semibold">{order.order_id}</p>
        <p className="text-xs">{order.items.map(i => `${i.name} × ${i.quantity}`).join(' · ')}</p>
        <p>{yuan(order.total_fen)}</p><p className="text-xs text-black/45">查看订单详情 →</p>
      </button>)}
    </div>}
  </section>
}
