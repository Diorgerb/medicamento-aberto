export function StatusBadge({ label, tone = 'neutral' }: { label: string; tone?: 'good' | 'warn' | 'danger' | 'info' | 'neutral' }) {
  return <span className={`badge ${tone}`}>{label}</span>
}
