import type {RoleSwitchAction} from './chatNavigation';
import type {GuideQuestion} from './productQuestions';
const API_BASE = '';

export interface BootstrapResponse {
  owner_id: string;
  store_id: string;
  delivery_zone_id: string;
  llm_mode: string;
  business_data_mode: string;
  demo_notice?: string;
}

let identityPromise: Promise<BootstrapResponse> | null = null;
let bootstrapCache: BootstrapResponse | null = null;

export class ApiError extends Error {
  code: string;
  taskId?: string;
  stateVersion?: number;
  sessionVersion?: number;
  retryable?: boolean;

  constructor(
    message: string,
    code: string,
    opts?: {
      taskId?: string;
      stateVersion?: number;
      sessionVersion?: number;
      retryable?: boolean;
    },
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.taskId = opts?.taskId;
    this.stateVersion = opts?.stateVersion;
    this.sessionVersion = opts?.sessionVersion;
    this.retryable = opts?.retryable;
  }
}

export function ensureIdentity(): Promise<BootstrapResponse> {
  if (typeof window === 'undefined') {
    return Promise.resolve({
      owner_id: '',
      store_id: 'store-demo-01',
      delivery_zone_id: 'zone-default',
      llm_mode: 'live',
      business_data_mode: 'demo',
    });
  }
  if (identityPromise) return identityPromise;
  identityPromise = fetch(`${API_BASE}/api/v1/bootstrap`, {
    credentials: 'include',
  })
    .then(async (res) => {
      if (!res.ok) throw new Error('bootstrap failed');
      const body = (await res.json()) as BootstrapResponse;
      bootstrapCache = body;
      return body;
    })
    .catch((err) => {
      identityPromise = null;
      throw err;
    });
  return identityPromise;
}

export function getBootstrapContext(): BootstrapResponse | null {
  return bootstrapCache;
}

export function progressPhaseLabel(phase: string | undefined | null): string {
  switch (phase) {
    case 'understanding':
      return '可可正在理解你的需求…';
    case 'retrieve':
      return '可可正在查阅商品信息…';
    case 'conditions_updated':
      return '条件已更新，正在按新条件核对…';
    case 'speaking':
      return '';
    case 'validate':
      return '可可正在整理采购清单…';
    default:
      return phase ? `可可正在处理（${phase}）…` : '可可正在思考…';
  }
}

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const isBootstrap = path.startsWith('/api/v1/bootstrap');
  const isPublicCatalog =
    path.startsWith('/api/v1/categories') ||
    path.startsWith('/api/v1/products') ||
    path.startsWith('/api/v1/search');
  if (!isBootstrap && !isPublicCatalog) {
    await ensureIdentity();
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    const body = payload?.error || {};
    throw new ApiError(
      body.message || res.statusText,
      body.code || 'UNKNOWN',
      {
        taskId: payload.task_id,
        stateVersion: payload.state_version,
        sessionVersion: payload.session_version,
        retryable: body.retryable,
      },
    );
  }
  return res.json();
}

export interface Product {
  sku_id: string;
  name: string;
  name_zh?: string;
  category_id: string;
  price_fen?: number;
  image_path?: string;
  sellable?: boolean;
  source?: string;
  spec_unit?: string | null;
  spec_quantity: number | null;
  brand: string | null;
  available_qty: number | null;
}

export interface Category {
  id: string;
  name: string;
  name_zh: string;
  product_count: number;
}

export interface CartItem {
  sku_id: string;
  name: string;
  quantity: number;
  unit_price_fen: number;
  line_total_fen: number;
  image_path?: string | null;
  sellable?: boolean;
}

export interface Cart {
  store_id?: string;
  version: number;
  items: CartItem[];
  total_price_fen: number;
  business_data_mode?: string;
}

export function listCategories() {
  return fetchApi<Category[]>('/api/v1/categories');
}

export function listProducts(params?: { category_id?: string; q?: string; page_size?: number }) {
  const search = new URLSearchParams();
  if (params?.category_id) search.set('category_id', params.category_id);
  if (params?.q) search.set('q', params.q);
  search.set('page_size', String(params?.page_size ?? 48));
  const qs = search.toString();
  return fetchApi<{ items: Product[]; total?: number }>(`/api/v1/products?${qs}`);
}

