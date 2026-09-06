import { DatabaseZap } from 'lucide-react'
export function EmptyState({ title = 'Nenhum dado encontrado', text }: { title?: string; text?: string }) {
  return (
    <div className="empty-state">
      <DatabaseZap size={34} />
      <h3>{title}</h3>
      {text && <p>{text}</p>}
    </div>
  )
}
