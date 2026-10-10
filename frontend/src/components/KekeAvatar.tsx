export function KekeAvatar({ size = 28, animated = false }: { size?: number; animated?: boolean }) {
  return (
    <svg className={animated ? 'keke-breathe' : undefined} width={size} height={size} viewBox="0 0 40 40" fill="none" aria-label="可可，四叶草导购助手">
      <ellipse cx="24.5" cy="27.5" rx="13" ry="10.5" fill="#B9DF75" opacity="0.8" />
      <path d="M24 27.6C24.8 31.1 23.8 34.4 21.6 36.2" stroke="#3AA763" strokeWidth="4.2" strokeLinecap="round" />
      <circle cx="20" cy="10.3" r="9.4" fill="#42B46C" />
      <circle cx="10.8" cy="19.4" r="9.5" fill="#42B46C" />
      <circle cx="29.1" cy="19.4" r="9.5" fill="#42B46C" />
      <circle cx="20" cy="28.3" r="9.35" fill="#42B46C" />
      <ellipse cx="20" cy="12.4" rx="5" ry="2.5" fill="#75CB8B" opacity="0.72" />
      <ellipse cx="15.3" cy="23.6" rx="2.6" ry="1.55" fill="#8ED196" opacity="0.85" />
      <ellipse cx="25.8" cy="23.6" rx="2.65" ry="1.55" fill="#8ED196" opacity="0.85" />
      <path d="M15 19.4C16.8 17.7 19.1 17.7 20.7 19.4" stroke="#173A2A" strokeWidth="2" strokeLinecap="round" />
      <ellipse cx="25.7" cy="19.1" rx="2.05" ry="2.55" fill="#173A2A" />
      <circle cx="26.4" cy="18.25" r="0.7" fill="white" />
      <path d="M16.9 24.1C19.3 27.2 22.9 27.3 25.2 24.1" stroke="#173A2A" strokeWidth="2.05" strokeLinecap="round" />
    </svg>
  )
}