export function getProduct(skuId: string) {
  return fetchApi<Product>(`/api/v1/products/${encodeURIComponent(skuId)}`);
}

export function getCart() {
  return fetchApi<Cart>('/api/v1/cart');
}

export function addCartItem(skuId: string, quantity: number, expectedCartVersion: number) {
  return fetchApi<Cart>('/api/v1/cart/items', {
    method: 'POST',
    body: JSON.stringify({
      sku_id: skuId,
      quantity,
      expected_cart_version: expectedCartVersion,
    }),
  });
}

export function patchCartItem(skuId: string, quantity: number, expectedCartVersion: number) {
  return fetchApi<Cart>(`/api/v1/cart/items/${encodeURIComponent(skuId)}`, {
    method: 'PATCH',
    body: JSON.stringify({ quantity, expected_cart_version: expectedCartVersion }),
  });
}

export function removeCartItem(skuId: string, expectedCartVersion: number) {
  const qs = new URLSearchParams({ expected_cart_version: String(expectedCartVersion) });
  return fetchApi<Cart>(`/api/v1/cart/items/${encodeURIComponent(skuId)}?${qs}`, {
    method: 'DELETE',
  });
}

export async function clearCartItems(cart: Cart): Promise<Cart> {
  let current = cart;
  for (const item of [...current.items]) {
    current = await removeCartItem(item.sku_id, current.version);
  }
  return current;
}

export interface LocalOrder {
  id: string;
  date: string;
  status: string;
  items: string[];
  total: number;
  total_fen: number;
}

const LOCAL_ORDERS_KEY = 'ceres-local-orders';

