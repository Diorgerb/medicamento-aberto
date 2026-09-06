import { createContext, useContext, useEffect, useMemo, useState } from 'react'

export type ViewMode = 'patient' | 'professional'

type ContextValue = {
  mode: ViewMode
  setMode: (mode: ViewMode) => void
}

const ViewModeContext = createContext<ContextValue | null>(null)
const STORAGE_KEY = 'medicamento-aberto:view-mode'

export function ViewModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ViewMode>('patient')

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved === 'patient' || saved === 'professional') setModeState(saved)
  }, [])

  const setMode = (next: ViewMode) => {
    setModeState(next)
    window.localStorage.setItem(STORAGE_KEY, next)
  }

  const value = useMemo(() => ({ mode, setMode }), [mode])
  return <ViewModeContext.Provider value={value}>{children}</ViewModeContext.Provider>
}

export function useViewMode() {
  const context = useContext(ViewModeContext)
  if (!context) throw new Error('useViewMode deve ser usado dentro de ViewModeProvider')
  return context
}
