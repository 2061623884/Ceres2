import { ApiError, ensureIdentity } from './saleGuide'

export interface OrderItem {
  sku_id: string
  name: string
  quantity: number
  unit_price_fen: number
  line_total_fen: number
  image_path: string | null
  offer_version: number | null
  returnable: boolean | null
  return_policy_source: string
}
export interface CheckoutPreview {
  preview_id: string
  cart_version: number
  store_id: string
  items: OrderItem[]
  total_fen: number
  business_data_mode: 'demo'
}
export interface SimulatedOrder {
  order_id: string
  status: string
  version: number
  store_id: string | null
  items: OrderItem[]
  total_fen: number
  business_data_mode: 'demo'
  created_at: string
  delivered_at: string | null
}
export interface CheckoutReceipt {
  receipt_id: string
  order: SimulatedOrder
  cart_version: number
}
async function request<T>(path: string, body?: object): Promise<T> {
  await ensureIdentity()
  const response = await fetch(`/api/v1${path}`, {
    credentials: 'include',
    method: body ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  const result = await response.json()
  if (!response.ok) throw new ApiError(result.error?.message || '订单请求失败', result.error?.code || 'UNKNOWN')
  return result as T
}
export const previewCheckout = (version: number) => request<CheckoutPreview>('/checkout/preview', { expected_cart_version: version })
export const confirmCheckout = (previewId: string, key: string) => request<CheckoutReceipt>('/checkout/confirm', { preview_id: previewId, idempotency_key: key, confirmed: true })
export const listOrders = () => request<{ items: SimulatedOrder[] }>('/orders')
export const getOrder = (orderId: string) => request<SimulatedOrder>(`/orders/${encodeURIComponent(orderId)}`)