export function getLocalOrders(): LocalOrder[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = sessionStorage.getItem(LOCAL_ORDERS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as LocalOrder[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function addLocalOrder(order: LocalOrder): void {
  if (typeof window === 'undefined') return;
  const existing = getLocalOrders();
  sessionStorage.setItem(LOCAL_ORDERS_KEY, JSON.stringify([order, ...existing]));
}

export function formatOrderDate(d = new Date()): string {
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `今天 ${hh}:${mm}`;
}

export function nextLocalOrderId(): string {
  const n = getLocalOrders().length + 7;
  return `#CE24${String(n).padStart(2, '0')}`;
}

/** Map catalog image_path to a browser-loadable URL. */
export function productImageUrl(imagePath?: string | null): string {
  if (!imagePath) return '/placeholder-product.svg';
  const normalized = imagePath.replace(/^\/+/, '');
  if (normalized.startsWith('data/images/')) {
    return `/media/images/${normalized.slice('data/images/'.length)}`;
  }
  if (normalized.startsWith('media/images/')) {
    return `/${normalized}`;
  }
  if (normalized.startsWith('demo/')) {
    return `/${normalized}`;
  }
  return `/${normalized}`;
}

export interface PlanItem {
  sellable?: boolean;
  available_qty?: number;
  ingredient_id?: string;
  available_specs?: {sku_id: string; name: string; spec_quantity: number | null; spec_unit: string | null}[];
  sku_id: string;
  name?: string;
  quantity: number;
  unit_price_fen: number;
  line_total_fen: number;
  image_path?: string | null;
  role?: 'required' | 'pantry' | 'optional';
  selected?: boolean;
  added_quantity?: number;
  remaining_quantity?: number;
  spec_quantity?: number | null;
  spec_unit?: string | null;
  requirement?: { quantity: number | null; unit: string | null; source?: { original_quantity?: number | null; original_unit?: string | null } } | null;
  contributions?: { group_id: string; ingredient_id?: string; sku_id?: string; selected?: boolean; quantity: number; requirement?: PlanItem['requirement'] }[] | null;
}

export interface PlanGap {
  group_ids?: string[];
  requirement?: {quantity: number | null; unit: string | null};
  requested_packs?: number | null;
  available_packs?: number | null;
  shortfall_packs?: number | null;
  alternatives?: {items: {sku_id: string; quantity: number}[]; total_price_fen: number; leftover_quantity: number}[];
  gap_id: string;
  kind: string;
  message?: string;
  name?: string | null;
  sku_id?: string | null;
}

export interface HistorySource {
  task_id: string;
  goal: string | null;
}

export interface HistoryReminder {
  source_task_id: string;
  goal: string | null;
  message: string;
}

export interface PlanResponse {
  budget_quote?: {budget_fen:number; total_fen:number};
  history_source?: {task_id:string; plan_id:string; plan_version:number; goal:string | null};
  history_changes?: string[];
  history_memory?: {memory_id:string; revision:number; content:string}[];
  plan_kind?: 'full_plan' | 'supply_preview' | 'partial_purchase';
  purchase_ledger?: { operation_id: string; sku_id: string; name: string; added_quantity: number; groups: {group_id: string; name: string}[]; contributions: NonNullable<PlanItem['contributions']> }[];
  groups?: { group_id: string; dish_id: string; name: string; base_people: number; people: number; people_source: 'default' | 'explicit' }[];
  dish?: { dish_id: string; name: string; base_people: number; people: number; people_source: 'default' | 'explicit' };
  plan_id: string;
  plan_version: number;
  mode: 'bundle' | 'alternatives';
  items: PlanItem[];
  targets?: { group_id: string | null; name: string | null }[];
  total_price_fen: number;
  selected_total_fen?: number;
  expires_at: string | null;
  validation_status: string;
  gaps?: PlanGap[] | null;
  can_confirm?: boolean;
}

export interface ClarificationOption {
  id: string;
  label: string;
}

export interface PendingClarification {
  question_id: string;
  question: string;
  options: ClarificationOption[];
}

export function normalizePendingClarifications(raw: unknown): PendingClarification[] {
  const list = Array.isArray(raw) ? raw : raw ? [raw] : [];
  const seen = new Set<string>();
  const out: PendingClarification[] = [];
  for (const entry of list) {
    if (!entry || typeof entry !== 'object') continue;
    const row = entry as Record<string, unknown>;
    const question =
      typeof row.question === 'string'
        ? row.question
        : typeof row.prompt === 'string'
          ? row.prompt
          : '';
    if (!question) continue;
    const questionId = String(row.question_id ?? row.id ?? '');
    const key = questionId || question;
    if (seen.has(key)) continue;
    seen.add(key);
    const options: ClarificationOption[] = [];
    if (Array.isArray(row.options)) {
      for (const opt of row.options) {
        if (!opt || typeof opt !== 'object') continue;
        const option = opt as Record<string, unknown>;
        const label = typeof option.label === 'string' ? option.label.trim() : '';
        if (!label) continue;
        options.push({
          id: String(option.id ?? option.candidate_ref ?? label),
          label,
        });
      }
    }
    out.push({ question_id: questionId, question, options });
  }
  return out;
}

export function clarificationChipLabels(clarifications: PendingClarification[]): string[] {
  const seen = new Set<string>();
  const labels: string[] = [];
  for (const item of clarifications) {
    for (const option of item.options) {
      if (seen.has(option.label)) continue;
      seen.add(option.label);
      labels.push(option.label);
    }
  }
  return labels;
}

export interface ProductComparisonCard {
  ref: string;
  sku_id: string;
  name: string;
  brand: string | null;
  image_path: string | null;
  packaging: string | null;
  pack_count: number | null;
  item_volume_ml: number | null;
  total_volume_ml: number | null;
  spec_quantity: number | null;
  spec_unit: string | null;
  price_fen: number | null;
  price_per_litre_yuan: number | null;
}

export interface DisplayedPlanRef {
  task_id: string;
  plan_id: string;
  plan_version: number;
  state_version: number;
  session_version: number;
}

export interface TurnResponse {
  navigation_action?: RoleSwitchAction | null;
  active_question?: GuideQuestion | null;
  question_history?: GuideQuestion[];
  history_sources?: HistorySource[];
  confirmation_result?: ConfirmResponse | null;
  product_cards: ProductComparisonCard[];
  request_id: string;
  session_id: string;
  task_id: string | null;
  state_version: number;
  session_version: number;
  status: string;
  message: string;
  messages?: Array<{message_id: string; content: string}>;
  answer_kind?: 'general_explanation' | 'business_facts' | 'result_introduction';
  expression_status?: 'running' | 'completed' | 'failed' | 'deadline' | 'stopped' | 'stale';
  runtime_status?: string;
  no_matches?: boolean;
  product_evidence?: unknown[];
  plan?: PlanResponse | null;
  plan_effect?: 'keep' | 'replace' | 'clear';
  pending_clarification?: Record<string, unknown> | null;
  pending_clarifications?: Array<Record<string, unknown>> | null;
  available_actions?: string[] | null;
  trace_id: string;
  model_mode: string;
  business_data_mode: string;
  assistant_message_id?: string | null;
}

export interface SessionResponse {
  active_question?: GuideQuestion | null;
  question_history?: GuideQuestion[];
  history_reminder?: HistoryReminder | null;
  product_cards: ProductComparisonCard[];
  confirmation_result?: {
    items_added?: Array<{ sku_id: string; quantity: number }>;
    cart_version?: number;
  } | null;
  session_id: string;
  task_id?: string | null;
  state_version: number;
  session_version: number;
  current_step?: string | null;
  task_status?: string | null;
  entry_context: Record<string, unknown>;
  plan?: PlanResponse | null;
  plan_read_only?: boolean;
  message?: string | null;
  available_actions: string[];
  cart_version?: number | null;
  pending_clarifications?: Array<Record<string, unknown>> | null;
  messages?: Array<{
    message_id: string;
    request_id?: string;
    session_id: string;
    task_id?: string | null;
    sequence: number;
    role: string;
    kind: string;
    content: string;
    plan_id?: string | null;
    plan_version?: number | null;
  }> | null;
}

export interface ConfirmResponse {
  operation_id: string;
  status: string;
  cart_version: number;
  items_added: Array<{ sku_id: string; quantity: number }>;
  errors: string[];
  task_id: string;
  state_version: number;
  session_version: number;
  confirmation_id: string;
}

export function yuan(fen: number | null | undefined): string {
  return `${((fen ?? 0) / 100).toFixed(2)} 元`;
}

export function remainingQuantity(item: PlanItem): number {
  if (typeof item.remaining_quantity === 'number') return item.remaining_quantity;
  return Math.max(0, item.quantity - (item.added_quantity ?? 0));
}

export function confirmableItems(items: PlanItem[]): Array<{ sku_id: string; quantity: number }> {
  return items
    .filter((item) => item.selected !== false && remainingQuantity(item) > 0)
    .map((item) => ({ sku_id: item.sku_id, quantity: remainingQuantity(item) }));
}

export function categoryEmoji(id: string): string {
  const map: Record<string, string> = {
    vegetable: '🥬',
    meat: '🥩',
    dairy: '🥛',
    grain: '🌾',
    condiment: '🧂',
    baking: '🧁',
  };
  return map[id] ?? '📦';
}

export function cartItemCount(cart: Cart | null | undefined): number {
  return cart?.items.reduce((sum, item) => sum + item.quantity, 0) ?? 0;
}

export function clearStoredSessionId() {
  if (typeof window === 'undefined') return;
  sessionStorage.removeItem(SESSION_KEY);
}

const SESSION_KEY = 'ceres-langgraph-guide-session-id';

export function getStoredSessionId(): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(SESSION_KEY);
}

export function storeSessionId(sessionId: string) {
  sessionStorage.setItem(SESSION_KEY, sessionId);
}

export async function createGuideSession(entryContext: Record<string, unknown>) {
  const bootstrap = await ensureIdentity();
  const res = await fetchApi<SessionResponse>('/api/v1/guide/sessions', {
    method: 'POST',
    body: JSON.stringify({
      entry_context: {
        ...entryContext,
        store_id: bootstrap.store_id,
        delivery_zone_id: bootstrap.delivery_zone_id,
      },
    }),
  });
  storeSessionId(res.session_id);
  return res;
}

export async function getHistoricalSources(sessionId: string) {
  return fetchApi<{sources:HistorySource[]}>(`/api/v1/guide/sessions/${sessionId}/history`);
}

export async function dismissHistoryReminder(sessionId: string, taskId: string, decision: 'ignore' | 'decline') {
  return fetchApi<SessionResponse>(`/api/v1/guide/sessions/${sessionId}/history/reminder`, {method:'POST', body:JSON.stringify({task_id:taskId,decision})});
}

export async function getGuideSession(sessionId: string, includeMessages = true) {
  const q = includeMessages ? '?include_messages=1' : '';
  return fetchApi<SessionResponse>(`/api/v1/guide/sessions/${sessionId}${q}`);
}

export interface TurnStreamEvent {
  protocol_version: number;
  run_id: string | null;
  sequence: number;
  type: string;
  recorded_at_ms: number | null;
  elapsed_ms: number | null;
  session_id: string;
  target_task_id?: string | null;
  message_id?: string | null;
  payload?: Record<string, unknown>;
}

export interface TurnStreamCallbacks {
  onAccepted?: (event: TurnStreamEvent) => void;
  onProgress?: (event: TurnStreamEvent) => void;
  onAnswerDelta?: (event: TurnStreamEvent) => void;
  onInterimMessage?: (event: TurnStreamEvent) => void;
  onPlanReady?: (event: TurnStreamEvent) => void;
  onClarification?: (event: TurnStreamEvent) => void;
  onTurnCompleted?: (event: TurnStreamEvent) => void;
  onError?: (event: TurnStreamEvent) => void;
  onStopped?: (event: TurnStreamEvent) => void;
  signal?: AbortSignal;
}

function buildTurnRequestBody(
  message: string,
  expectedTaskId: string | null,
  expectedStateVersion: number,
  requestId: string,
  expectedSessionVersion?: number | null,
  viewContext?: {
    page: string;
    category_id?: string | null;
    product_id?: string | null;
  },
) {
  return {
    request_id: requestId,
    message,
    expected_task_id: expectedTaskId,
    expected_state_version: expectedStateVersion,
    expected_session_version: expectedSessionVersion ?? undefined,
    view_context: viewContext,
  };
}

function parseSseTurnEvents(buffer: string): { events: TurnStreamEvent[]; remainder: string } {
  const parts = buffer.split('\n\n');
  const remainder = parts.pop() ?? '';
  const events: TurnStreamEvent[] = [];
  for (const part of parts) {
    const line = part.trim();
    if (!line.startsWith('data:')) continue;
    events.push(JSON.parse(line.slice(5).trim()) as TurnStreamEvent);
  }
  return { events, remainder };
}

function dispatchStreamEvent(event: TurnStreamEvent, callbacks?: TurnStreamCallbacks): TurnResponse | null {
  switch (event.type) {
    case 'accepted':
      callbacks?.onAccepted?.(event);
      return null;
    case 'progress':
      callbacks?.onProgress?.(event);
      return null;
    case 'answer.delta':
      callbacks?.onAnswerDelta?.(event);
      return null;
    case 'message.interim':
      callbacks?.onInterimMessage?.(event);
      return null;
    case 'plan.ready':
      callbacks?.onPlanReady?.(event);
      return null;
    case 'clarification':
      callbacks?.onClarification?.(event);
      return null;
    case 'turn.completed':
      callbacks?.onTurnCompleted?.(event);
      return event.payload ? (event.payload as unknown as TurnResponse) : null;
    case 'turn.stopped':
    case 'stopped':
      callbacks?.onStopped?.(event);
      return event.payload
        ? ({ ...(event.payload as unknown as TurnResponse), status: 'stopped' } as TurnResponse)
        : null;
    case 'error': {
      callbacks?.onError?.(event);
      const code = String(event.payload?.code || 'STREAM_ERROR');
      throw new ApiError(String(event.payload?.message || 'Stream failed'), code, {
        retryable: Boolean(event.payload?.retryable),
      });
    }
    default:
      return null;
  }
}

export async function sendTurnStream(
  sessionId: string,
  message: string,
  expectedTaskId: string | null,
  expectedStateVersion: number,
  requestId: string,
  expectedSessionVersion?: number | null,
  viewContext?: {
    page: string;
    category_id?: string | null;
    product_id?: string | null;
  },
  callbacks?: TurnStreamCallbacks,
  displayedPlan?: DisplayedPlanRef | null,
  displayedCandidateRefs: string[] = [],
  routingRequestId?: string,
): Promise<TurnResponse> {
  await ensureIdentity();

  const res = await fetch(`/api/v1/guide/sessions/${sessionId}/turns/stream`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    signal: callbacks?.signal,
    body: JSON.stringify(
      { ...buildTurnRequestBody(
        message,
        expectedTaskId,
        expectedStateVersion,
        requestId,
        expectedSessionVersion,
        viewContext,
      ), displayed_plan: displayedPlan ?? null, displayed_candidate_refs: displayedCandidateRefs, routing_request_id: routingRequestId ?? null },
    ),
  });

  if (!res.ok || !res.body) {
    const payload = await res.json().catch(() => ({}));
    const body = payload?.error || {};
    throw new ApiError(body.message || res.statusText, body.code || 'STREAM_FAILED', {
      taskId: payload.task_id,
      stateVersion: payload.state_version,
      sessionVersion: payload.session_version,
      retryable: body.retryable,
    });
  }

  return consumeTurnStream(res, callbacks);
}

async function consumeTurnStream(res: Response, callbacks?: TurnStreamCallbacks): Promise<TurnResponse> {
  if (!res.body) throw new Error('Stream body missing');
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let turnResult: TurnResponse | null = null;
  const sequences = new Map<string | null, number>();
  function receive(event: TurnStreamEvent) {
    callbacks?.signal?.throwIfAborted();
    // SSE recovery replays a run; a repeated frame must never append text twice.
    if (event.sequence <= (sequences.get(event.run_id) ?? 0)) return;
    sequences.set(event.run_id, event.sequence);
    const completed = dispatchStreamEvent(event, callbacks);
    if (completed) turnResult = completed;
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSseTurnEvents(buffer);
      buffer = parsed.remainder;
      for (const event of parsed.events) {
        receive(event);
      }
    }

    if (buffer.trim()) {
      const parsed = parseSseTurnEvents(`${buffer}\n\n`);
      for (const event of parsed.events) {
        receive(event);
      }
    }
  } finally {
    reader.releaseLock();
  }

  if (!turnResult) {
    throw new Error('Stream ended without turn.completed');
  }
  return turnResult;
}

