import { ensureIdentity } from './saleGuide'

export interface AfterSalesProposal {
  proposal_id: string
  revision: number
  order_id: string
  kind: 'refund' | 'return'
  amount_fen: number
  reason: string
  policy_id: string
  policy: string
  items: { item_id: string; name: string; quantity: number; amount_fen: number }[]
}
export interface AfterSalesReceipt extends AfterSalesProposal {
  receipt_id: string
  application_id: string
  status: 'requested'
  message: string
}
export interface AfterSalesState {
  proposal: AfterSalesProposal | null
  receipts: AfterSalesReceipt[]
}
export interface AfterSalesOrder {
  items: { sku_id: string; name: string; quantity: number }[]
}
async function request<T>(url: string, body?: object): Promise<T> {
  await ensureIdentity()
  const response = await fetch(url, { credentials: 'include', ...(body ? {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  } : {}) })
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail?.error?.message ?? data.error?.message ?? '售后操作失败，请刷新后重试')
  }
  return response.json()
}
const base = (caseId: string) => `/api/v1/mercury/sessions/${encodeURIComponent(caseId)}`
export const readAftersales = (caseId: string) => request<AfterSalesState>(`${base(caseId)}/aftersales`)
export const readAftersalesOrder = (orderId: string) => request<AfterSalesOrder>(`/api/v1/orders/${encodeURIComponent(orderId)}`)
export const proposeAftersales = (caseId: string, body: { kind: 'refund' | 'return'; item_id: string | null; reason: string; selection_version: number }) => request<AfterSalesProposal>(`${base(caseId)}/proposals`, body)
export const confirmAftersales = (caseId: string, proposalId: string) => request<AfterSalesReceipt>(`${base(caseId)}/confirm`, {
  proposal_id: proposalId, idempotency_key: proposalId, confirmed: true,
})
