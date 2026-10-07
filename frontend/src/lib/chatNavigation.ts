import { createGuideSession, ensureIdentity } from './saleGuide'

export type ChatRole = 'keke' | 'momo'
export interface Opening {
  opening_id: string
  role: ChatRole
  prompt_displayed: boolean
  closed: boolean
  pending_request_id: string | null
  handoff?: Handoff | null
}
export interface Handoff {
  routing_request_id: string
  original_message: string
  selected_object: {kind: 'order' | 'product'; id: string} | null
}
export interface RouteDecision extends Handoff {
  status: 'ready' | 'switch'
  capability: null
  entry_judgment: {outcome: 'yes' | 'no' | 'uncertain' | 'timeout' | 'error' | 'not_attempted'; elapsed_ms: number | null; reason: string | null} | null
  target_role: ChatRole
  show_prompt: boolean
  continue_original: false
  message?: string
}
export interface RoleSwitchAction {
  type: 'switch_role'
  session_id: string
  request: {opening_id: string; target_role: ChatRole; accept: boolean; routing_request_id: null}
}
export type BeforeText = (role: ChatRole, message: string, requestId: string, selectedOrder?: string, roleSessionId?: string) => Promise<string | null>
async function api<T>(sessionId: string, path: string, method = 'GET', body?: unknown): Promise<T> {
  await ensureIdentity()
  const response = await fetch(`/api/v1/navigation/sessions/${encodeURIComponent(sessionId)}${path}`, {
    method, credentials: 'include', headers: {'Content-Type': 'application/json'},
    ...(body === undefined ? {} : {body: JSON.stringify(body)}),
  })
  const data = await response.json()
  if (!response.ok) throw new Error(data.error?.message ?? '角色导航暂时不可用')
  return data as T
}
export async function openNavigation(role: ChatRole) {
  const guide = await createGuideSession({page: role === 'keke' ? 'home' : 'orders'})
  return {sessionId: guide.session_id, opening: await api<Opening>(guide.session_id, '/opening', 'POST', {role})}
}
export const readOpening = (sid: string) => api<Opening>(sid, '/opening')
export const closeOpening = (sid: string, oid: string) => api<Opening>(sid, `/opening/${oid}`, 'DELETE')
export const routeText = (sid: string, oid: string, role: ChatRole, message: string, requestId: string, orderId?: string, roleSessionId?: string) => api<RouteDecision>(sid, '/routes', 'POST', {
  opening_id: oid, role, message, request_id: requestId, role_session_id: roleSessionId ?? null, selected_object: orderId ? {kind:'order', id:orderId} : null,
})
export const ackPrompt = (sid: string, oid: string, rid: string) => api<Opening>(sid, '/prompt-displayed', 'POST', {opening_id:oid, routing_request_id:rid})
export const chooseRole = (sid: string, oid: string, target: ChatRole, accept = true, rid?: string) => api<Opening & {handoff: Handoff | null}>(sid, '/switches', 'POST', {
  opening_id:oid, target_role:target, accept, routing_request_id:rid ?? null,
})