export interface GuideRun {
  run_id: string;
  request_id: string;
  status: string;
  input: {message?: string; kind?: string; role?: 'keke' | 'momo'};
  result?: Partial<TurnResponse> & {code?:string};
}

export function getGuideStatus(sessionId: string) {
  return fetchApi<SessionResponse & {runs: GuideRun[]}>(`/api/v1/guide/sessions/${sessionId}/status`);
}

export async function reconnectGuideRun(sessionId: string, runId: string, callbacks?: TurnStreamCallbacks, afterSequence = 0) {
  await ensureIdentity();
  const res = await fetch(`/api/v1/guide/sessions/${sessionId}/runs/${runId}/stream?after_sequence=${afterSequence}`, {credentials:'include', signal:callbacks?.signal});
  if (!res.ok) throw new Error('运行恢复失败');
  return consumeTurnStream(res, callbacks);
}

export function stopGuideTurn(sessionId: string, requestId: string) {
  return fetchApi<{cancelled:boolean; result?:TurnResponse}>(`/api/v1/guide/sessions/${sessionId}/turns/stop`, {method:'POST', body:JSON.stringify({request_id:requestId})});
}

export function abandonGuideTask(sessionId: string, snapshot: {task_id: string|null; state_version:number; session_version:number}) {
  return fetchApi<SessionResponse>(`/api/v1/guide/sessions/${sessionId}/tasks/current`, {method:'POST', body:JSON.stringify({request_id:crypto.randomUUID(), kind:'abandon', expected_task_id:snapshot.task_id, expected_state_version:snapshot.state_version, expected_session_version:snapshot.session_version})});
}

