export function Loading({ label = 'Carregando dados…' }: { label?: string }) {
  return <div className="loading"><span className="spinner" /> {label}</div>
}
