import { AlertCircle } from 'lucide-react'

export function ErrorState({ message = 'Não foi possível carregar estes dados.' }: { message?: string }) {
  return <div className="empty-state" role="alert"><AlertCircle size={24}/><h3>Erro ao carregar</h3><p>{message}</p></div>
}