export async function confirmPlan(
  taskId: string,
  planId: string,
  planVersion: number,
  stateVersion: number,
  sessionVersion: number,
  selectedItems: Array<{ sku_id: string; quantity: number }>,
  idempotencyKey: string,
): Promise<ConfirmResponse> {
  return fetchApi<ConfirmResponse>(`/api/v1/guide/tasks/${taskId}/confirm`, {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    body: JSON.stringify({
      plan_id: planId,
      plan_version: planVersion,
      expected_state_version: stateVersion,
      expected_session_version: sessionVersion,
      selected_items: selectedItems,
    }),
  });
}

export async function revisePlan(
  taskId: string,
  plan: PlanResponse,
  stateVersion: number,
  sessionVersion: number,
  items: Array<{ sku_id: string; quantity: number; selected: boolean }>,
): Promise<PlanResponse & {
  can_confirm: boolean;
  state_version: number;
  session_version: number;
}> {
  return fetchApi(`/api/v1/guide/tasks/${taskId}/plan-revisions`, {
    method: 'POST',
    body: JSON.stringify({
      request_id: crypto.randomUUID(),
      expected_state_version: stateVersion,
      expected_session_version: sessionVersion,
      base_plan_id: plan.plan_id,
      base_plan_version: plan.plan_version,
      coverage_intent: 'selection_only',
      items,
    }),
  });
}


