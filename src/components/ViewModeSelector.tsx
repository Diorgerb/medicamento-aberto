import { HeartPulse, Stethoscope } from 'lucide-react'
import { useViewMode, type ViewMode } from './ViewModeContext'

export function ViewModeSelector({ compact = false }: { compact?: boolean }) {
  const { mode, setMode } = useViewMode()
  const options: { value: ViewMode; label: string; short: string; icon: React.ReactNode }[] = [
    { value: 'patient', label: 'Paciente / cidadão', short: 'Paciente', icon: <HeartPulse size={15}/> },
    { value: 'professional', label: 'Profissional', short: 'Profissional', icon: <Stethoscope size={15}/> },
  ]
  return <div className={`view-mode-selector ${compact ? 'compact' : ''}`} role="group" aria-label="Escolha como visualizar as informações">
    {options.map((option) => <button key={option.value} type="button" className={mode === option.value ? 'active' : ''} aria-pressed={mode === option.value} onClick={() => setMode(option.value)}>
      {option.icon}<span>{compact ? option.short : option.label}</span>
    </button>)}
  </div>
}
