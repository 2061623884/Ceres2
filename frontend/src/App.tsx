import { runResultIntroduction, type IntroductionSource } from './lib/resultIntroduction'
import { enterLightMealActivity } from './lib/activity'
import QuestionChoices from './QuestionChoices'
import { answerGuideQuestion, type GuideQuestion } from './lib/productQuestions'
import './role-chat.css'
import { openNavigation, closeOpening, routeText, ackPrompt, chooseRole, type BeforeText, type ChatRole, type Handoff, type Opening, type RouteDecision } from './lib/chatNavigation'
import ComparisonCards from './ComparisonCards'
import { useState, useRef, useEffect, useCallback } from 'react'
import { MercuryChat } from './MercuryChat'
import { KekeAvatar } from './components/KekeAvatar'
import { RoleChatFrame, composerToolChipClass, type ComposerPlusAction, type RoleChatNavigationProps } from './RoleChatFrame'
import { HumanOperatorPage } from './HumanOperatorPage'
import { SimulatedCheckout, SimulatedOrdersScreen } from './SimulatedOrders'
import { MomoAvatar } from './components/MomoToast'
import {
  ApiError,
  addCartItem,
  addPlanItem,
  acceptPlanQuote,
  cartItemCount,
  categoryEmoji,
  confirmPlan,
  confirmableItems,
  createGuideSession,
  ensureIdentity,
  getCart,
  getGuideSession,
  getHistoricalSources,
  dismissHistoryReminder,
  type HistorySource,
  type HistoryReminder,
  getGuideStatus,
  reconnectGuideRun,
  stopGuideTurn,
  abandonGuideTask,
  listCategories,
  listProducts,
  clarificationChipLabels,
  normalizePendingClarifications,
  patchCartItem,
  progressPhaseLabel,
  productImageUrl,
  remainingQuantity,
  revisePlan,
  reviseDishPlan,
  choosePartialSupply,
  chooseSupplyAlternative,
  sendTurnStream,
  yuan,
  type Cart,
  type ConfirmResponse,
  type Category,
  type PlanResponse,
  type DisplayedPlanRef,
  type Product,
  type ProductComparisonCard,
  type SessionResponse,
  type TurnResponse,
} from './lib/saleGuide'

// ── Ceres Mascot ─────────────────────────────────────────────
type CeresMood = 'angry' | 'sad' | 'calm' | 'pleased' | 'happy'

function CeresMascot({ size = 36, mood = 'happy', animated = false }: { size?: number; mood?: CeresMood; animated?: boolean }) {
  const g = '#3DAA6B'
  const s = '#1A2E1F'
  return (
    <svg className={animated ? `ceres-hero-motion ceres-motion-${mood}` : undefined} width={size} height={size * 1.05} viewBox="0 0 72 76" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="36" cy="19" r="17" fill={g} />
      <circle cx="19" cy="36" r="17" fill={g} />
      <circle className={animated ? 'ceres-wave-leaf' : undefined} cx="53" cy="36" r="17" fill={g} />
      <circle cx="36" cy="53" r="17" fill={g} />
      <circle cx="36" cy="36" r="16" fill={g} />
      <ellipse cx="36" cy="12" rx="8" ry="4.5" fill="white" opacity="0.18" />
      {mood === 'angry' && <><path d="M27 37 L33 39 M45 37 L39 39" stroke={s} strokeWidth="2.4" strokeLinecap="round" /><ellipse className="ceres-eye" cx="31" cy="42" rx="2.1" ry="2.4" fill={s}/><ellipse className="ceres-eye" cx="41" cy="42" rx="2.1" ry="2.4" fill={s}/><path d="M30 51 Q36 46.5 42 51" stroke={s} strokeWidth="2.3" fill="none" strokeLinecap="round"/></>}
      {mood === 'sad' && <><ellipse className="ceres-eye" cx="31" cy="40" rx="2" ry="2.5" fill={s}/><ellipse className="ceres-eye" cx="41" cy="40" rx="2" ry="2.5" fill={s}/><path d="M30 51 Q36 46.5 42 51" stroke={s} strokeWidth="2" fill="none" strokeLinecap="round"/><path d="M45 44 C48 47 45 51 43.5 48 C42 46 44 44 45 44Z" fill="#9EDAF2"/></>}
      {mood === 'calm' && <><path d="M27 41 Q31 44 34 41 M38 41 Q41 44 45 41" stroke={s} strokeWidth="2" fill="none" strokeLinecap="round"/><path d="M31 49 L41 49" stroke={s} strokeWidth="2" strokeLinecap="round"/></>}
      {mood === 'pleased' && <><path d="M27 40 Q31 44 34 40 M38 40 Q42 44 45 40" stroke={s} strokeWidth="2.1" fill="none" strokeLinecap="round"/><path d="M30 48 Q36 54 42 48" stroke={s} strokeWidth="2.2" fill="none" strokeLinecap="round"/><ellipse cx="25.5" cy="46" rx="4" ry="2.5" fill="#F5A8C0" opacity="0.48"/><ellipse cx="46.5" cy="46" rx="4" ry="2.5" fill="#F5A8C0" opacity="0.48"/></>}
      {mood === 'happy' && <><path d="M 29 40 Q 32.5 37 36 40" stroke={s} strokeWidth="2.2" fill="none" strokeLinecap="round" /><ellipse className="ceres-eye" cx="42" cy="38.5" rx="2.6" ry="2.8" fill={s} /><circle cx="43.1" cy="37.1" r="1" fill="white" /><ellipse cx="25.5" cy="44.5" rx="4" ry="2.5" fill="#F5A8C0" opacity="0.4" /><ellipse cx="46.5" cy="44.5" rx="4" ry="2.5" fill="#F5A8C0" opacity="0.4" /><path d="M 30 47.5 Q 36 52.5 42 47.5" stroke={s} strokeWidth="2" fill="none" strokeLinecap="round" /></>}
    </svg>
  )
}

function ToastMascot({ mood, animated = false }: { mood: CeresMood; animated?: boolean }) {
  const motionClass = animated ? `toast-motion toast-motion-${mood}` : ''
  const face = {
    angry: <><path d="M246 279l42 12m137-3-42 14" stroke="#303040" strokeWidth="12" strokeLinecap="round"/><ellipse cx="278" cy="310" rx="12" ry="16" fill="#303040"/><ellipse cx="391" cy="310" rx="12" ry="16" fill="#303040"/><path d="M296 367q41-25 82 0" fill="none" stroke="#303040" strokeWidth="10" strokeLinecap="round"/></>,
    sad: <><path d="M246 296q28-18 55 1m67 1q28-18 55 1" fill="none" stroke="#303040" strokeWidth="10" strokeLinecap="round"/><ellipse cx="278" cy="311" rx="10" ry="13" fill="#303040"/><ellipse cx="391" cy="311" rx="10" ry="13" fill="#303040"/><path d="M296 373q41-25 82 0" fill="none" stroke="#303040" strokeWidth="9" strokeLinecap="round"/><path className="toast-tear" d="M407 329c10 15 5 27-5 27s-15-12 5-27Z" fill="#79cbe8"/></>,
    calm: <><path d="M244 310q29 20 58 0m64 0q29 20 58 0" fill="none" stroke="#303040" strokeWidth="10" strokeLinecap="round"/><path d="M300 367h74" stroke="#303040" strokeWidth="9" strokeLinecap="round"/></>,
    pleased: <><path d="M244 309q29 22 58 0m64 0q29 22 58 0" fill="none" stroke="#303040" strokeWidth="10" strokeLinecap="round"/><path d="M298 359q40 47 80 0" fill="none" stroke="#303040" strokeWidth="10" strokeLinecap="round"/><ellipse cx="239" cy="349" rx="22" ry="12" fill="#f39aad" opacity=".75"/><ellipse cx="430" cy="349" rx="22" ry="12" fill="#f39aad" opacity=".75"/></>,
    happy: <><path d="M243 303q30 27 60 0m63 0q30 27 60 0" fill="none" stroke="#303040" strokeWidth="11" strokeLinecap="round"/><path d="M295 354q42 55 85 0" fill="#303040" stroke="#303040" strokeWidth="8" strokeLinecap="round"/><path d="M314 372q23 12 46 0" stroke="white" strokeWidth="8" strokeLinecap="round"/><ellipse cx="238" cy="347" rx="24" ry="13" fill="#f39aad" opacity=".8"/><ellipse cx="432" cy="347" rx="24" ry="13" fill="#f39aad" opacity=".8"/></>,
  }[mood]

  return (
    <div className={`toast-mascot relative block h-[218px] w-[205px] brightness-[1.06] saturate-[1.04] contrast-[1.01] ${motionClass}`}>
      <img src="/assets/a49bc.svg" alt="吐司吉祥物" className="block h-full w-full" width="205" height="218" />
      <svg aria-hidden="true" className="pointer-events-none absolute inset-0 h-full w-full -translate-y-[6px] scale-[1.12]" viewBox="0 0 676 720" fill="none">
        <path d="M210 236C256 205 337 204 401 236C432 251 444 279 434 318L415 394C374 420 278 411 221 375C203 332 197 277 210 236Z" fill="#E0D080" />
        {face}
      </svg>
    </div>
  )
}

// ── Illustrations ─────────────────────────────────────────────
function DietBowlSVG() {
  return (
    <svg width="110" height="110" viewBox="0 0 110 110" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* plate shadow */}
      <ellipse cx="55" cy="88" rx="32" ry="7" fill="#E8D5C4" opacity="0.5" />
      {/* bowl body */}
      <path d="M22 58 Q22 86 55 86 Q88 86 88 58 Z" fill="white" stroke="#E8D5C4" strokeWidth="1.5" />
      {/* bowl rim */}
      <ellipse cx="55" cy="58" rx="33" ry="10" fill="white" stroke="#E8D5C4" strokeWidth="1.5" />
      {/* salad greens */}
      <ellipse cx="55" cy="54" rx="26" ry="9" fill="#5BC480" />
      <path d="M30 54 Q38 44 46 54 Q54 44 62 54 Q70 44 78 54" fill="#3DAA6B" />
      <path d="M34 56 Q42 48 50 56" fill="#5BC480" />
      <path d="M60 56 Q68 48 76 56" fill="#5BC480" />
      {/* tomatoes */}
      <circle cx="44" cy="52" r="6" fill="#F05A5A" />
      <path d="M42 46 Q44 43 46 46" stroke="#3DAA6B" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      <circle cx="44" cy="52" r="2" fill="#F07070" opacity="0.5" />
      <circle cx="65" cy="53" r="5" fill="#F05A5A" />
      <path d="M63 48 Q65 45 67 48" stroke="#3DAA6B" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      {/* lemon wedge */}
      <path d="M72 48 Q80 44 82 52 Q76 54 72 48Z" fill="#FFE566" stroke="#F5C800" strokeWidth="1" />
      <path d="M74 49 L80 51" stroke="#F5C800" strokeWidth="0.8" strokeLinecap="round" />
      {/* sparkles */}
      <path d="M20 38 L21.5 34 L23 38 L20 38Z" fill="#FFD166" />
      <path d="M21.5 34 L21.5 30 L20 34" fill="#FFD166" opacity="0.6" />
      <circle cx="21.5" cy="34" r="1.5" fill="#FFD166" />
      <path d="M88 30 L89.5 26 L91 30 L88 30Z" fill="#FFD166" />
      <path d="M89.5 26 L89.5 22" stroke="#FFD166" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M85 28 L89.5 26 L94 28" stroke="#FFD166" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="25" cy="24" r="2" fill="#FFD166" opacity="0.6" />
      <circle cx="85" cy="40" r="1.5" fill="#FFD166" opacity="0.8" />
    </svg>
  )
}

function BasketSVG() {
  return (
    <svg width="110" height="110" viewBox="0 0 110 110" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* shadow */}
      <ellipse cx="55" cy="90" rx="30" ry="6" fill="#E0C9A0" opacity="0.4" />
      {/* basket body */}
      <path d="M20 55 Q20 85 55 85 Q90 85 90 55 Z" fill="#D4A86A" />
      <path d="M20 55 L90 55" stroke="#C49050" strokeWidth="1" />
      {/* weave lines horizontal */}
      <path d="M22 63 L88 63" stroke="#C49050" strokeWidth="0.8" opacity="0.6" />
      <path d="M23 71 L87 71" stroke="#C49050" strokeWidth="0.8" opacity="0.6" />
      <path d="M25 79 L85 79" stroke="#C49050" strokeWidth="0.8" opacity="0.6" />
      {/* weave lines vertical */}
      <path d="M35 55 L32 85" stroke="#C49050" strokeWidth="0.8" opacity="0.5" />
      <path d="M45 55 L43 85" stroke="#C49050" strokeWidth="0.8" opacity="0.5" />
      <path d="M55 55 L55 85" stroke="#C49050" strokeWidth="0.8" opacity="0.5" />
      <path d="M65 55 L67 85" stroke="#C49050" strokeWidth="0.8" opacity="0.5" />
      <path d="M75 55 L78 85" stroke="#C49050" strokeWidth="0.8" opacity="0.5" />
      {/* basket rim */}
      <ellipse cx="55" cy="55" rx="35" ry="10" fill="#E8B87A" stroke="#C49050" strokeWidth="1.5" />
      {/* handle */}
      <path d="M30 55 Q30 28 55 28 Q80 28 80 55" fill="none" stroke="#C49050" strokeWidth="5" strokeLinecap="round" />
      <path d="M30 55 Q30 30 55 30 Q80 30 80 55" fill="none" stroke="#D4A86A" strokeWidth="3" strokeLinecap="round" />
      {/* carrot */}
      <path d="M62 22 Q65 10 68 20 Q70 30 65 40 Q60 35 62 22Z" fill="#FF8C3A" />
      <path d="M65 10 L62 4 M65 10 L68 3 M65 10 L60 5" stroke="#3DAA6B" strokeWidth="1.8" strokeLinecap="round" />
      {/* leafy greens */}
      <path d="M28 44 Q20 30 30 28 Q32 38 28 44Z" fill="#5BC480" />
      <path d="M33 42 Q26 26 38 24 Q38 36 33 42Z" fill="#3DAA6B" />
      <path d="M38 42 Q34 28 44 26 Q43 38 38 42Z" fill="#5BC480" />
      {/* radish */}
      <circle cx="48" cy="44" r="7" fill="#F06090" />
      <path d="M46 37 L45 30 M48 37 L48 29 M50 37 L51 30" stroke="#3DAA6B" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M48 51 L49 57" stroke="#F06090" strokeWidth="1.5" strokeLinecap="round" />
      {/* sparkles */}
      <circle cx="88" cy="38" r="2" fill="#FFD166" />
      <path d="M88 34 L88 42 M84 38 L92 38" stroke="#FFD166" strokeWidth="1.2" strokeLinecap="round" />
      <circle cx="18" cy="42" r="1.5" fill="#FFD166" opacity="0.8" />
      <path d="M20 26 L21 22 L22 26 L20 26Z" fill="#FFD166" />
      <circle cx="85" cy="22" r="1.5" fill="#FFD166" opacity="0.7" />
    </svg>
  )
}