export function addPlanItem(taskId: string, skuId: string, plan: PlanResponse, stateVersion: number, sessionVersion: number, quantity: number, idempotencyKey: string): Promise<ConfirmResponse> {
  return fetchApi(`/api/v1/guide/tasks/${taskId}/items/${encodeURIComponent(skuId)}/add`, {
    method: 'POST', headers: {'Idempotency-Key': idempotencyKey},
    body: JSON.stringify({plan_id:plan.plan_id, plan_version:plan.plan_version, expected_state_version:stateVersion, expected_session_version:sessionVersion, selected_items:[{sku_id:skuId,quantity}]}),
  });
}

export function reviseDishPlan(taskId: string, plan: PlanResponse, stateVersion: number, sessionVersion: number, changes: {people?: number; selections?: Record<string,string>; group_id?: string; remove_group?: boolean}): Promise<PlanResponse & {state_version: number; session_version: number}> {
  return fetchApi(`/api/v1/guide/tasks/${taskId}/plan-revisions`, {method:'POST', body:JSON.stringify({request_id:crypto.randomUUID(), base_plan_id:plan.plan_id, base_plan_version:plan.plan_version, expected_state_version:stateVersion, expected_session_version:sessionVersion, coverage_intent:changes.remove_group ? 'group_remove' : changes.group_id ? 'group_update' : 'dish_update', items:[], people:changes.people, selections:changes.selections, group_id:changes.group_id})});
}

