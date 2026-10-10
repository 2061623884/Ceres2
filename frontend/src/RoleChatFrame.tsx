import { useEffect, useRef, useState, type ReactNode, type RefObject } from 'react'
import type { ChatRole, RouteDecision } from './lib/chatNavigation'

export interface RoleChatNavigationProps {
  view: ChatRole
  navigationBusy: boolean
  navigationReady: boolean
  navigationError: string | null
  routePrompt: RouteDecision | null
  onSwitchRole: (role: ChatRole) => void
  onClose: () => void
  onRouteAccept: () => void
  onRouteDecline: () => void
  onRetryAck?: () => void
}

export interface RoleChatComposerProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  placeholder: string
  disabled?: boolean
  sendDisabled?: boolean
}

export interface ComposerPlusAction {
  label: string
  onClick: () => void
  disabled?: boolean
  ariaLabel?: string
}

const composerToolChipBase =
  'inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-2 text-[13px] font-medium tracking-[-0.01em] transition-colors shadow-[0_1px_8px_rgba(40,36,29,0.07)] active:scale-[0.98] disabled:opacity-40'

export function composerToolChipClass(active: boolean) {
  return `${composerToolChipBase} ${
    active
      ? 'border-black/[0.14] bg-white text-[#1d1c1a]'
      : 'border-black/[0.07] bg-white text-black/55 hover:text-black/72'
  }`
}

/** 跨角色快捷入口（如墨墨侧的「继续选购」） */
export function composerKekeGuideChipClass() {
  return `${composerToolChipBase} border-[#c5ddb8] bg-[#e8f4e0] text-[#2a5038] hover:bg-[#dfeccd]`
}

export function RoleChatFrame({
  activeRole,
  agentAvatar,
  agentName,
  statusLine,
  headerTools,
  navigation,
  threadBanner,
  children,
  bottomRef,
  toolRow,
  sheetSlot,
  composer,
  composerPlusActions,
  overlay,
}: {
  activeRole: ChatRole
  agentAvatar: ReactNode
  agentName: string
  statusLine?: ReactNode
  headerTools?: ReactNode
  navigation?: RoleChatNavigationProps
  threadBanner?: ReactNode
  children: ReactNode
  bottomRef?: RefObject<HTMLDivElement | null>
  toolRow?: ReactNode
  sheetSlot?: ReactNode
  composer: RoleChatComposerProps
  composerPlusActions?: ComposerPlusAction[]
  overlay?: ReactNode
}) {
  const sendActive = composer.value.trim() && !composer.sendDisabled
  const [plusOpen, setPlusOpen] = useState(false)
  const plusRef = useRef<HTMLDivElement>(null)
  const plusActions = composerPlusActions ?? []

  useEffect(() => {
    if (!plusOpen) return
    const close = (event: MouseEvent) => {
      if (plusRef.current && !plusRef.current.contains(event.target as Node)) setPlusOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [plusOpen])

  return (
    <section
      className="guide-chat-panel chat-panel-enter relative flex h-[min(65vh,600px)] min-h-[min(420px,60vh)] flex-col overflow-hidden rounded-t-[38px] font-sans"
    >
      <div className="flex flex-shrink-0 justify-center bg-[#f7f5f0] pt-3 pb-1.5" aria-hidden="true">
        <span className="h-1 w-10 rounded-full bg-black/[.12]" />
      </div>
      <header className="flex-shrink-0 bg-[#f7f5f0] px-4 pb-3" aria-label={navigation ? '角色导航' : undefined}>
        <div className="guide-glass-header-pill flex items-center gap-3 rounded-full px-4 py-2">
          {agentAvatar}
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-semibold tracking-[-0.04em] text-[#191817]">{agentName}</p>
            {statusLine ? (
              <div className="text-[10px] text-black/40">{statusLine}</div>
            ) : (
              <p className="text-[10px] text-black/40">{activeRole === 'keke' ? '选购助手' : '订单与售后'}</p>
            )}
          </div>
          {headerTools}
        </div>

        {navigation && (navigation.navigationBusy || navigation.navigationError || navigation.routePrompt) && (
          <div className="mt-2">
            {navigation.navigationBusy && (
              <p className="mt-2 text-xs" role="status">
                正在连接角色…
              </p>
            )}
            {navigation.navigationError && (
              <p className="mt-2 text-xs text-red-700" role="alert">
                {navigation.navigationError}
              </p>
            )}
            {navigation.routePrompt && (
              <div className="mt-2 text-sm" role="status">
                <p>{navigation.routePrompt.message}</p>
                <div className="mt-2 flex flex-wrap gap-3">
                  <button type="button" disabled={navigation.navigationBusy} onClick={navigation.onRouteAccept}>
                    切换并继续原请求
                  </button>
                  <button type="button" disabled={navigation.navigationBusy} onClick={navigation.onRouteDecline}>
                    留在这里
                  </button>
                  {navigation.navigationError?.startsWith('提示确认失败') && navigation.onRetryAck && (
                    <button type="button" onClick={navigation.onRetryAck}>重试确认</button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </header>

      {threadBanner}

      <div className="scrollbar-hide min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-5">
        {children}
        {bottomRef && <div ref={bottomRef} />}
      </div>

      <div className="relative flex-shrink-0 px-5 pb-4 pt-1">
        {sheetSlot}
        {toolRow}
        <div
          className="flex items-center gap-1.5 rounded-full border border-black/[0.08] bg-white py-1.5 pl-1.5 pr-2 shadow-[0_2px_12px_rgba(40,36,29,0.06)]"
        >
          {plusActions.length > 0 && (
            <div className="relative shrink-0" ref={plusRef}>
              <button
                type="button"
                aria-label="更多操作"
                aria-expanded={plusOpen}
                onClick={() => setPlusOpen(open => !open)}
                className="grid h-9 w-9 place-items-center rounded-full text-black/45 transition hover:bg-black/[0.04] active:scale-95"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </button>
              {plusOpen && (
                <div
                  role="menu"
                  className="absolute bottom-full left-0 z-20 mb-2 min-w-[10.5rem] overflow-hidden rounded-2xl border border-black/[0.08] bg-white py-1 shadow-[0_8px_28px_rgba(40,36,29,0.12)]"
                >
                  {plusActions.map(action => (
                    <button
                      key={action.ariaLabel ?? action.label}
                      type="button"
                      role="menuitem"
                      disabled={action.disabled}
                      aria-label={action.ariaLabel}
                      onClick={() => {
                        setPlusOpen(false)
                        action.onClick()
                      }}
                      className="block w-full px-4 py-2.5 text-left text-[13px] font-medium text-[#1d1c1a] transition hover:bg-black/[0.04] disabled:opacity-40"
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          <input
            value={composer.value}
            onChange={event => composer.onChange(event.target.value)}
            onKeyDown={event => {
              if (event.key === 'Enter') composer.onSend()
            }}
            placeholder={composer.placeholder}
            disabled={composer.disabled}
            className="min-w-0 flex-1 bg-transparent px-1 py-2 text-[13px] font-medium text-[#1d1c1a] outline-none placeholder:text-black/35"
          />
          <button
            type="button"
            onClick={composer.onSend}
            disabled={!sendActive}
            className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full transition-all active:scale-90 ${
              sendActive ? 'bg-[#171716]' : 'bg-[#eeece7]'
            }`}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="white">
              <path d="M2 21L23 12 2 3v7l15 2-15 2z" />
            </svg>
          </button>
        </div>
      </div>

      {overlay ? <div className="absolute inset-0 z-40">{overlay}</div> : null}
    </section>
  )
}