// ── Icons ─────────────────────────────────────────────────────
function IconHome({ filled }: { filled?: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      {!filled && <polyline points="9 22 9 12 15 12 15 22" />}
    </svg>
  )
}
function IconGrid({ filled }: { filled?: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" fill={filled ? 'currentColor' : 'none'} />
      <rect x="14" y="3" width="7" height="7" fill={filled ? 'currentColor' : 'none'} />
      <rect x="3" y="14" width="7" height="7" fill={filled ? 'currentColor' : 'none'} />
      <rect x="14" y="14" width="7" height="7" fill={filled ? 'currentColor' : 'none'} />
    </svg>
  )
}
function IconOrders({ filled }: { filled?: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  )
}
function IconUser({ filled }: { filled?: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  )
}
function IconCart() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="9" cy="21" r="1" /><circle cx="20" cy="21" r="1" />
      <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
    </svg>
  )
}
function IconSearch() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  )
}
function IconBell() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  )
}

// ── Demo badge & Chat types ───────────────────────────────────
function DemoBadge() {
  return (
    <span className="rounded-full bg-black/[0.06] px-1.5 py-0.5 text-[9px] font-semibold tracking-wide text-black/40">
      演示
    </span>
  )
}

type Role = 'user' | 'ai'
interface Msg { id: string; role: Role; text: string; question?: GuideQuestion; generalExplanation?: boolean; suggestions?: string[]; productCards?: ProductComparisonCard[] }

const WELCOME_MSG: Msg = {
  id: 'welcome',
  role: 'ai',
  text: '嗨！我是可可 🌿\n你的专属导购小助手！告诉我今天想吃什么，我来帮你搞定～',
}

function newRequestId() {
  return `req-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

function formatText(text: string) {
  return text.split('\n').map((line, i, arr) => (
    <span key={i}>
      {line.split(/\*\*(.*?)\*\*/g).map((part, j) =>
        j % 2 === 1 ? <strong key={j}>{part}</strong> : part
      )}
      {i < arr.length - 1 && <br />}
    </span>
  ))
}

function stripDuplicateClarificationOptions(text: string, suggestions: string[] | undefined): string {
  if (!suggestions?.length || !text.trim()) return text

  const lines = text.split('\n')
  const numbered: { index: number; label: string }[] = []

  for (let i = 0; i < lines.length; i++) {
    const match = lines[i].trim().match(/^\d+\.\s*(.+)$/)
    if (match) numbered.push({ index: i, label: match[1].trim() })
  }

  if (numbered.length === 0) return text

  const firstIdx = numbered[0].index
  const contiguous = numbered.every((item, idx) => item.index === firstIdx + idx)
  if (!contiguous) return text

  const parsedLabels = numbered.map(item => item.label)
  const suggestionSet = new Set(suggestions)
  const labelsMatch =
    parsedLabels.length === suggestions.length &&
    parsedLabels.every(label => suggestionSet.has(label)) &&
    suggestions.every(label => parsedLabels.includes(label))

  if (!labelsMatch) return text

  return lines.slice(0, firstIdx).join('\n').trimEnd()
}

// ── Landing Screen ────────────────────────────────────────────
const MOODS: { id: CeresMood; label: string; emoji: string }[] = [
  { id: 'angry', label: '烦躁', emoji: '😡' }, { id: 'sad', label: '低气压', emoji: '😕' }, { id: 'calm', label: '平静', emoji: '😐' }, { id: 'pleased', label: '不错', emoji: '🙂' }, { id: 'happy', label: '超开心', emoji: '😍' },
]

function LandingScreen({ onGoShelf, onDietPlan, activityBusy, activityError }: { onGoShelf: () => void; onDietPlan: () => void; activityBusy: boolean; activityError: string | null }) {
  const [activeMood, setActiveMood] = useState<CeresMood>('happy')
  const [moodMotion, setMoodMotion] = useState(0)

  return (
    <div className="home-atmosphere h-full overflow-y-auto scrollbar-hide">
      <div className="flex min-h-full flex-col justify-end">
      <section className="relative h-[326px] shrink-0 overflow-hidden px-5 pt-8">
        <div aria-hidden="true" className="absolute -left-16 bottom-14 h-36 w-56 rounded-[50%] bg-[#dfe8ff]" />
        <div aria-hidden="true" className="absolute -left-8 bottom-10 h-20 w-56 rounded-[50%] bg-[#385af2]" />
        <div aria-hidden="true" className="absolute right-[-22px] top-12 h-20 w-20 rounded-full bg-[#ffb18c]" />
        <div aria-hidden="true" className="absolute bottom-12 right-3 h-28 w-28 rounded-full bg-[#b8dd82]" />
        <div aria-hidden="true" className="absolute bottom-[82px] left-8 h-2.5 w-2.5 rounded-full bg-[#e97255] shadow-[13px_-13px_0_#e97255]" />
        <div className="absolute left-7 top-4 z-10 whitespace-nowrap text-[40px] font-normal leading-[1.16] tracking-[-0.035em] text-[#18251d]" style={{ fontFamily: "'ZCOOL KuaiLe', 'Noto Sans SC', sans-serif" }}>哈喽，<br/>Ceres的朋友!</div>
        <svg aria-hidden="true" className="absolute left-[226px] top-[106px] z-10" width="38" height="28" viewBox="0 0 38 28" fill="none"><path d="M2 4C8 2 15 6 16 13C17 20 25 23 35 20" stroke="#18251D" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="4 5" /></svg>
        <div className="absolute right-5 top-[82px] z-10 rotate-[8deg] drop-shadow-[0_13px_5px_rgba(57,93,40,0.18)]"><CeresMascot key={`${activeMood}-${moodMotion}`} size={174} mood={activeMood} animated /></div>
        <div aria-hidden="true" className="absolute bottom-[92px] right-[48px] h-8 w-4 rotate-[16deg] rounded-full bg-[#3d9a61]" />
      </section>

      <section className="shrink-0 px-6 pb-5">
        <h2 className="mb-3 flex items-center gap-2 text-[18px] font-bold tracking-[-0.04em] text-[#34463a]">今日心情 <DemoBadge /></h2>
        <div className="flex items-center justify-between">
          {MOODS.map(mood => {
            const selected = activeMood === mood.id
            return <button key={mood.id} aria-label={mood.label} onClick={() => { setActiveMood(mood.id); setMoodMotion(n => n + 1) }} className="grid h-[55px] w-[55px] place-items-center bg-transparent text-[43px] leading-none transition-transform active:scale-90" style={{ transform: selected ? 'translateY(-4px) scale(1.12)' : undefined, filter: selected ? 'drop-shadow(0 5px 5px rgba(49,86,60,0.24))' : 'drop-shadow(0 2px 3px rgba(67,75,57,0.10))' }}>{mood.emoji}</button>
          })}
        </div>
      </section>

      <section className="shrink-0 px-5 pb-4 pt-3">
        <div className="mb-3 flex items-center justify-between"><h2 className="flex items-center gap-2 text-[15px] font-semibold tracking-[-0.02em] text-[#26372c]"><span className="h-2 w-2 rounded-full bg-[#d6bded]"/>为你准备</h2><button className="text-[11px] font-semibold text-[#477950]">查看全部 ↗</button></div>
        {activityError && <p role="alert" className="mb-3 text-xs text-red-700">{activityError}</p>}
        <div className="grid grid-cols-2 gap-3">
          <button onClick={onDietPlan} disabled={activityBusy} aria-busy={activityBusy} className="relative h-[178px] overflow-hidden rounded-[25px] border-2 border-white bg-[#f3b18e] p-4 text-left shadow-[0_5px_0_#d7876c] transition-transform active:translate-y-1 active:shadow-none"><div aria-hidden="true" className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-[#f9e58d]"/><div aria-hidden="true" className="absolute -left-8 bottom-4 h-12 w-16 rotate-[-25deg] rounded-full bg-[#cf92e8]/60"/><span className="relative text-[10px] font-semibold text-[#7f3328]">轻盈计划</span><p className="relative mt-1 text-lg font-bold leading-none tracking-[-0.04em] text-[#522d27]">减脂餐</p><p className="relative mt-1 max-w-[95px] text-[10px] font-medium leading-snug text-[#794f45]">{activityBusy ? '正在读取活动商品…' : '成品轻食选购（演示）'}</p><div className="absolute -bottom-5 right-[-3px] scale-[0.86]"><DietBowlSVG /></div></button>
          <button onClick={onGoShelf} className="relative h-[178px] overflow-hidden rounded-[25px] border-2 border-white bg-[#c3e493] p-4 text-left shadow-[0_5px_0_#90b567] transition-transform active:translate-y-1 active:shadow-none"><div aria-hidden="true" className="absolute -left-5 -top-5 h-20 w-20 rounded-full bg-[#f7e666]"/><div aria-hidden="true" className="absolute right-4 top-12 h-12 w-5 rotate-[35deg] rounded-full bg-[#bca8ec]/70"/><span className="relative text-[10px] font-semibold text-[#356234]">当季鲜选</span><p className="relative mt-1 text-lg font-bold leading-none tracking-[-0.04em] text-[#244c2c]">生鲜采买</p><p className="relative mt-1 max-w-[95px] text-[10px] font-medium leading-snug text-[#527151]">当季食材一键备货</p><div className="absolute -bottom-5 right-[-4px] scale-[0.86]"><BasketSVG /></div></button>
        </div>
      </section>
      </div>
    </div>
  )
}

// ── Cart Drawer ───────────────────────────────────────────────
function CartDrawer({
  open,
  cart,
  onClose,
  onCheckout,
  onUpdateQty,
  loading,
  error,
}: {
  open: boolean
  cart: Cart | null
  onClose: () => void
  onCheckout: () => void
  onUpdateQty: (skuId: string, qty: number) => void
  loading: boolean
  error: string | null
}) {
  if (!open) return null
  return (
    <div className="absolute inset-0 z-30 flex flex-col justify-end bg-black/25" role="dialog" aria-label="购物车">
      <button type="button" className="absolute inset-0" aria-label="关闭购物车" onClick={onClose} />
      <aside className="relative max-h-[70vh] overflow-hidden rounded-t-[28px] bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="text-[17px] font-semibold tracking-[-0.04em] text-[#1d1c1a]">购物车</h3>
          <button type="button" onClick={onClose} className="grid h-8 w-8 place-items-center rounded-full bg-[#f2f1ed] text-black/50 active:scale-90">✕</button>
        </div>
        <div className="scrollbar-hide max-h-[50vh] overflow-y-auto px-5 py-3">
          {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
          {!cart?.items.length && <p className="py-8 text-center text-sm text-black/40">购物车是空的</p>}
          {cart?.items.map((item) => (
            <div key={item.sku_id} className="flex items-center gap-3 border-b border-black/[0.05] py-3 last:border-0">
              <img src={productImageUrl(item.image_path)} alt="" className="h-12 w-12 rounded-xl object-cover bg-[#f2f2f4]" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-medium text-[#1d1c1a]">{item.name}</p>
                <p className="text-[12px] text-black/45">{yuan(item.unit_price_fen)}</p>
              </div>
              <div className="flex items-center gap-2">
                <button type="button" disabled={loading} onClick={() => onUpdateQty(item.sku_id, item.quantity - 1)} className="grid h-7 w-7 place-items-center rounded-full bg-[#f2f1ed] text-sm active:scale-90">−</button>
                <span className="w-5 text-center text-sm font-semibold">{item.quantity}</span>
                <button type="button" disabled={loading} onClick={() => onUpdateQty(item.sku_id, item.quantity + 1)} className="grid h-7 w-7 place-items-center rounded-full bg-[#f2f1ed] text-sm active:scale-90">+</button>
              </div>
            </div>
          ))}
        </div>
        {cart && cart.items.length > 0 && (
          <div className="border-t px-5 py-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-black/50">合计</span>
              <span className="text-[17px] font-bold tracking-[-0.03em]">{yuan(cart.total_price_fen)}</span>
              <button disabled={loading} onClick={onCheckout} className="rounded-full bg-[#171716] px-4 py-2 text-sm text-white disabled:opacity-40">模拟结算</button>
            </div>
          </div>
        )}
      </aside>
    </div>
  )
}

// ── Shelf Screen ──────────────────────────────────────────────
function ProductCard({ p, onAdd, adding }: { p: Product; onAdd: (skuId: string) => void; adding: boolean }) {
  const [liked, setLiked] = useState(false)
  const displayName = p.name_zh || p.name
  const unitLabel = p.spec_unit ? `/${p.spec_unit}` : ''
  return (
    <article className="group flex flex-col overflow-hidden rounded-[22px] border border-black/[0.06] bg-white transition-colors duration-200 hover:border-black/[0.13]">
      <div className="relative aspect-[1/0.91] overflow-hidden bg-[#f2f2f4]">
        <img src={productImageUrl(p.image_path)} alt={displayName} className="h-full w-full object-cover" loading="lazy" />
        <span className="absolute left-3 top-3 rounded-md bg-white/95 px-2 py-1 text-[9px] font-medium tracking-[0.02em] text-[#5f655f]">产地可溯源</span>
        <button onClick={() => setLiked(v => !v)} aria-label={liked ? `取消收藏${displayName}` : `收藏${displayName}`} className="absolute right-3 top-3 grid h-8 w-8 place-items-center rounded-full bg-white/95 text-[15px] text-[#4c554c] transition active:scale-90">
          {liked ? '♥' : '♡'}
        </button>
        <span className="absolute right-1 top-10 scale-90"><DemoBadge /></span>
      </div>
      <div className="flex flex-col gap-1.5 px-4 pb-4 pt-3.5">
        <p className="line-clamp-2 text-[14px] font-semibold leading-tight text-[#20211f]">{displayName}</p>
        <div className="flex items-center gap-1 text-[10px] font-medium tracking-[0.01em] text-[#8a8d85]"><span className="text-[#d98a37]">★</span> 4.9 <span className="text-[#c7c8c1]">·</span> 今日采摘</div>
        <div className="mt-1.5 flex items-center justify-between">
          <span className="text-[15px] font-extrabold tracking-tight text-[#171816]" style={{ fontFamily: "'Instrument Sans', 'Noto Sans SC', sans-serif" }}>
            {yuan(p.price_fen ?? 0)}
            {unitLabel && <em className="ml-1 text-[10px] not-italic font-medium text-[#94968f]">{unitLabel}</em>}
          </span>
          <button
            onClick={() => onAdd(p.sku_id)}
            disabled={adding || !p.sellable}
            aria-label={`添加${displayName}到购物车`}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-[#191a18] transition-all duration-200 active:scale-90 disabled:opacity-40"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
          </button>
        </div>
      </div>
    </article>
  )
}

function ShelfScreen({
  cart,
  cartCount,
  onCartChange,
  onViewOrders,
  onCategoryChange,
  onSearchChange,
}: {
  cart: Cart | null
  cartCount: number
  onCartChange: (cart: Cart) => void
  onViewOrders: () => void
  onCategoryChange: (categoryId: string | null) => void
  onSearchChange?: (query: string) => void
}) {
  const [categories, setCategories] = useState<Category[]>([])
  const [activeCat, setActiveCat] = useState<string | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cartOpen, setCartOpen] = useState(false)
  const [checkoutOpen, setCheckoutOpen] = useState(false)
  const [cartBusy, setCartBusy] = useState(false)
  const [cartError, setCartError] = useState<string | null>(null)
  const [addingSku, setAddingSku] = useState<string | null>(null)
  const productsRef = useRef<HTMLDivElement>(null)

  const PROMO_CARDS = [
    {
      categoryId: 'vegetable',
      tag: '绿色餐桌计划',
      title: '有机蔬菜',
      subtitle: '全场 88 折',
      image: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500&h=300&fit=crop&auto=format',
      gradient: 'from-[#173321]/85 via-[#173321]/42 to-transparent',
      tagColor: 'text-[#d9efbd]',
    },
    {
      categoryId: 'meat',
      tag: '限时会员价',
      title: '牧场鲜肉',
      subtitle: '买二减一',
      image: 'https://images.unsplash.com/photo-1603048297172-c92544798d5a?w=500&h=300&fit=crop&auto=format',
      gradient: 'from-[#4f251d]/85 via-[#4f251d]/42 to-transparent',
      tagColor: 'text-[#ffe0c5]',
    },
  ] as const

  function jumpToCategory(categoryId: string) {
    const target =
      categories.find((c) => c.id === categoryId)?.id ??
      categories.find((c) => c.id.includes(categoryId) || c.name_zh.includes(categoryId === 'vegetable' ? '蔬菜' : '肉'))?.id ??
      categoryId
    setSearch('')
    onSearchChange?.('')
    setActiveCat(target)
    onCategoryChange(target)
    requestAnimationFrame(() => {
      productsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }

  const loadProducts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listProducts({
        category_id: search ? undefined : activeCat ?? undefined,
        q: search || undefined,
        page_size: 40,
      })
      setProducts(res.items)
    } catch {
      setError('商品加载失败')
      setProducts([])
    } finally {
      setLoading(false)
    }
  }, [activeCat, search])

  useEffect(() => {
    listCategories()
      .then((cats) => {
        setCategories(cats)
        if (cats.length) {
          setActiveCat((prev) => {
            const next = prev ?? cats[0].id
            if (!prev) onCategoryChange(cats[0].id)
            return next
          })
        }
      })
      .catch(() => setError('分类加载失败'))
  }, [onCategoryChange])

  useEffect(() => { loadProducts() }, [loadProducts])

  async function handleAdd(skuId: string) {
    if (!cart) return
    setAddingSku(skuId)
    setCartError(null)
    try {
      const next = await addCartItem(skuId, 1, cart.version)
      onCartChange(next)
    } catch (e) {
      if (e instanceof ApiError && e.code === 'STALE_STATE') {
        const fresh = await getCart()
        onCartChange(fresh)
        setCartError('购物车已更新，请重试')
      } else {
        setCartError(e instanceof Error ? e.message : '加购失败')
      }
    } finally {
      setAddingSku(null)
    }
  }

  async function handleUpdateQty(skuId: string, qty: number) {
    if (!cart) return
    setCartBusy(true)
    setCartError(null)
    try {
      const next = await patchCartItem(skuId, qty, cart.version)
      onCartChange(next)
    } catch (e) {
      if (e instanceof ApiError && e.code === 'STALE_STATE') {
        const fresh = await getCart()
        onCartChange(fresh)
        setCartError('购物车已更新，请重试')
      } else {
        setCartError(e instanceof Error ? e.message : '更新失败')
      }
    } finally {
      setCartBusy(false)
    }
  }

  return (
    <div className="relative flex h-full flex-col overflow-hidden bg-[#f5f5f7]">
      <header className="z-10 flex-shrink-0 border-b border-black/[0.05] bg-[#f5f5f7] px-5 pb-3 pt-5">
        <div className="mb-4 flex items-center justify-between">
          <button className="flex items-center gap-1 text-[18px] font-extrabold tracking-[-0.07em] text-[#22231f]">静安区 <span className="mt-0.5 text-[11px] font-semibold text-black/35">⌄</span></button>
          <div className="flex items-center gap-2">
            <button aria-label="通知" className="grid h-9 w-9 place-items-center rounded-full bg-white text-[#626560] transition active:scale-90"><IconBell /></button>
            <button aria-label="购物车" onClick={() => setCartOpen(true)} className="relative grid h-9 w-9 place-items-center rounded-full bg-[#1d1d1f] text-white transition active:scale-90">
              <IconCart />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-[17px] min-w-[17px] items-center justify-center rounded-full bg-[#df7f51] px-1 text-[9px] font-extrabold text-white">
                  {cartCount}
                </span>
              )}
            </button>
          </div>
        </div>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#78917d]"><IconSearch /></div>
          <input value={search} onChange={e => { setSearch(e.target.value); onSearchChange?.(e.target.value) }} placeholder="搜索有机食材与好物" className="w-full rounded-2xl bg-white py-3.5 pl-10 pr-4 text-xs font-semibold text-[#30312d] outline-none transition placeholder:text-[#9a9a91] focus:ring-2 focus:ring-[#8ebc9a]" />
        </div>
      </header>

      <div className="z-10 flex-shrink-0 px-5 pt-3">
        <div className="flex gap-2 overflow-x-auto py-3 scrollbar-hide">
          {categories.map((cat) => {
            const isActive = cat.id === activeCat
            const emoji = categoryEmoji(cat.id)
            return (
              <button
                key={cat.id}
                onClick={() => { setActiveCat(cat.id); onCategoryChange(cat.id) }}
                aria-pressed={isActive}
                className={`group relative flex w-[68px] flex-shrink-0 flex-col items-center gap-2 bg-transparent pb-1 outline-none transition duration-200 ease-out active:scale-[0.98] ${isActive ? '-translate-y-0.5' : 'hover:-translate-y-px'}`}
              >
                <span className={`grid h-[58px] w-[58px] place-items-center rounded-[20px] bg-[#f5f5f7] transition-all duration-200 ${isActive ? 'shadow-[0_5px_10px_rgba(29,29,31,0.12),0_1px_2px_rgba(29,29,31,0.06)]' : 'shadow-[0_0_0_1px_rgba(245,245,247,0.6)] group-hover:shadow-[0_3px_7px_rgba(29,29,31,0.05)]'}`}>
                  <span className={`text-[30px] leading-none transition-transform duration-200 ${isActive ? 'scale-[1.04]' : 'grayscale-[0.08] group-hover:scale-[1.02]'}`}>{emoji}</span>
                </span>
                <span className={`relative w-full truncate text-center text-[12px] font-semibold tracking-[-0.05em] transition-colors duration-200 ${isActive ? 'text-[#252622]' : 'text-[#8c8d87] group-hover:text-[#596158]'}`}>
                  {cat.name_zh || cat.name}
                  <span aria-hidden="true" className={`absolute -bottom-1.5 left-1/2 h-[2px] -translate-x-1/2 rounded-full bg-[#252622] transition-all duration-300 ${isActive ? 'w-4 opacity-100' : 'w-0 opacity-0'}`} />
                </span>
              </button>
            )
          })}
        </div>
      </div>

      <div className="z-10 flex-1 overflow-y-auto scrollbar-hide px-5 pt-4 pb-6">
        {!search && (
          <section className="mb-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-[19px] font-semibold tracking-[-0.06em] text-[#202124]">今日精选 <DemoBadge /></h2>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {PROMO_CARDS.map((card) => (
                <button
                  key={card.categoryId}
                  type="button"
                  onClick={() => jumpToCategory(card.categoryId)}
                  className="relative h-[7.25rem] overflow-hidden rounded-[20px] p-3.5 text-left text-white transition active:scale-[0.98]"
                >
                  <img
                    src={card.image}
                    alt={card.title}
                    className="absolute inset-0 h-full w-full object-cover"
                    loading="lazy"
                  />
                  <div className={`absolute inset-0 bg-gradient-to-r ${card.gradient}`} />
                  <p className={`relative text-[10px] font-semibold ${card.tagColor}`}>{card.tag}</p>
                  <p className="relative mt-1 text-sm font-bold leading-tight tracking-[-0.04em]">
                    {card.title}
                    <br />
                    {card.subtitle}
                  </p>
                </button>
              ))}
            </div>
          </section>
        )}
        <div ref={productsRef} className="mb-3 flex items-end justify-between">
          <div>
            <h2 className="text-[19px] font-semibold tracking-[-0.06em] text-[#202124]">{search ? '搜索结果' : '人气鲜品'}</h2>
            <p className="mt-0.5 text-[10px] font-medium tracking-[0.02em] text-[#7c7c80]">最快 30 分钟送达</p>
          </div>
          <button className="flex items-center gap-1 rounded-full border border-black/[0.08] bg-transparent px-3.5 py-2 text-[10px] font-medium text-[#505055] transition active:scale-95">综合排序⌄ <DemoBadge /></button>
        </div>
        {error && (
          <div className="mb-4 rounded-2xl bg-red-50 px-4 py-3 text-center">
            <p className="text-sm text-red-700">{error}</p>
            <button type="button" onClick={loadProducts} className="mt-2 text-xs font-semibold text-red-800 underline">重试</button>
          </div>
        )}
        {loading && <p className="py-8 text-center text-sm text-black/40">加载中…</p>}
        {!loading && !error && products.length === 0 && <p className="py-8 text-center text-sm text-black/40">暂无商品</p>}
        <div className="grid grid-cols-2 gap-3">
          {products.map(p => (
            <ProductCard key={p.sku_id} p={p} onAdd={handleAdd} adding={addingSku === p.sku_id} />
          ))}
        </div>
      </div>
      <CartDrawer onCheckout={() => { setCartOpen(false); setCheckoutOpen(true) }} open={cartOpen} cart={cart} onClose={() => setCartOpen(false)} onUpdateQty={handleUpdateQty} loading={cartBusy} error={cartError} />
      {checkoutOpen && <SimulatedCheckout onCartChange={onCartChange} onClose={() => setCheckoutOpen(false)} onViewOrders={() => { setCheckoutOpen(false); onViewOrders() }} />}
    </div>
  )
}