export function choosePartialSupply(taskId: string, plan: PlanResponse, stateVersion: number, sessionVersion: number) {
  return fetchApi<PlanResponse & {state_version: number; session_version: number}>(`/api/v1/guide/tasks/${taskId}/plan-revisions`, {method:'POST', body:JSON.stringify({request_id:crypto.randomUUID(), base_plan_id:plan.plan_id, base_plan_version:plan.plan_version, expected_state_version:stateVersion, expected_session_version:sessionVersion, coverage_intent:'choose_partial', items:[]})});
}

export function chooseSupplyAlternative(taskId: string, plan: PlanResponse, stateVersion: number, sessionVersion: number, gapId: string, alternativeIndex: number) {
  return fetchApi<PlanResponse & {state_version: number; session_version: number}>(`/api/v1/guide/tasks/${taskId}/plan-revisions`, {method:'POST', body:JSON.stringify({request_id:crypto.randomUUID(), base_plan_id:plan.plan_id, base_plan_version:plan.plan_version, expected_state_version:stateVersion, expected_session_version:sessionVersion, coverage_intent:'choose_alternative', items:[], gap_id:gapId, alternative_index:alternativeIndex})});
}

export function acceptPlanQuote(taskId: string, plan: PlanResponse, stateVersion: number, sessionVersion: number) {
  return fetchApi<PlanResponse & {state_version: number; session_version: number}>(`/api/v1/guide/tasks/${taskId}/plan-revisions`, {method:'POST', body:JSON.stringify({request_id:crypto.randomUUID(), base_plan_id:plan.plan_id, base_plan_version:plan.plan_version, expected_state_version:stateVersion, expected_session_version:sessionVersion, coverage_intent:'accept_quote', items:[]})});
}
