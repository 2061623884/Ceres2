import { ensureIdentity } from './saleGuide'

export interface AfterSalesProposal {
  proposal_id: string
  revision: number
  order_id: string
  kind: 'refund' | 'return' | 'quality' | 'fulfillment'
  problem_quantity?: number
  photo_ids?: string[]
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
export const proposeAftersales = (caseId: string, body: { kind: 'refund' | 'return' | 'quality' | 'fulfillment'; item_id: string | null; reason: string; selection_version: number; problem_quantity?: number; photo_ids?: string[] }) => request<AfterSalesProposal>(`${base(caseId)}/proposals`, body)
export const uploadAftersalesPhoto = async(caseId: string, selectionVersion: number, file: File) => {
  const bytes = new Uint8Array(await file.arrayBuffer())
  let binary = ''
  for (let i=0;i<bytes.length;i+=8192) binary += String.fromCharCode(...bytes.subarray(i,i+8192))
  return request<{photo_id:string;order_id:string}>(`${base(caseId)}/photos`, { content_type:file.type, data_base64:btoa(binary), selection_version:selectionVersion })
}
export const photoUrl = (caseId: string, photoId: string) => `${base(caseId)}/photos/${encodeURIComponent(photoId)}`
export const confirmAftersales = (caseId: string, proposalId: string) => request<AfterSalesReceipt>(`${base(caseId)}/confirm`, {
  proposal_id: proposalId, idempotency_key: proposalId, confirmed: true,
})