// ── Guide floating sheets ─────────────────────────────────────
type GuideSheet = 'activity' | 'plan' | 'cart'

function SheetCloseButton({ onClose }: { onClose: () => void }) {
  return (
    <button
      type="button"
      onClick={onClose}
      aria-label="关闭"
      className="absolute right-3 top-3 z-10 grid h-[22px] w-[22px] place-items-center rounded-full bg-black/[0.06] text-black/40 backdrop-blur-sm transition hover:bg-black/[0.09]"
    >
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
    </button>
  )
}

function ChatFloatingSheet({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="guide-sheet-enter absolute inset-x-0 bottom-full z-10 mb-2 px-4">
      <div className="relative flex flex-col overflow-hidden rounded-[24px] bg-[#fcfbf8]">
        <SheetCloseButton onClose={onClose} />
        {children}
      </div>
    </div>
  )
}

function GuideSheetItemList({ itemCount, children }: { itemCount: number; children: React.ReactNode }) {
  const scrollable = itemCount > 2
  return (
    <div
      className={`space-y-2 px-4 pb-2 ${
        scrollable ? 'guide-sheet-scroll max-h-[148px] overflow-y-auto pr-1.5' : ''
      }`}
    >
      {children}
    </div>
  )
}

function ChatGuideCapsules({
  openSheet,
  onToggle,
  planCount,
  cartCount,
  navigation,
}: {
  openSheet: GuideSheet | null
  onToggle: (sheet: GuideSheet) => void
  planCount: number
  cartCount: number
  navigation?: RoleChatNavigationProps
}) {
  const countBadge = (count: number) =>
    count > 0 ? (
      <span className="grid h-[18px] min-w-[18px] place-items-center rounded-full bg-[#e23b3b] px-1 text-[10px] font-semibold leading-none text-white">
        {count}
      </span>
    ) : null

  return (
    <div className="scrollbar-hide mb-2 flex gap-2 overflow-x-auto pb-0.5">
      <button type="button" onClick={() => onToggle('activity')} className={composerToolChipClass(openSheet === 'activity')}>
        今日活动
      </button>
      <button type="button" onClick={() => onToggle('plan')} className={composerToolChipClass(openSheet === 'plan')} aria-label={planCount > 0 ? `采购清单 ${planCount} 件` : '采购清单'}>
        采购清单
        {countBadge(planCount)}
      </button>
      <button type="button" onClick={() => onToggle('cart')} className={composerToolChipClass(openSheet === 'cart')} aria-label={cartCount > 0 ? `购物车 ${cartCount} 件` : '购物车'}>
        购物车
        {countBadge(cartCount)}
      </button>
      {navigation && (
        <button
          type="button"
          aria-label="售后问题，联系墨墨"
          disabled={navigation.navigationBusy || !navigation.navigationReady}
          onClick={() => navigation.onSwitchRole('momo')}
          className={composerToolChipClass(false)}
        >
          <MomoAvatar size={20} />
          售后问题
        </button>
      )}
    </div>
  )
}

function PlanRowCheckbox({ checked, disabled, onToggle }: { checked: boolean; disabled: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      disabled={disabled}
      onClick={onToggle}
      className={`grid h-5 w-5 shrink-0 place-items-center rounded-full transition ${
        checked ? 'bg-[#171716] text-white' : 'bg-white/80 ring-1 ring-black/12'
      }`}
    >
      {checked && (
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><polyline points="20 6 9 17 4 12" /></svg>
      )}
    </button>
  )
}

function ActivitySheetContent() {
  return (
    <div className="flex min-h-[120px] items-center justify-center px-6 py-10">
      <p className="text-[12px] font-medium text-black/35">今日暂无活动</p>
    </div>
  )
}

