import { CircleCheck, CircleX, CircleHelp } from 'lucide-react'
import { normalizeText } from '../lib/format'

export type RegistrationState = 'active' | 'inactive' | 'unknown'

export function registrationState(status: string | null | undefined): RegistrationState {
  const normalized = normalizeText(status)
  if (normalized === 'ativo' || normalized.includes('registro ativo')) return 'active'
  if (normalized === 'inativo' || normalized.includes('registro inativo')) return 'inactive'
  return 'unknown'
}

export function RegistrationStatus({ status, compact = false }: { status: string | null | undefined; compact?: boolean }) {
  const state = registrationState(status)
  const label = status?.trim() || 'Não informado'
  const Icon = state === 'active' ? CircleCheck : state === 'inactive' ? CircleX : CircleHelp

  return <span className={`registration-status ${state} ${compact ? 'compact' : ''}`}>
    <Icon size={compact ? 14 : 18} aria-hidden="true"/>
    <span className="registration-status-copy">
      {!compact && <small>Situação do registro</small>}
      <strong>{label}</strong>
    </span>
  </span>
}
