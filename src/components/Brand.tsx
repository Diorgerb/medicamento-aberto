import type { CSSProperties } from 'react'

export function BrandMark({ size = 48, className = '' }: { size?: number; className?: string }) {
  const style: CSSProperties = { width: size, height: size }
  return <svg
    className={`brand-symbol ${className}`}
    style={style}
    viewBox="-7 -7 110 110"
    role="img"
    aria-label="Símbolo Medicamento Aberto"
  >
    <defs>
      <linearGradient id="ma-pill" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#0B3D4D"/>
        <stop offset=".5" stopColor="#007A8A"/>
        <stop offset=".5" stopColor="#2DBE6B"/>
        <stop offset="1" stopColor="#22A75A"/>
      </linearGradient>
    </defs>
    <path d="M31 18C31 8 39 4 48 4s17 4 17 14v20" fill="none" stroke="#0B3D4D" strokeWidth="8" strokeLinecap="round"/>
    <path d="M31 39v38c0 10 8 15 17 15s17-5 17-15V61" fill="none" stroke="#2DBE6B" strokeWidth="8" strokeLinecap="round"/>
    <path d="M31 44h34" stroke="#E6E8EB" strokeWidth="2" opacity=".9"/>
    <rect x="35" y="35" width="6" height="6" rx="1" fill="#007A8A"/>
    <rect x="44" y="35" width="6" height="6" rx="1" fill="#0B3D4D"/>
    <rect x="35" y="44" width="6" height="6" rx="1" fill="#2DBE6B"/>
    <rect x="44" y="44" width="6" height="6" rx="1" fill="#007A8A"/>
    <rect x="53" y="44" width="6" height="6" rx="1" fill="#5C7CFA"/>
    <rect x="35" y="53" width="6" height="6" rx="1" fill="#2DBE6B"/>
    <path d="M58 36h14" stroke="#007A8A" strokeWidth="3" strokeLinecap="round"/>
    <path d="M58 47h22" stroke="#0B3D4D" strokeWidth="3" strokeLinecap="round"/>
    <path d="M58 58h16" stroke="#2DBE6B" strokeWidth="3" strokeLinecap="round"/>
    <circle cx="78" cy="36" r="4" fill="#fff" stroke="#007A8A" strokeWidth="3"/>
    <circle cx="86" cy="47" r="4" fill="#fff" stroke="#0B3D4D" strokeWidth="3"/>
    <circle cx="80" cy="58" r="4" fill="#fff" stroke="#2DBE6B" strokeWidth="3"/>
  </svg>
}

export function BrandLogo({ compact = false, inverse = false, className = '' }: { compact?: boolean; inverse?: boolean; className?: string }) {
  return <span className={`brand-logo-lockup ${inverse ? 'inverse' : ''} ${className}`}>
    <BrandMark size={compact ? 38 : 50}/>
    <span className="brand-wordmark" aria-label="Medicamento Aberto">
      <strong>Medicamento</strong>
      <span>Aberto</span>
    </span>
  </span>
}