function PlanEmptySheetContent() {
  return (
    <div className="flex min-h-[120px] items-center justify-center px-6 py-10">
      <p className="text-[12px] font-medium text-black/35">还没有采购清单</p>
    </div>
  )
}

function CartEmptySheetContent() {
  return (
    <div className="flex min-h-[120px] items-center justify-center px-6 py-10">
      <p className="text-[12px] font-medium text-black/35">购物车是空的</p>
    </div>
  )
}

function PlanSheetContent({
  plan,
  onChangeDish,
  onChoosePartial,
  onChooseAlternative,
  onToggleItem,
  onChangeQuantity,
  onAcceptQuote,
  onAddItem,
  confirming,
  canConfirm,
  typing,
  onConfirm,
}: {
  plan: PlanResponse
  onChangeDish: (changes: {people?: number; selections?: Record<string,string>; group_id?: string; remove_group?: boolean}) => void
  onChoosePartial: () => void
  onChooseAlternative: (gapId: string, alternativeIndex: number) => void
  onToggleItem: (skuId: string) => void
  onChangeQuantity: (skuId: string, quantity: number) => void
  onAcceptQuote: () => void
  onAddItem: (skuId: string) => void
  confirming: boolean
  canConfirm: boolean
  typing: boolean
  onConfirm: () => void
}) {
  const peopleInput = useRef<HTMLInputElement>(null)
  const gaps = plan.gaps?.filter(g => g.message) ?? []
  const total = plan.items
    .filter((item) => item.selected !== false)
    .reduce((sum, item) => sum + remainingQuantity(item) * item.unit_price_fen, 0)
  const hasConfirmable = confirmableItems(plan.items).length > 0
  return (
    <div className="flex flex-col pt-4">
      <p className="px-5 pb-2 text-[12px] font-semibold tracking-[-0.02em] text-[#1d1c1a]">{plan.plan_kind === 'supply_preview' ? '供给预览' : plan.plan_kind === 'partial_purchase' ? '部分采购清单' : '采购清单'}</p>
      {plan.budget_quote && <div className="mx-5 mb-3 rounded-xl bg-amber-50 p-3 text-[11px]">
        <p>当前预算 {yuan(plan.budget_quote.budget_fen)} · 本方案报价 {yuan(plan.budget_quote.total_fen)}</p>
        <p>接受报价只更新任务预算，仍需另行确认加购。</p>
        <button type="button" disabled={confirming || typing} onClick={onAcceptQuote} className="mt-2 rounded-full bg-black/5 px-3 py-2">接受报价 {yuan(plan.budget_quote.total_fen)}，更新预算</button>
      </div>}
      {plan.history_source && <div className="mx-5 mb-3 rounded-xl bg-amber-50 p-3 text-[11px]"><p>历史来源：{plan.history_source.goal || plan.history_source.task_id}</p>{plan.history_changes?.map((change,index) => <p key={index}>{change}</p>)}{plan.history_memory?.map(memory => <p key={memory.memory_id}>当前有效偏好：{memory.content}</p>)}</div>}
      {plan.dish && <p className="px-5 pb-2 text-[11px] text-black/50">{plan.dish.name} · {plan.dish.people_source === 'default' ? `菜谱默认基准 ${plan.dish.base_people} 人用量（非指定人数）` : `用户指定 ${plan.dish.people} 人，菜谱基准 ${plan.dish.base_people} 人`}</p>}
      {plan.dish && <form className="flex items-center gap-2 px-5 pb-2" onSubmit={event => {event.preventDefault(); const people = Number(peopleInput.current?.value); if (Number.isInteger(people) && people > 0) onChangeDish({people})}}>
        <label className="text-[11px]">人数 <input key={plan.plan_version} ref={peopleInput} aria-label="单菜人数" type="number" min="1" step="1" required defaultValue={plan.dish.people} disabled={confirming || typing} className="w-14 rounded border px-2 py-1" /></label>
        <button type="submit" disabled={confirming || typing} className="rounded-full bg-black/5 px-3 py-1 text-[11px]">更新人数</button>
      </form>}
      {(plan.groups?.length ?? 0) > 1 && plan.groups!.map(group => <fieldset key={group.group_id} disabled={confirming || typing} className="mx-5 mb-3 rounded-xl bg-black/[0.03] p-3">
        <legend className="text-[12px] font-medium">{group.name}</legend>
        <p className="text-[10px] text-black/50">{group.people_source === 'default' ? `菜谱默认基准 ${group.base_people} 人用量（非指定人数）` : `用户指定 ${group.people} 人，菜谱基准 ${group.base_people} 人`}</p>
        <form className="mt-2 flex items-center gap-2" onSubmit={event => {event.preventDefault(); const input = event.currentTarget.elements.namedItem('people') as HTMLInputElement; const people = Number(input.value); if (Number.isInteger(people) && people > 0) onChangeDish({group_id:group.group_id,people})}}>
          <label className="text-[11px]">人数 <input key={plan.plan_version} name="people" aria-label={`分组人数 ${group.group_id}`} type="number" min="1" step="1" required defaultValue={group.people} className="w-14 rounded border px-2 py-1" /></label>
          <button aria-label={`更新分组人数 ${group.group_id}`} type="submit" className="rounded-full bg-black/5 px-3 py-1 text-[11px]">更新人数</button>
        </form>
        {plan.items.filter(item => item.contributions?.some(c => c.group_id === group.group_id)).map(item => {
          const contribution = item.contributions!.find(c => c.group_id === group.group_id)!
          return <div key={item.sku_id} className="mt-1 text-[10px] text-black/50">
            {item.name}：{contribution.requirement?.quantity ?? '用量未知'}{contribution.requirement?.unit ?? ''}
            {(item.available_specs?.length ?? 0) > 1 && contribution.ingredient_id && <select aria-label={`分组规格 ${group.group_id} ${contribution.ingredient_id}`} value={item.sku_id} onChange={event => onChangeDish({group_id:group.group_id,selections:{[contribution.ingredient_id!]:event.target.value}})} className="ml-2 max-w-full rounded border">
              {item.available_specs!.map(option => <option key={option.sku_id} value={option.sku_id}>{option.name} · {option.spec_quantity ?? '未知'}{option.spec_unit ?? ''}</option>)}
            </select>}
          </div>
        })}
        <button aria-label={`移除分组 ${group.group_id}`} type="button" onClick={() => onChangeDish({group_id:group.group_id,remove_group:true})} className="mt-2 text-[10px] text-black/50">移除这道菜</button>
      </fieldset>)}
      {plan.groups?.length === 1 && <button aria-label={`移除分组 ${plan.groups[0].group_id}`} type="button" disabled={confirming || typing} onClick={() => onChangeDish({group_id:plan.groups![0].group_id,remove_group:true})} className="mb-2 px-5 text-left text-[10px] text-black/50">移除这道菜</button>}
      {plan.purchase_ledger?.map(record => <p key={`${record.operation_id}:${record.sku_id}`} className="px-5 pb-2 text-[10px] text-black/50">
        {record.groups.length > 1 ? '共同加购' : '分组已加购'}：{record.groups.map(group => group.name).join('、')} · {record.name} {record.added_quantity} 件（保留原购买来源；移除菜品不会移除购物车商品）
      </p>)}
      <GuideSheetItemList itemCount={plan.items.length}>
        {plan.items.map((item) => {
          const checked = item.selected !== false
          const packageUnit = item.spec_unit === 'kg' ? 'g' : item.spec_unit === 'l' ? 'ml' : item.spec_unit
          const packageAmount = (item.spec_quantity ?? 0) * (item.spec_unit === 'kg' || item.spec_unit === 'l' ? 1000 : 1)
          const contributions = item.contributions?.filter(c => c.selected !== false)
          const requirements = contributions?.length ? contributions.map(c => c.requirement) : [item.requirement]
          const compatible = requirements.filter(r => r?.quantity != null && r.unit === packageUnit)
          const requirementQuantity = compatible.reduce((sum, r) => sum + r!.quantity!, 0)
          const comparable = compatible.length > 0 && packageAmount > 0
          const purchased = ((item.added_quantity ?? 0) + (checked ? remainingQuantity(item) : 0)) * packageAmount
          const needed = packageUnit === 'pc' ? Math.ceil(requirementQuantity) : requirementQuantity
          const difference = purchased - needed
          const unitLabel = packageUnit === 'pc' ? '枚' : packageUnit
          return (
            <div
              key={item.sku_id}
              className={`flex items-center gap-2.5 rounded-[18px] px-2.5 py-2 transition-opacity ${
                checked ? 'bg-white/70' : 'bg-white/40 opacity-70'
              }`}
            >
              <PlanRowCheckbox checked={checked} disabled={confirming || typing || plan.plan_kind === 'supply_preview'} onToggle={() => onToggleItem(item.sku_id)} />
              <img src={productImageUrl(item.image_path)} alt="" className="h-11 w-11 shrink-0 rounded-xl bg-black/[0.04] object-cover" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[12px] font-medium text-[#1d1c1a]">{item.name || item.sku_id}</p>
                <p className="mt-0.5 text-[10px] text-black/38">已加购 {item.added_quantity ?? 0} 件 · 本次选购 {checked ? remainingQuantity(item) : 0} 件</p>
                <form className="mt-1 flex items-center gap-1 text-[10px]" onSubmit={event => {
                  event.preventDefault()
                  const quantity = Number(new FormData(event.currentTarget).get('quantity'))
                  if (Number.isInteger(quantity) && quantity > 0) onChangeQuantity(item.sku_id, quantity)
                }}>
                  <label>购买数量 <input key={`${plan.plan_version}-${item.sku_id}`} name="quantity" aria-label={`购买数量 ${item.name || item.sku_id}`} type="number" min="1" step="1" required defaultValue={item.quantity} disabled={confirming || typing || plan.plan_kind === 'supply_preview'} className="w-12 rounded border px-1" /></label>
                  <button type="submit" aria-label={`更新数量 ${item.name || item.sku_id}`} disabled={confirming || typing || plan.plan_kind === 'supply_preview'} className="rounded bg-black/5 px-1 py-0.5">更新</button>
                </form>
                {item.sellable === false && <p className="mt-0.5 text-[10px] text-black/45">当前不可售；未选项不影响其余已选商品。</p>}
                {plan.dish && item.ingredient_id && (item.available_specs?.length ?? 0) > 1 && <select aria-label={`规格 ${item.name || item.sku_id}`} value={item.sku_id} disabled={confirming || typing} onChange={event => onChangeDish({selections:{[item.ingredient_id!]:event.target.value}})} className="mt-1 max-w-full rounded border text-[10px]">
                  {item.available_specs!.map(option => <option key={option.sku_id} value={option.sku_id}>{option.name} · {option.spec_quantity ?? '未知'}{option.spec_unit ?? ''}</option>)}
                </select>}
                {item.role === 'pantry' && item.requirement?.quantity == null && <p className="mt-0.5 text-[10px] text-black/45">用量未知；未选不代表家中已有，勾选为购买整包。</p>}
                {comparable && (
                  <p className="mt-0.5 text-[10px] leading-snug text-black/45">
                    需求 {requirementQuantity}{unitLabel}{packageUnit === 'pc' && needed !== requirementQuantity ? `（整枚 ${needed}）` : ''} · 采购覆盖 {purchased}{unitLabel} · {difference >= 0 ? '包装余量' : '本次未覆盖'} {Math.abs(difference)}{unitLabel}
                  </p>
                )}
                {requirements.filter(r => r?.source?.original_quantity != null).map((r, index) => (
                  <p key={index} className="mt-0.5 text-[10px] leading-snug text-black/38">
                    菜谱原需 {r!.source!.original_quantity}{r!.source!.original_unit === 'pc' ? '枚' : r!.source!.original_unit}，本规格分担 {r!.quantity}{unitLabel}
                  </p>
                ))}
                {(item.contributions?.length ?? 0) > 1 && item.contributions!.map(c => (
                  <p key={c.group_id} className="mt-0.5 text-[10px] leading-snug text-black/38">
                    {plan.targets?.find(t => t.group_id === c.group_id)?.name ?? c.group_id}：{c.requirement?.quantity ?? '用量未明确'}{c.requirement?.unit === 'pc' ? '枚' : c.requirement?.unit}
                  </p>
                ))}
              </div>
              <span className="shrink-0 text-[12px] font-medium text-black/55">{yuan(checked ? remainingQuantity(item) * item.unit_price_fen : 0)}</span>
              <button type="button" aria-label={`加购 ${item.name || item.sku_id}`} disabled={confirming || typing || !canConfirm || !checked || remainingQuantity(item) <= 0} onClick={() => onAddItem(item.sku_id)} className="rounded-full px-2 py-1 text-[10px] text-black/60 disabled:opacity-30">加购此项</button>
            </div>
          )
        })}
      </GuideSheetItemList>
      {plan.items.some(item => item.role === 'required' && item.selected === false) && (
        <p className="px-5 pb-1 text-[10px] leading-snug text-black/45">未选的必需食材不会加购；当前仅采购勾选部分。</p>
      )}
      {plan.plan_kind === 'supply_preview' && <div className="px-5 py-2 text-[11px]"><p>必需食材尚未配齐。选择当前可售部分后，还需要独立确认加购。</p><button type="button" disabled={confirming || typing} onClick={onChoosePartial} className="mt-2 rounded-full bg-black/5 px-3 py-2">选择可售部分</button></div>}
      {plan.plan_kind === 'partial_purchase' && <p className="px-5 py-2 text-[11px]">已明确选择部分采购；缺项仍保留，不代表已配齐整道菜。</p>}
      {gaps.map((g) => (
        <div key={g.gap_id} className="px-5 pb-1 text-[10px] leading-snug text-black/45"><p>{g.message}</p><p>{g.group_ids?.map(id => plan.groups?.find(group => group.group_id === id)?.name ?? id).join("、")}</p>
          {plan.plan_kind === 'supply_preview' && g.alternatives?.map((option,index) => <button type="button" key={index} aria-label={`选择替代 ${g.gap_id} ${index}`} disabled={confirming || typing} onClick={() => onChooseAlternative(g.gap_id,index)} className="my-1 block rounded border px-2 py-1 text-left">
            选择替代：{option.items.map(item => `${item.sku_id} × ${item.quantity} 件`).join(' + ')} · 整项 {yuan(option.total_price_fen)} · 余量 {option.leftover_quantity}{g.requirement?.unit ?? ''}
          </button>)}
        </div>
      ))}
      <div className="flex items-center justify-between px-5 py-3">
        <span className="text-[13px] font-semibold tracking-[-0.03em] text-[#1d1c1a]">{yuan(total)}</span>
        <button
          type="button"
          disabled={confirming || typing || !canConfirm || !hasConfirmable}
          onClick={onConfirm}
          className="rounded-full bg-[#171716] px-4 py-2 text-[11px] font-semibold text-white disabled:opacity-50"
        >
          {confirming ? '处理中…' : '确认加购'}
        </button>
      </div>
    </div>
  )
}

function CartSheetContent({
  cart,
  busy,
  error,
  onUpdateQty,
  onCheckout,
}: {
  cart: Cart
  busy: boolean
  error: string | null
  onUpdateQty: (skuId: string, qty: number) => void
  onCheckout: () => void
}) {
  return (
    <div className="flex flex-col pt-4">
      <p className="px-5 pb-2 text-[12px] font-semibold tracking-[-0.02em] text-[#1d1c1a]">购物车</p>
      <GuideSheetItemList itemCount={cart.items.length}>
        {cart.items.map((item) => (
          <div key={item.sku_id} className="flex items-center gap-3 rounded-[18px] bg-white/55 px-2.5 py-2">
            <img src={productImageUrl(item.image_path)} alt="" className="h-11 w-11 shrink-0 rounded-xl bg-black/[0.04] object-cover" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-[12px] font-medium text-[#1d1c1a]">{item.name}</p>
              <p className="mt-0.5 text-[10px] text-black/38">{yuan(item.line_total_fen)}</p>
            </div>
            <button type="button" disabled={busy} onClick={() => onUpdateQty(item.sku_id, item.quantity - 1)} className="grid h-6 w-6 place-items-center rounded-full bg-black/[0.05] text-sm text-black/55">−</button>
            <span className="w-4 text-center text-[12px] font-semibold text-[#1d1c1a]">{item.quantity}</span>
            <button type="button" disabled={busy} onClick={() => onUpdateQty(item.sku_id, item.quantity + 1)} className="grid h-6 w-6 place-items-center rounded-full bg-black/[0.05] text-sm text-black/55">+</button>
          </div>
        ))}
      </GuideSheetItemList>
      {error && <p className="px-5 pb-1 text-[10px] text-red-600">{error}</p>}
      <div className="flex items-center justify-between px-5 py-3">
        <span className="text-[13px] font-semibold tracking-[-0.03em] text-[#1d1c1a]">{yuan(cart.total_price_fen)}</span>
        <button
          type="button"
          disabled={busy}
          onClick={onCheckout}
          className="rounded-full bg-[#171716] px-4 py-2 text-[11px] font-semibold text-white disabled:opacity-50"
        >
          结算
        </button>
      </div>
    </div>
  )
}

// ── Chat Screen ───────────────────────────────────────────────

function ChatScreen({
  viewContext,
  onCartRefresh,
  cart,
  onCartChange,
  onViewOrders,
  beforeText,
  handoff,
  onHandoffDone,
  active,
  interactionEpoch,
  interactionVersion,
  onInteraction,
  navigation,
}: {
  active: boolean
  interactionEpoch: {current: number}
  interactionVersion: number
  onInteraction: () => number
  beforeText: BeforeText
  handoff?: Handoff | null
  onHandoffDone: () => void
  viewContext: { page: string; category_id?: string | null }
  onCartRefresh: () => void
  cart: Cart | null
  onCartChange: (cart: Cart) => void
  onViewOrders: () => void
  navigation?: RoleChatNavigationProps
}) {
  const [msgs, setMsgs] = useState<Msg[]>([WELCOME_MSG])
  const [input, setInput] = useState('')
  const [typing, setTyping] = useState(false)
  const [restoring, setRestoring] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [stateVersion, setStateVersion] = useState(0)
  const [sessionVersion, setSessionVersion] = useState(0)
  const [plan, setPlan] = useState<PlanResponse | null>(null)
  const [historySources, setHistorySources] = useState<HistorySource[] | null>(null)
  const [historyReminder, setHistoryReminder] = useState<HistoryReminder | null>(null)
  const [canConfirm, setCanConfirm] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [questionBusy, setQuestionBusy] = useState(false)
  const [progressText, setProgressText] = useState<string | null>(null)
  const [cartBusy, setCartBusy] = useState(false)
  const [cartError, setCartError] = useState<string | null>(null)
  const [checkoutPhase, setCheckoutPhase] = useState<'checkout' | null>(null)
  const [openSheet, setOpenSheet] = useState<GuideSheet | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const streamRef = useRef(new Map<string, AbortController>())
  const phaseRef = useRef(new Map<string, string>())
  const [activeRequests, setActiveRequests] = useState<string[]>([])
  const initializationRef = useRef(0)
  const snapshotSessionRef = useRef<string | null>(null)
  const snapshotOrderRef = useRef(0)
  const snapshotOrdersRef = useRef(new WeakMap<object, number>())
  const acceptedSnapshotRef = useRef<SessionResponse | null>(null)
  const acceptedSnapshotOrderRef = useRef(0)
  const readSnapshot = useCallback(async <T extends SessionResponse,>(request: Promise<T>): Promise<T> => {
    const order = ++snapshotOrderRef.current
    const snapshot = await request
    snapshotOrdersRef.current.set(snapshot, order)
    return snapshot
  }, [])
  const displayedPlanRef = useRef<DisplayedPlanRef | null>(null)
  const displayedCandidateRefs = useRef<string[]>([])
  const [pendingIntroduction, setPendingIntroduction] = useState<{source: IntroductionSource; snapshot: SessionResponse; epoch: number; viewKey: string} | null>(null)
  const [introductionStatus, setIntroductionStatus] = useState<string | null>(null)
  const introductionRef = useRef<{controller: AbortController; done: boolean} | null>(null)
  const activeRef = useRef(active)
  activeRef.current = active
  const viewKey = `${viewContext.page}:${viewContext.category_id ?? ''}`
  const viewKeyRef = useRef(viewKey)
  viewKeyRef.current = viewKey

  const queueIntroduction = useCallback((source: IntroductionSource, snapshot: SessionResponse, epoch: number) => {
    if (!activeRef.current || interactionEpoch.current !== epoch || acceptedSnapshotRef.current !== snapshot) return
    setPendingIntroduction({source, snapshot, epoch, viewKey})
  }, [interactionEpoch, viewKey])

  // Effects run after factual cards/plan/receipt have committed to the DOM.
  // Expression state never enters business typing, snapshots or write receipts.
  useEffect(() => {
    const pending = pendingIntroduction
    if (!pending || !active || typing || confirming || questionBusy || restoring ||
        pending.epoch !== interactionEpoch.current || pending.viewKey !== viewKey ||
        acceptedSnapshotRef.current !== pending.snapshot) return
    const entry = {controller: new AbortController(), done: false}
    introductionRef.current = entry
    const current = () => introductionRef.current === entry && !entry.controller.signal.aborted &&
      activeRef.current && interactionEpoch.current === pending.epoch &&
      viewKeyRef.current === pending.viewKey && acceptedSnapshotRef.current === pending.snapshot
    setIntroductionStatus('running')
    void runResultIntroduction(pending.snapshot.session_id, pending.source, {
      signal: entry.controller.signal,
      onDelta: (text, messageId, replace) => {
        if (!current()) return
        const id = messageId || `introduction-${pending.source.source_id}`
        setMsgs(messages => {
          if (!current()) return messages
          const prior = messages.find(message => message.id === id)
          const content = replace ? text : (prior?.text ?? '') + text
          return prior ? messages.map(message => message.id === id ? {...message, text: content} : message)
            : [...messages, {id, role: 'ai', text: content}]
        })
      },
    }).then(result => {
      if (current()) setIntroductionStatus(result?.expression_status ?? 'failed')
    }).catch(() => {
      if (current()) setIntroductionStatus('failed')
    }).finally(() => {
      entry.done = true
      if (introductionRef.current === entry) introductionRef.current = null
    })
    return () => {
      if (!entry.done) entry.controller.abort()
      if (introductionRef.current === entry) introductionRef.current = null
      setIntroductionStatus(null)
    }
  }, [pendingIntroduction, active, interactionVersion, interactionEpoch, viewKey, typing, confirming, questionBusy, restoring])

  function stopIntroduction() {
    introductionRef.current?.controller.abort()
    introductionRef.current = null
    setIntroductionStatus('stopped')
  }

  function showPurchaseReceipt(result: ConfirmResponse) {
    const id = `purchase-receipt-${result.confirmation_id}`
    const text = `模拟加购回执 ${result.confirmation_id}：本次加入 ${result.items_added.reduce((total, item) => total + item.quantity, 0)} 件销售包装。加购尚未下单或付款。`
    setMsgs(messages => messages.some(message => message.id === id)
      ? messages.map(message => message.id === id ? {...message, text} : message)
      : [...messages, {id, role: 'ai', text}])
  }

  useEffect(() => {
    displayedCandidateRefs.current = msgs.flatMap(message => message.productCards ?? []).map(card => card.ref)
  }, [msgs])

  useEffect(() => {
    displayedCandidateRefs.current = []
    setMsgs(current => current.map(message => ({...message, productCards:[]})))
  }, [viewContext.page, viewContext.category_id])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs, typing, plan, progressText, openSheet])

  useEffect(() => {
    if (!plan || !taskId) {
      displayedPlanRef.current = null
    } else if (openSheet === 'plan' && !checkoutPhase) {
      // Fetched state is not authority. Promote only after the factual sheet
      // has actually rendered; a later confirmation carries this exact ref.
      displayedPlanRef.current = {task_id:taskId,plan_id:plan.plan_id,plan_version:plan.plan_version,state_version:stateVersion,session_version:sessionVersion}
    }
  }, [plan, taskId, stateVersion, sessionVersion, openSheet, checkoutPhase])

  const applyAuthoritativeSnapshot = useCallback((snapshot: SessionResponse) => {
    if (snapshot.session_id !== snapshotSessionRef.current) return false
    // Candidate publication can keep the task anchor unchanged: compare read
    // admission order too, before touching cards or rendered confirmation facts.
    const current = acceptedSnapshotRef.current
    const order = snapshotOrdersRef.current.get(snapshot) ?? ++snapshotOrderRef.current
    if (current && (
      snapshot.session_version < current.session_version ||
      (snapshot.session_version === current.session_version && (
        snapshot.task_id !== current.task_id || snapshot.state_version < current.state_version ||
        (snapshot.state_version === current.state_version && order < acceptedSnapshotOrderRef.current)
      ))
    )) return false
    acceptedSnapshotRef.current = snapshot
    acceptedSnapshotOrderRef.current = order
    setHistoryReminder(snapshot.history_reminder ?? null)
    if (snapshot.question_history) {
      setMsgs(current => {
        const next = [...current]
        for (const question of snapshot.question_history ?? []) {
          const index = next.findIndex(message => message.id === question.question_id)
          const message: Msg = {id: question.question_id, role: 'ai', text: question.question, question}
          if (index >= 0) next[index] = {...next[index], ...message, suggestions: undefined}
          else next.push(message)
        }
        return next
      })
    }
    if (snapshot.product_cards) {
      const currentRefs = new Set(snapshot.product_cards.map(card => card.ref))
      setMsgs(current => current.map(message => ({...message, productCards:message.productCards?.filter(card => currentRefs.has(card.ref))})))
    }
    setTaskId(snapshot.task_id ?? null)
    setStateVersion(snapshot.state_version)
    setSessionVersion(snapshot.session_version)
    const canConfirmNow = snapshot.available_actions?.includes('confirm') ?? false
    setCanConfirm(canConfirmNow && snapshot.plan?.can_confirm !== false)
    const nextPlan = snapshot.available_actions?.includes('modify') ? (snapshot.plan ?? null) : null
    setPlan(nextPlan)
    const shown = displayedPlanRef.current
    if (nextPlan && snapshot.task_id && (!shown || shown.task_id !== snapshot.task_id || shown.plan_id !== nextPlan.plan_id || shown.plan_version !== nextPlan.plan_version || shown.state_version !== snapshot.state_version || shown.session_version !== snapshot.session_version)) {
      // In particular, an unrelated chat refresh must not silently authorize
      // another tab's newer plan. Show its facts before recording it as shown.
      setOpenSheet('plan')
    }
    return true
  }, [])

  const mergeTerminalTurn = useCallback((turn: TurnResponse, snapshot: SessionResponse, placeholderId: string) => {
    const accepted = applyAuthoritativeSnapshot(snapshot)
    const allowedRefs = new Set((acceptedSnapshotRef.current?.product_cards ?? []).map(card => card.ref))
    const replies = turn.messages ?? [{message_id:turn.assistant_message_id ?? placeholderId,content:turn.message}]
    setMsgs(current => {
      let next: Msg[] = current.filter(message => message.id !== placeholderId || replies.some(reply => reply.message_id === placeholderId)).map(message => ({...message, productCards:message.productCards?.filter(card => allowedRefs.has(card.ref))}))
      const chips = clarificationChipLabels(normalizePendingClarifications(turn.pending_clarifications ?? []))
      for (const [index, reply] of replies.entries()) {
        const question = acceptedSnapshotRef.current?.question_history?.find(item => item.question_id === reply.message_id)
        const message: Msg = {id:reply.message_id,role:'ai',text:question?.question ?? reply.content,question,generalExplanation:turn.answer_kind === 'general_explanation', ...(index === replies.length - 1 ? {suggestions:chips,productCards:turn.product_cards?.filter(card => allowedRefs.has(card.ref))} : {})}
        next = next.some(item => item.id === message.id) ? next.map(item => item.id === message.id ? message : item) : [...next,message]
      }
      return next
    })
    if (accepted && turn.history_sources?.length) setHistorySources(turn.history_sources)
    if (accepted && turn.plan_effect === 'replace') setHistorySources(null)
    return accepted
  }, [applyAuthoritativeSnapshot])

  const receiveDelta = useCallback((placeholderId: string, event: {payload?: Record<string, unknown>}) => {
    const payload = event.payload
    const delta = typeof payload?.delta === 'string' ? payload.delta : ''
    const messageId = typeof payload?.message_id === 'string' ? payload.message_id : placeholderId
    setMsgs(current => {
      const existing = current.find(message => message.id === messageId)
      const text = payload?.replace === true ? delta : (existing?.text ?? '') + delta
      if (existing) return current.map(message => message.id === messageId ? {...message,text,generalExplanation:payload?.answer_kind === 'general_explanation'} : message)
      const placeholder = current.findIndex(message => message.id === placeholderId)
      if (placeholder >= 0) return current.map((message,index) => index === placeholder ? {id:messageId,role:'ai',text,generalExplanation:payload?.answer_kind === 'general_explanation'} : message)
      return [...current,{id:messageId,role:'ai',text,generalExplanation:payload?.answer_kind === 'general_explanation'}]
    })
  }, [])

  const updatePhase = useCallback((requestId: string, phase: string) => {
    phaseRef.current.set(requestId, progressPhaseLabel(phase))
    setProgressText(progressPhaseLabel(phase) || null)
  }, [])

  const finishTransport = useCallback((requestId: string) => {
    streamRef.current.delete(requestId)
    phaseRef.current.delete(requestId)
    setActiveRequests([...streamRef.current.keys()])
    setTyping(streamRef.current.size > 0)
    setProgressText([...phaseRef.current.values()].at(-1) || null)
  }, [])

  useEffect(() => () => {
    // Closing this panel closes transport only. The admitted server run keeps
    // its original bounded budget; only the explicit stop control cancels it.
    for (const controller of streamRef.current.values()) controller.abort()
    streamRef.current.clear()
  }, [])

  const initSession = useCallback(async () => {
    const generation = ++initializationRef.current
    setRestoring(true)
    setError(null)
    try {
      await ensureIdentity()
      if (generation !== initializationRef.current) return
      const session = await readSnapshot(createGuideSession({page: viewContext.page, category_id: viewContext.category_id ?? null}))
      if (generation !== initializationRef.current) return
      setSessionId(session.session_id)
      if (snapshotSessionRef.current !== session.session_id) {
        snapshotSessionRef.current = session.session_id
        acceptedSnapshotRef.current = null
        displayedPlanRef.current = null
      }
      const accepted = applyAuthoritativeSnapshot(session)
      const pending = normalizePendingClarifications(session.pending_clarifications ?? [])
      const chipLabels = clarificationChipLabels(pending)
      if (accepted && session.messages?.length) {
        const restored: Msg[] = session.messages
          .filter(m => m.role === 'user' || m.role === 'assistant')
          .map(m => ({
            id: m.message_id,
            role: m.role === 'user' ? 'user' : 'ai',
            text: session.question_history?.find(question => question.question_id === m.message_id)?.question ?? m.content,
            question: session.question_history?.find(question => question.question_id === m.message_id),
            generalExplanation: m.kind === 'general',
          }))
        if (restored.length) {
          if (chipLabels.length || session.product_cards?.length) {
            const lastAi = restored.map((m, index) => ({ m, index })).reverse().find(entry => entry.m.role === 'ai')
            if (lastAi) {
              restored[lastAi.index] = { ...restored[lastAi.index], suggestions: chipLabels,
                productCards: session.product_cards }
            }
          }
          setMsgs(restored)
        }
      }
      const status = await readSnapshot(getGuideStatus(session.session_id))
      if (generation !== initializationRef.current) return
      applyAuthoritativeSnapshot(status)
      const knownRequests = new Set((session.messages ?? []).filter(message => message.role === 'user').map(message => message.request_id))
      setMsgs(current => {
        const next = [...current]
        for (const run of [...status.runs].reverse()) {
          if (run.input.kind === 'result_introduction') continue
          if (run.input.message && !knownRequests.has(run.request_id) && !next.some(message => message.id === `u-${run.request_id}`)) next.push({id:`u-${run.request_id}`,role:'user',text:run.input.message})
          for (const message of run.result?.messages ?? []) {
            if (!next.some(item => item.id === message.message_id)) next.push({id:message.message_id,role:'ai',text:message.content,generalExplanation:run.result?.answer_kind === 'general_explanation'})
          }
          if (['failed','interrupted'].includes(run.status)) {
            const id = `status-${run.run_id}`
            if (!next.some(message => message.id === id)) next.push({id,role:'ai',text:run.result?.message ?? '这次处理没有完成，请决定是否继续。'})
          }
        }
        return next
      })
      for (const run of status.runs.filter(run => run.input.kind !== 'result_introduction' && (run.status === 'running' || run.status === 'stop_requested'))) {
        if (streamRef.current.has(run.request_id)) continue
        const controller = new AbortController()
        streamRef.current.set(run.request_id, controller)
        setActiveRequests([...streamRef.current.keys()])
        setTyping(true)
        const placeholderId = `a-${run.request_id}`
        setMsgs(current => [...current,{id:placeholderId,role:'ai',text:''}])
        void reconnectGuideRun(session.session_id, run.run_id, {
          signal:controller.signal,
          onProgress:event => updatePhase(run.request_id, String(event.payload?.phase ?? 'understanding')),
          onAnswerDelta:event => receiveDelta(placeholderId,event),
        }).then(async turn => {
          const snapshot = await readSnapshot(getGuideSession(session.session_id, false))
          if (!controller.signal.aborted) mergeTerminalTurn(turn, snapshot, placeholderId)
        }).catch(error => {
          if (!controller.signal.aborted) setError(error instanceof Error ? error.message : '运行恢复失败')
        }).finally(() => finishTransport(run.request_id))
      }
    } catch {
      if (generation !== initializationRef.current) return
      setSessionId(null)
      setError('会话恢复失败，请重试')
    } finally {
      if (generation === initializationRef.current) setRestoring(false)
    }
  }, [viewContext.category_id, viewContext.page, applyAuthoritativeSnapshot, mergeTerminalTurn, finishTransport, receiveDelta, updatePhase, readSnapshot])

  useEffect(() => { void initSession(); return () => { initializationRef.current += 1 } }, [initSession])

  const send = useCallback(async (text: string, routedRequestId?: string) => {
    if (!text.trim() || !sessionId || confirming || restoring) return
    const actionEpoch = onInteraction()
    const trimmed = text.trim()
    const requestId = routedRequestId ?? newRequestId()
    const routeId = routedRequestId ?? await beforeText('keke', trimmed, requestId)
    if (!routeId) return
    const placeholderId = `a-${requestId}`
    setMsgs(current => [...current,{id:`u-${requestId}`,role:'user',text:trimmed},{id:placeholderId,role:'ai',text:''}])
    setInput('')
    setTyping(true)
    setError(null)
    const controller = new AbortController()
    streamRef.current.set(requestId,controller)
    setActiveRequests([...streamRef.current.keys()])
    const shownCandidates = [...displayedCandidateRefs.current]
    try {
      // Re-read the authoritative version at admission, including a just-routed
      // shopping goal from another live response.
      const displayedPlan = displayedPlanRef.current
      const snapshot = await readSnapshot(getGuideSession(sessionId, false))
      if (controller.signal.aborted) return
      const turn = await sendTurnStream(sessionId,trimmed,snapshot.task_id ?? null,snapshot.state_version,requestId,snapshot.session_version,viewContext,{
        signal:controller.signal,
        onProgress:event => updatePhase(requestId,String(event.payload?.phase ?? 'understanding')),
        onAnswerDelta:event => receiveDelta(placeholderId,event),
      }, displayedPlan, shownCandidates, routeId)
      if (controller.signal.aborted) return
      const latest = await readSnapshot(getGuideSession(sessionId, false))
      if (!controller.signal.aborted) {
        const accepted = mergeTerminalTurn(turn, latest, placeholderId)
        const freshQuestion = turn.active_question?.question_id === turn.assistant_message_id && !!turn.active_question
        const eligible = turn.runtime_status === 'completed' && turn.answer_kind !== 'general_explanation' &&
          (freshQuestion || !!turn.product_cards?.length || !!turn.product_evidence?.length || !!turn.confirmation_result ||
           turn.no_matches === true || (turn.plan_effect === 'replace' && !!turn.plan))
        if (accepted && eligible) queueIntroduction({source_kind: 'turn', source_id: requestId}, latest, actionEpoch)
      }
      if (turn.confirmation_result) onCartRefresh()
    } catch (error) {
      if (!controller.signal.aborted) setError(error instanceof Error ? error.message : '发送失败')
      if (!controller.signal.aborted && error instanceof ApiError && error.code === 'DISPLAYED_PLAN_STALE') {
        const latest = await readSnapshot(getGuideSession(sessionId, false))
        if (!controller.signal.aborted) {
          applyAuthoritativeSnapshot(latest)
          setOpenSheet('plan')
        }
      }
      const capturedRefs = new Set(shownCandidates)
      displayedCandidateRefs.current = displayedCandidateRefs.current.filter(ref => !capturedRefs.has(ref))
      setMsgs(current => current.filter(message => message.id !== placeholderId || message.text).map(message => ({...message, productCards:message.productCards?.filter(card => !capturedRefs.has(card.ref))})))
    } finally {
      finishTransport(requestId)
    }
  }, [sessionId, confirming, restoring, viewContext, applyAuthoritativeSnapshot, mergeTerminalTurn, receiveDelta, updatePhase, finishTransport, onCartRefresh, readSnapshot, beforeText, onInteraction, queueIntroduction])

  const resumedHandoff = useRef<string | null>(null)
  useEffect(() => {
    if (!handoff) { resumedHandoff.current = null; return }
    if (restoring || !sessionId || resumedHandoff.current === handoff.routing_request_id) return
    resumedHandoff.current = handoff.routing_request_id
    void send(handoff.original_message, handoff.routing_request_id).finally(onHandoffDone)
  }, [handoff, restoring, sessionId, send, onHandoffDone])

  async function handleQuestionAnswer(question: GuideQuestion, optionIds: string[], quantities: Record<string, number>) {
    if (!sessionId || questionBusy) return
    const actionEpoch = onInteraction()
    const requestId = newRequestId()
    setQuestionBusy(true)
    setError(null)
    try {
      const snapshot = await readSnapshot(answerGuideQuestion(sessionId, question, optionIds, quantities, requestId))
      if (applyAuthoritativeSnapshot(snapshot)) queueIntroduction({source_kind: 'question_answer', source_id: requestId}, snapshot, actionEpoch)
    } catch (error) {
      if (error instanceof ApiError && ['QUESTION_STALE', 'QUESTION_SUPPLY_CHANGED', 'STALE_STATE'].includes(error.code)) {
        applyAuthoritativeSnapshot(await readSnapshot(getGuideSession(sessionId, false)))
      }
      throw error
    } finally {
      setQuestionBusy(false)
    }
  }

  async function handleHistoryList() {
    if (!sessionId || restoring || typing || confirming) return
    setError(null)
    try { setHistorySources((await getHistoricalSources(sessionId)).sources) }
    catch (error) { setError(error instanceof Error ? error.message : '历史来源读取失败') }
  }

  async function handleHistoryDismiss() {
    if (!sessionId || !taskId || typing || confirming) return
    try { applyAuthoritativeSnapshot(await readSnapshot(dismissHistoryReminder(sessionId,taskId,'decline'))) }
    catch (error) { setError(error instanceof Error ? error.message : '提醒更新失败') }
  }

  async function handleHistorySelect(sourceId: string) {
    setHistorySources(null)
    setHistoryReminder(null)
    await send(`重新采购历史方案 ${sourceId}，请按当前条件和有效偏好重新准备清单。`)
  }

  async function handleAbandonTask() {
    if (!sessionId || !taskId) return
    try {
      const snapshot = await readSnapshot(getGuideSession(sessionId, false))
      const next = await abandonGuideTask(sessionId,{task_id:snapshot.task_id ?? null,state_version:snapshot.state_version,session_version:snapshot.session_version})
      applyAuthoritativeSnapshot(next)
      setMsgs(current => [...current,{id:newRequestId(),role:'ai',text:next.message ?? '已放弃当前购买任务。'}])
    } catch (error) { setError(error instanceof Error ? error.message : '任务更新失败') }
  }

  async function handleStop() {
    if (!sessionId || !activeRequests[0]) return
    try { await stopGuideTurn(sessionId,activeRequests[0]) }
    catch (error) { setError(error instanceof Error ? error.message : '停止失败') }
  }

  async function handleConfirm() {
    if (!plan || !taskId || confirming || typing || !canConfirm) return
    const actionEpoch = onInteraction()
    const confirmationKey = newRequestId()
    setConfirming(true)
    setError(null)
    try {
      const result = await confirmPlan(
        taskId,
        plan.plan_id,
        plan.plan_version,
        stateVersion,
        sessionVersion,
        confirmableItems(plan.items),
        confirmationKey,
      )
      showPurchaseReceipt(result)
      setStateVersion(result.state_version)
      setSessionVersion(result.session_version)
      if (sessionId) {
        const snapshot = await readSnapshot(getGuideSession(sessionId, false))
        if (applyAuthoritativeSnapshot(snapshot)) queueIntroduction({source_kind: 'purchase_confirmation', source_id: confirmationKey}, snapshot, actionEpoch)
      }
      setOpenSheet(null)
      onCartRefresh()
    } catch (e) {
      if (e instanceof ApiError && e.code === 'STALE_STATE' && sessionId) {
        try {
          const session = await readSnapshot(getGuideSession(sessionId, false))
          applyAuthoritativeSnapshot(session)
          onCartRefresh()
          setError('清单或供给已变化，请修改清单后重新核对确认')
        } catch {
          setError(e instanceof Error ? e.message : '确认失败')
        }
      } else {
        setError(e instanceof Error ? e.message : '确认失败')
      }
    } finally {
      setConfirming(false)
    }
  }

  async function handleAddPlanItem(skuId: string) {
    if (!plan || !taskId || !sessionId || confirming || typing || !canConfirm) return
    const item = plan.items.find(row => row.sku_id === skuId)
    if (!item || item.selected === false || remainingQuantity(item) <= 0) return
    const actionEpoch = onInteraction()
    const confirmationKey = newRequestId()
    setConfirming(true)
    setError(null)
    try {
      const result = await addPlanItem(taskId, skuId, plan, stateVersion, sessionVersion, remainingQuantity(item), confirmationKey)
      showPurchaseReceipt(result)
      const snapshot = await readSnapshot(getGuideSession(sessionId, false))
      if (applyAuthoritativeSnapshot(snapshot)) queueIntroduction({source_kind: 'purchase_confirmation', source_id: confirmationKey}, snapshot, actionEpoch)
      onCartRefresh()
    } catch (error) {
      setError(error instanceof Error ? error.message : '逐行加购失败')
    } finally { setConfirming(false) }
  }

  async function handleChooseAlternative(gapId: string, alternativeIndex: number) {
    if (!plan || !taskId || confirming || typing) return
    setConfirming(true)
    setError(null)
    try {
      const {state_version, session_version, ...nextPlan} = await chooseSupplyAlternative(taskId, plan, stateVersion, sessionVersion, gapId, alternativeIndex)
      applyAuthoritativeSnapshot({...acceptedSnapshotRef.current!, session_id:sessionId!, task_id:taskId, state_version, session_version, product_cards:[], plan:nextPlan, available_actions:['send_message','modify',...(nextPlan.can_confirm ? ['confirm'] : [])]})
    } catch (error) { setError(error instanceof Error ? error.message : '替代规格选择失败') }
    finally { setConfirming(false) }
  }

  async function handleChoosePartial() {
    if (!plan || !taskId || confirming || typing) return
    setConfirming(true)
    setError(null)
    try {
      const {state_version, session_version, ...nextPlan} = await choosePartialSupply(taskId, plan, stateVersion, sessionVersion)
      applyAuthoritativeSnapshot({...acceptedSnapshotRef.current!, session_id:sessionId!, task_id:taskId, state_version, session_version, product_cards:[], plan:nextPlan, available_actions:['send_message','modify',...(nextPlan.can_confirm ? ['confirm'] : [])]})
    } catch (error) { setError(error instanceof Error ? error.message : '部分采购选择失败') }
    finally { setConfirming(false) }
  }

  async function handleChangeDish(changes: {people?: number; selections?: Record<string,string>; group_id?: string; remove_group?: boolean}) {
    if (!plan || !taskId || confirming || typing) return
    setConfirming(true)
    setError(null)
    try {
      const {state_version, session_version, ...nextPlan} = await reviseDishPlan(taskId, plan, stateVersion, sessionVersion, changes)
      applyAuthoritativeSnapshot({...acceptedSnapshotRef.current!, session_id:sessionId!, task_id:taskId, state_version, session_version, product_cards:[], plan:nextPlan, available_actions:['send_message','modify',...(nextPlan.can_confirm ? ['confirm'] : [])]})
    } catch (error) {
      setError(error instanceof Error ? error.message : '菜谱修改失败')
    } finally { setConfirming(false) }
  }

  async function handleAcceptQuote() {
    if (!plan?.budget_quote || !taskId || confirming || typing) return
    setConfirming(true)
    setError(null)
    try {
      const {state_version, session_version, ...nextPlan} = await acceptPlanQuote(taskId, plan, stateVersion, sessionVersion)
      applyAuthoritativeSnapshot({...acceptedSnapshotRef.current!, session_id:sessionId!, task_id:taskId, state_version, session_version, product_cards:[], plan:nextPlan, available_actions:['send_message','modify',...(nextPlan.can_confirm ? ['confirm'] : [])]})
    } catch (error) { setError(error instanceof Error ? error.message : '预算更新失败') }
    finally { setConfirming(false) }
  }

  async function handleRevisePlanItem(skuId: string, quantity?: number) {
    if (!plan || !taskId || confirming || typing) return
    setConfirming(true)
    setError(null)
    try {
      const revision = await revisePlan(
        taskId,
        plan,
        stateVersion,
        sessionVersion,
        plan.items.map(item => ({
          sku_id: item.sku_id,
          quantity: item.sku_id === skuId && quantity !== undefined ? quantity : item.quantity,
          selected: item.sku_id === skuId && quantity === undefined ? item.selected === false : item.selected !== false,
        })),
      )
      const { state_version, session_version, ...revisedPlan } = revision
      applyAuthoritativeSnapshot({...acceptedSnapshotRef.current!, session_id:sessionId!, task_id:taskId, state_version, session_version, product_cards:[], plan:revisedPlan, available_actions:['send_message','modify',...(revision.can_confirm ? ['confirm'] : [])]})
    } catch (e) {
      setError(e instanceof Error ? e.message : '清单修改失败')
    } finally {
      setConfirming(false)
    }
  }

  const hasPlan = !!plan
  const cartCount = cartItemCount(cart)
  const planItemCount = hasPlan ? plan.items.length : 0

  const introductionBanner = (
    <>
      {introductionStatus === 'running' && (
        <p role="status" aria-label="结果介绍进度" className="border-b border-black/[0.05] px-6 py-2 text-xs text-black/50">
          正在补充介绍，已有结果可以继续操作。{' '}
          <button type="button" aria-label="停止结果介绍" onClick={stopIntroduction}>停止介绍</button>
        </p>
      )}
      {introductionStatus && ['failed', 'deadline'].includes(introductionStatus) && (
        <p role="status" className="border-b border-black/[0.05] px-6 py-2 text-xs text-black/50">介绍未完成，已有结果仍保留。</p>
      )}
      {introductionStatus === 'stopped' && (
        <p role="status" className="border-b border-black/[0.05] px-6 py-2 text-xs text-black/50">介绍已停止，已有结果仍保留。</p>
      )}
    </>
  )

  const kekePlusActions: ComposerPlusAction[] = [
    {
      label: '历史方案',
      onClick: handleHistoryList,
      disabled: restoring || typing || confirming,
    },
    ...(activeRequests.length > 0
      ? [{ label: '停止处理', onClick: handleStop, ariaLabel: '停止本次处理' }]
      : []),
    {
      label: '放弃购买任务',
      onClick: handleAbandonTask,
      disabled: !taskId,
      ariaLabel: '放弃购买任务',
    },
  ]

  return (
    <RoleChatFrame
      activeRole="keke"
      agentAvatar={<KekeAvatar size={40} animated />}
      agentName="可可"
      statusLine={
        progressText ? (
          <div data-guide-action-line className="h-4 overflow-hidden" aria-live="polite">
            <p key={progressText} className="guide-action-roll">{progressText}</p>
          </div>
        ) : undefined
      }
      navigation={navigation}
      threadBanner={introductionBanner}
      bottomRef={bottomRef}
      toolRow={
        <ChatGuideCapsules
          openSheet={openSheet}
          onToggle={sheet => setOpenSheet(prev => (prev === sheet ? null : sheet))}
          planCount={planItemCount}
          cartCount={cartCount}
          navigation={navigation}
        />
      }
      composerPlusActions={kekePlusActions}
      sheetSlot={
        openSheet && !checkoutPhase ? (
          <ChatFloatingSheet onClose={() => setOpenSheet(null)}>
            {openSheet === 'activity' && <ActivitySheetContent />}
            {openSheet === 'plan' && (
              hasPlan
                ? (
                  <PlanSheetContent
                    plan={plan}
                    onChangeDish={handleChangeDish}
                    onChoosePartial={handleChoosePartial}
                    onChooseAlternative={handleChooseAlternative}
                    onToggleItem={skuId => handleRevisePlanItem(skuId)}
                    onChangeQuantity={handleRevisePlanItem}
                    onAcceptQuote={handleAcceptQuote}
                    onAddItem={handleAddPlanItem}
                    confirming={confirming}
                    canConfirm={canConfirm}
                    typing={typing}
                    onConfirm={handleConfirm}
                  />
                )
                : <PlanEmptySheetContent />
            )}
            {openSheet === 'cart' && (
              cart && cart.items.length > 0
                ? (
                  <CartSheetContent
                    cart={cart}
                    busy={cartBusy}
                    error={cartError}
                    onCheckout={() => {
                      setOpenSheet(null)
                      setCheckoutPhase('checkout')
                    }}
                    onUpdateQty={async (skuId, qty) => {
                      setCartBusy(true)
                      setCartError(null)
                      try {
                        const next = await patchCartItem(skuId, qty, cart.version)
                        onCartChange(next)
                      } catch (e) {
                        if (e instanceof ApiError && e.code === 'STALE_STATE') {
                          const fresh = await getCart()
                          onCartChange(fresh)
                          setCartError('购物车已更新，请重试')
                        } else {
                          setCartError(e instanceof Error ? e.message : '更新失败')
                        }
                      } finally {
                        setCartBusy(false)
                      }
                    }}
                  />
                )
                : <CartEmptySheetContent />
            )}
          </ChatFloatingSheet>
        ) : null
      }
      composer={{
        value: input,
        onChange: setInput,
        onSend: () => void send(input),
        placeholder: '问问可可吧…',
        disabled: restoring,
        sendDisabled: !input.trim() || !sessionId || confirming || restoring,
      }}
      overlay={
        checkoutPhase === 'checkout' ? (
          <SimulatedCheckout
            onCartChange={onCartChange}
            onClose={() => setCheckoutPhase(null)}
            onViewOrders={() => {
              setCheckoutPhase(null)
              onViewOrders()
            }}
          />
        ) : undefined
      }
    >
      {historyReminder && (
        <div className="rounded-2xl bg-amber-50 p-3 text-[12px]" aria-label="历史采购提醒">
          <p>{historyReminder.message}</p>
          <div className="mt-2 flex gap-3">
            <button disabled={typing || confirming} onClick={() => void handleHistorySelect(historyReminder.source_task_id)}>按当前条件重新准备</button>
            <button disabled={typing || confirming} onClick={handleHistoryDismiss}>不再提醒</button>
          </div>
        </div>
      )}
      {historySources && (
        <div className="rounded-2xl bg-black/[0.03] p-3 text-[12px]" aria-label="历史方案来源">
          <p>{historySources.length ? '请选择历史来源，选择后仍需核对新清单并单独确认加购。' : '目前没有历史方案。'}</p>
          {historySources.map(source => (
            <button
              key={source.task_id}
              disabled={typing || confirming}
              aria-label={`重新采购 ${source.task_id}`}
              onClick={() => void handleHistorySelect(source.task_id)}
              className="mt-2 block rounded-xl bg-white px-3 py-2 text-left"
            >
              {source.goal || '历史采购'} · {source.task_id.slice(-8)}
            </button>
          ))}
        </div>
      )}
      {restoring && <p className="text-center text-sm text-black/40">正在连接可可…</p>}
      {error && <p className="text-center text-xs text-red-600">{error}</p>}
      {msgs.map(msg => (
        <div key={msg.id} className={`flex items-end gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
          {msg.role === 'ai' && <KekeAvatar size={26} />}
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
                {msg.generalExplanation && (
                  <p className="mb-1 text-[10px] font-normal text-black/45" title="通用知识解释，不是门店事实或商业操作回执">通用解释</p>
                )}
                {formatText(stripDuplicateClarificationOptions(msg.text, msg.suggestions))}
              </div>
            ) : msg.role === 'ai' && typing && !progressText ? (
              <div
                className="ai-loading-bubble px-4 py-3 text-[13px] font-medium leading-[1.7] tracking-[-0.015em]"
                style={{
                  borderRadius: '24px 24px 24px 8px',
                  background: '#f2f1ed',
                  color: '#292825',
                }}
              >
                <span className="ai-loading-ellipsis" aria-label="可可正在输入">
                  <span className="ai-loading-ellipsis__dot" aria-hidden="true">.</span>
                  <span className="ai-loading-ellipsis__dot" aria-hidden="true">.</span>
                  <span className="ai-loading-ellipsis__dot" aria-hidden="true">.</span>
                </span>
              </div>
            ) : null}
            {msg.question && (
              <QuestionChoices
                question={msg.question}
                disabled={typing || confirming || restoring || questionBusy}
                onAnswer={(optionIds, quantities) => handleQuestionAnswer(msg.question!, optionIds, quantities)}
              />
            )}
            <ComparisonCards cards={msg.productCards ?? []} disabled={typing || confirming || restoring} onSelect={text => { void send(text) }} />
            {msg.suggestions && !msg.question && msg.role === 'ai' && !typing && !confirming && (
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

// ── Profile Screen ────────────────────────────────────────────
function ProfileScreen() {
  const menuItems = [
    { label: '收货地址', icon: '📍' }, { label: '优惠券', icon: '🎟️' },
    { label: '会员中心', icon: '⭐' }, { label: '消息通知', icon: '🔔' },
    { label: '帮助与反馈', icon: '💬' }, { label: '关于 Ceres', icon: '🌿' },
  ]
  return (
    <div className="flex h-full flex-col bg-[#fcfbf8]">
      <div className="flex-shrink-0 px-6 pt-10 pb-5">
        <h2 className="flex items-center gap-2 text-[26px] font-semibold tracking-[-0.07em] text-[#191817]">个人中心 <DemoBadge /></h2>
      </div>
      <div className="mx-5 flex flex-shrink-0 items-center gap-4 rounded-[30px] bg-[#f2f1ed] p-4">
        <div className="grid h-14 w-14 place-items-center rounded-[20px] bg-[#f6df91] text-[22px]">C</div>
        <div className="min-w-0 flex-1"><p className="text-[16px] font-semibold tracking-[-0.04em] text-[#1d1c1a]">Ceres 会员</p><p className="mt-1 text-[11px] font-medium text-black/38">138 **** 8888</p></div>
        <span className="rounded-full bg-white/75 px-2.5 py-1 text-[10px] font-medium text-[#6e581a]">绿金会员</span>
      </div>
      <div className="mx-5 mt-3 flex flex-shrink-0 rounded-[25px] bg-[#f7f6f2] px-2 py-3">
        {[['12', '订单数'], ['3', '优惠券'], ['286', '积分']].map(([val, label]) => (
          <button key={label} className="flex-1 border-r border-black/[.06] last:border-0">
            <p className="text-[18px] font-semibold tracking-[-0.04em] text-[#1d1c1a]">{val}</p>
            <p className="mt-0.5 text-[10px] font-medium text-black/35">{label}</p>
          </button>
        ))}
      </div>
      <div className="scrollbar-hide mx-5 mt-5 flex-1 space-y-1.5 overflow-y-auto pb-5">
        <p className="px-2 pb-1 text-[10px] font-medium tracking-[0.12em] text-black/30">ACCOUNT</p>
        {menuItems.map(item => (
          <button key={item.label}
            className="flex w-full items-center gap-3 rounded-[20px] bg-[#f7f6f2] px-4 py-3.5 text-left transition hover:bg-[#f2f1ed] active:scale-[.985]">
            <span className="grid h-8 w-8 place-items-center rounded-xl bg-white/75 text-[15px]">{item.icon}</span>
            <span className="flex-1 text-[13px] font-medium text-[#302f2b]">{item.label}</span>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="rgba(0,0,0,.25)" strokeWidth="2" strokeLinecap="round"><polyline points="9 18 15 12 9 6" /></svg>
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Bottom Nav ────────────────────────────────────────────────
type ViewState = 'home' | 'shelf' | 'keke' | 'orders' | 'momo' | 'profile'

interface NavItem {
  id: string
  label: string
  icon: (active: boolean) => React.ReactNode
  isKeke?: boolean
  isMomo?: boolean
}

function BottomNav({ view, onTap }: { view: ViewState; onTap: (id: string) => void }) {
  const onShelfCtx = view === 'shelf' || view === 'keke'
  const onOrdersCtx = view === 'orders' || view === 'momo'

  const tab2: NavItem = onShelfCtx
    ? { id: 'keke',  label: view === 'keke' ? '自己逛逛' : '问问可可', isKeke: true,  icon: () => <KekeAvatar size={20} /> }
    : { id: 'shelf', label: '商品',     isKeke: false, icon: (a) => <IconGrid filled={a} /> }

  const tab3: NavItem = onOrdersCtx
    ? { id: 'momo',  label: view === 'momo' ? '我再逛逛' : '问问墨墨', isMomo: true,  icon: () => <MomoAvatar size={20} /> }
    : { id: 'orders', label: '订单', icon: (a) => <IconOrders filled={a} /> }

  const tabs: NavItem[] = [
    { id: 'home',    label: '主页',   icon: (a) => <IconHome filled={a} /> },
    tab2,
    tab3,
    { id: 'profile', label: '个人中心', icon: (a) => <IconUser filled={a} /> },
  ]

  function isActive(id: string) {
    if (id === 'home')    return view === 'home'
    if (id === 'shelf')   return view === 'shelf'
    if (id === 'keke')    return view === 'keke'
    if (id === 'momo')    return view === 'momo'
    if (id === 'orders')  return view === 'orders'
    if (id === 'profile') return view === 'profile'
    return false
  }

  return (
    <div className="relative z-20 flex-shrink-0 px-5 pb-5 pt-3">
      <div className="flex items-center justify-between gap-1.5 rounded-full border border-white/90 bg-white/90 px-2 py-2 backdrop-blur-xl"
        style={{ boxShadow: '0 10px 26px rgba(56,72,54,0.16), 0 2px 0 rgba(190,185,170,0.18)' }}>
        {tabs.map(tab => {
          const active = isActive(tab.id)
          const isKeke = !!tab.isKeke
          const isMomo = !!tab.isMomo
          const expanded = active || isKeke || isMomo
          return (
            <button key={tab.id} onClick={() => onTap(tab.id)}
              className="flex h-10 items-center justify-center transition-all duration-300 ease-out active:scale-90"
              style={{
                borderRadius: 999,
                gap: expanded ? 6 : 0,
                padding: expanded ? (isKeke || isMomo ? '7px 14px 7px 9px' : '7px 14px') : '9px',
                background: isMomo
                  ? (active ? '#E9C96F' : '#FFF3C9')
                  : isKeke
                  ? (active ? '#E9C96F' : '#FFF3C9')
                  : (active ? '#39714B' : 'transparent'),
                color: active
                  ? (isMomo || isKeke ? '#4E3D12' : 'white')
                  : (isMomo || isKeke ? '#9D7B22' : '#91A097'),
                boxShadow: isMomo || isKeke
                  ? (active ? '0 4px 10px rgba(191,151,52,0.24)' : 'inset 0 0 0 1px rgba(220,185,75,0.22)')
                  : 'none',
              }}>
              {tab.icon(active && !isKeke && !isMomo)}
              <span className="text-xs font-extrabold whitespace-nowrap overflow-hidden transition-all duration-300"
                style={{ maxWidth: expanded ? 84 : 0, opacity: expanded ? 1 : 0 }}>
                {tab.label}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────
export default function App() {
  if (window.location.pathname === '/operator/human-cases') return <HumanOperatorPage />
  return <ShoppingApp />
}

function ShoppingApp() {
  const [view, setView] = useState<ViewState>(() => sessionStorage.getItem('ceres-chat-visible') === 'momo' ? 'momo' : sessionStorage.getItem('ceres-chat-visible') === 'keke' ? 'keke' : 'home')
  const [cart, setCart] = useState<Cart | null>(null)
  const [activeCategoryId, setActiveCategoryId] = useState<string | null>(null)
  const [shelfSearch, setShelfSearch] = useState('')
  const [guideFromHome, setGuideFromHome] = useState(false)
  const [activityBusy, setActivityBusy] = useState(false)
  const [activityError, setActivityError] = useState<string | null>(null)
  const interactionEpoch = useRef(0)
  const [interactionVersion, setInteractionVersion] = useState(0)
  const trackInteraction = useCallback(() => {
    const epoch = ++interactionEpoch.current
    // Invalidate stale introductions immediately, but let native control
    // change handlers finish before a capture-phase parent render.
    setTimeout(() => setInteractionVersion(epoch), 0)
    return epoch
  }, [])
  const activityNavigationEpoch = useRef(0)
  useEffect(() => () => { activityNavigationEpoch.current += 1 }, [])
  const [mercuryEntry, setMercuryEntry] = useState<{orderId:string|undefined; sequence:number}>({orderId:undefined,sequence:0})
  const consumeMercuryEntry = useCallback((sequence:number) => setMercuryEntry(current => current.sequence === sequence ? {...current,orderId:undefined} : current),[])
  const [navigation, setNavigation] = useState<{sessionId: string; opening: Opening} | null>(null)
  const [navigationError, setNavigationError] = useState<string | null>(null)
  const [routePrompt, setRoutePrompt] = useState<RouteDecision | null>(null)
  const [navigationBusy, setNavigationBusy] = useState(false)
  const [handoff, setHandoff] = useState<(Handoff & {role: ChatRole}) | null>(null)
  const clearHandoff = useCallback(() => setHandoff(null), [])
  const chatOpen = view === 'keke' || view === 'momo'
  const navigationRef = useRef(navigation)
  navigationRef.current = navigation
  useEffect(() => {
    if (!chatOpen) return
    sessionStorage.setItem('ceres-chat-visible', view)
    if (navigation) return
    let active = true
    setNavigationBusy(true)
    void openNavigation(view === 'momo' ? 'momo' : 'keke').then(next => {
      if (!active) return
      setNavigation(next)
      setView(next.opening.role)
      if (next.opening.handoff) setHandoff({...next.opening.handoff,role:next.opening.role})
      setNavigationError(null)
    }).catch(error => { if (active) setNavigationError(error.message) })
      .finally(() => { if (active) setNavigationBusy(false) })
    return () => { active = false }
  }, [chatOpen, navigation, view])

  const beforeText = useCallback<BeforeText>(async (role, message, requestId, selectedOrder, roleSessionId) => {
    const nav = navigationRef.current
    if (!nav) { setNavigationError('正在恢复聊天，请稍后再试'); return null }
    setNavigationBusy(true)
    setNavigationError(null)
    setRoutePrompt(null)
    try {
      const result = await routeText(nav.sessionId, nav.opening.opening_id, role, message, requestId, selectedOrder, roleSessionId)
      if (result.status === 'ready') return result.routing_request_id
      if (result.status === 'navigation') {
        setView(result.target_role)
        setNavigation({...nav, opening:{...nav.opening, role:result.target_role}})
        if (result.continue_original) setHandoff({...result, role:result.target_role})
      } else if (result.status === 'switch') {
        if (result.show_prompt) setRoutePrompt(result)
        else setNavigationError('这次请求属于另一角色，可使用上方角色按钮继续。')
      } else setNavigationError(result.message ?? '请重新说明需求')
      return null
    } catch (error) {
      setNavigationError(error instanceof Error ? error.message : '职责判断暂时不可用，请使用角色按钮')
      return null
    } finally { setNavigationBusy(false) }
  }, [])

  useEffect(() => {
    if (!routePrompt || !navigation) return
    // This effect runs after the prompt was committed to the visible DOM.
    void ackPrompt(navigation.sessionId, navigation.opening.opening_id, routePrompt.routing_request_id)
      .then(opening => setNavigation(current => current ? {...current, opening} : current))
      .catch(error => setNavigationError(`提示确认失败：${error.message}，可重试确认。`))
  }, [routePrompt?.routing_request_id])

  async function switchChatRole(role: ChatRole, accept = true, requestId?: string) {
    if (!navigation || navigationBusy) return
    setNavigationBusy(true)
    try {
      const result = await chooseRole(navigation.sessionId, navigation.opening.opening_id, role, accept, requestId)
      setNavigation({...navigation, opening:result})
      setRoutePrompt(null)
      setNavigationError(null)
      if (accept) {
        setView(role)
        if (result.handoff) {
          if (result.handoff.selected_object?.kind === 'order' && role === 'momo') setMercuryEntry(current => ({orderId:result.handoff!.selected_object!.id,sequence:current.sequence + 1}))
          setHandoff({...result.handoff,role})
        }
      }
    } catch (error) { setNavigationError(error instanceof Error ? error.message : '角色切换失败') }
    finally { setNavigationBusy(false) }
  }

  async function leaveChat(target: ViewState) {
    if (navigationBusy) return
    try {
      if (navigation) await closeOpening(navigation.sessionId, navigation.opening.opening_id)
      setNavigation(null)
      setRoutePrompt(null)
      setHandoff(null)
      sessionStorage.removeItem('ceres-chat-visible')
      setView(target)
    } catch (error) { setNavigationError(error instanceof Error ? error.message : '关闭失败，请重试') }
  }
  const cartCount = cartItemCount(cart)

  const refreshCart = useCallback(async () => {
    try {
      await ensureIdentity()
      const data = await getCart()
      setCart(data)
    } catch {
      /* cart may be unavailable before bootstrap */
    }
  }, [])

  useEffect(() => { refreshCart() }, [refreshCart])

  const guideViewContext = guideFromHome
    ? { page: 'home', category_id: null }
    : shelfSearch.trim()
      ? { page: 'search', category_id: null }
      : view === 'shelf' || view === 'keke'
        ? { page: 'category', category_id: activeCategoryId }
        : { page: 'home', category_id: null }

  function handleNavTap(id: string) {
    activityNavigationEpoch.current += 1
    if (chatOpen) {
      const target = id === 'keke' ? 'shelf' : id === 'momo' ? 'orders' : id as ViewState
      void leaveChat(target)
      return
    }
    if (id === 'home')    { setView('home'); return }
    if (id === 'orders')  { setView('orders'); return }
    if (id === 'profile') { setView('profile'); return }
    if (id === 'shelf') setView('shelf')
    if (id === 'keke')  { setView(v => v === 'keke' ? 'shelf' : 'keke') }
    if (id === 'momo')  { setView(v => v === 'momo' ? 'orders' : 'momo') }
  }

  async function handleDietPlan() {
    if (activityBusy) return
    const requestedNavigation = ++activityNavigationEpoch.current
    setActivityBusy(true)
    setActivityError(null)
    try {
      const snapshot = await createGuideSession({page: 'home'})
      if (requestedNavigation !== activityNavigationEpoch.current) return
      await enterLightMealActivity(snapshot, newRequestId())
      // The result stays in the canonical session if the user has moved on.
      // Only the still-current navigation intent may open the chat overlay.
      if (requestedNavigation !== activityNavigationEpoch.current) return
      // Opening ChatScreen re-reads the canonical snapshot through its normal
      // ordered restoration path; the activity result is never sent as text.
      setGuideFromHome(true)
      setView('keke')
    } catch (error) {
      if (requestedNavigation === activityNavigationEpoch.current) setActivityError(error instanceof Error ? error.message : '活动商品暂时无法读取，请重试')
    } finally {
      setActivityBusy(false)
    }
  }

  const chatNavigation: RoleChatNavigationProps | undefined = chatOpen && navigation
    ? {
        view: view === 'momo' ? 'momo' : 'keke',
        navigationBusy,
        navigationReady: true,
        navigationError,
        routePrompt,
        onSwitchRole: role => void switchChatRole(role),
        onClose: () => void leaveChat(view === 'momo' ? 'orders' : 'shelf'),
        onRouteAccept: () => {
          if (routePrompt) void switchChatRole(routePrompt.target_role, true, routePrompt.routing_request_id)
        },
        onRouteDecline: () => {
          if (routePrompt) void switchChatRole(routePrompt.target_role, false, routePrompt.routing_request_id)
        },
        onRetryAck: () => {
          if (!navigation || !routePrompt) return
          void ackPrompt(navigation.sessionId, navigation.opening.opening_id, routePrompt.routing_request_id)
            .then(opening => {
              setNavigation({ ...navigation, opening })
              setNavigationError(null)
            })
            .catch(error => setNavigationError(`提示确认失败：${error.message}`))
        },
      }
    : undefined

  return (
    <main onClickCapture={trackInteraction} onKeyDownCapture={trackInteraction} onChangeCapture={trackInteraction} className="box-border min-h-dvh bg-[#eaf1ed] p-0 sm:p-8" style={{ fontFamily: "'Noto Sans SC', 'Manrope', system-ui, sans-serif" }}>
      <div className="relative mx-auto flex h-dvh w-full max-w-[430px] flex-col overflow-hidden bg-[#F5F5F7] sm:h-[min(860px,calc(100dvh-4rem))] sm:rounded-[32px] sm:shadow-[0_24px_70px_rgba(38,64,51,0.16)]">
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          {view === 'home' && (
            <LandingScreen
              onGoShelf={() => { activityNavigationEpoch.current += 1; setGuideFromHome(false); setView('shelf') }}
              onDietPlan={() => void handleDietPlan()}
              activityBusy={activityBusy} activityError={activityError}
            />
          )}
          {(view === 'shelf' || view === 'keke') && (
            <ShelfScreen
              cart={cart}
              cartCount={cartCount}
              onCartChange={setCart}
              onViewOrders={() => setView('orders')}
              onCategoryChange={setActiveCategoryId}
              onSearchChange={setShelfSearch}
            />
          )}
          {(view === 'orders' || view === 'momo') && (
            <SimulatedOrdersScreen
              onContactOrder={orderId => {
                setMercuryEntry(current => ({ orderId, sequence: current.sequence + 1 }))
                setView('momo')
              }}
            />
          )}
          {view === 'profile' && <ProfileScreen />}
        </div>

        <BottomNav view={view} onTap={handleNavTap} />
        {chatOpen && navigation && (
          <div className="absolute inset-x-0 bottom-[82px] top-0 z-10 flex flex-col justify-end bg-[#18261b]/20 backdrop-blur-[1px]">
            <div className={view === 'keke' ? '' : 'hidden'}>
              <ChatScreen
                active={view === 'keke'}
                interactionEpoch={interactionEpoch}
                interactionVersion={interactionVersion}
                onInteraction={trackInteraction}
                viewContext={guideViewContext}
                onCartRefresh={refreshCart}
                cart={cart}
                onCartChange={setCart}
                onViewOrders={() => void leaveChat('orders')}
                beforeText={beforeText}
                handoff={handoff?.role === 'keke' ? handoff : null}
                onHandoffDone={clearHandoff}
                navigation={chatNavigation}
              />
            </div>
            <div className={view === 'momo' ? '' : 'hidden'}>
              <MercuryChat
                visible={view === 'momo'}
                initialOrderId={mercuryEntry.orderId}
                entrySequence={mercuryEntry.sequence}
                onOrderEntryConsumed={consumeMercuryEntry}
                beforeText={beforeText}
                handoff={handoff?.role === 'momo' ? handoff : null}
                onHandoffDone={clearHandoff}
                navigation={chatNavigation}
              />
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
