export interface HumanMessage {
  message_id: string
  author: 'user' | 'operator'
  kind: 'reply' | 'ask' | 'resolve' | 'close'
  content: string
  created_at: string
}
export interface HumanTicket {
  ticket_id: string
  case_id: string
  owner_id: string
  order_id: string | null
  order_summary: { order_id: string; status: string; total_fen: number; items: { name: string; quantity: number }[] } | null
  reason: string
  summary: string
  status: 'open' | 'waiting_user' | 'resolved' | 'closed'
  generation: number
  version: number
  history: { role: string; content: string }[]
  messages: HumanMessage[]
}
const root = '/api/v1/mercury'
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(root + path, { credentials: 'include', ...init })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(typeof error.detail === 'string' ? error.detail : '工单操作失败，请刷新后重试')
  }
  return response.json()
}
export const readHumanTicket = (caseId: string) => request<HumanTicket | null>(`/sessions/${encodeURIComponent(caseId)}/human-ticket`)
export const requestHumanTicket = (caseId: string, summary: string) => request<HumanTicket>(`/sessions/${encodeURIComponent(caseId)}/human-ticket`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ summary }),
})
export const replyHumanTicket = (caseId: string, ticketId: string, content: string, version: number) => request<HumanTicket>(`/sessions/${encodeURIComponent(caseId)}/human-ticket/messages`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ticket_id: ticketId, content, version }),
})
export const listOperatorTickets = (token: string) => request<HumanTicket[]>('/operator/tickets', { headers: { 'X-Internal-Token': token } })
export const actOnHumanTicket = (token: string, ticket: HumanTicket, action: 'reply' | 'ask' | 'resolve' | 'close', content: string) => request<HumanTicket>(`/operator/tickets/${encodeURIComponent(ticket.ticket_id)}/messages`, {
  method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Internal-Token': token },
  body: JSON.stringify({ action, content, version: ticket.version }),
})
