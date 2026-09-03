const styles = {
  ACTIVE: 'bg-gold/20 text-amber-800',
  RECOVERED: 'bg-mint/15 text-emerald-800',
  STOPPED: 'bg-slate-200 text-slate-700',
  ESCALATED: 'bg-coral/15 text-red-800',
}

export function StatusBadge({ status }) {
  return <span className={`rounded px-2 py-1 text-xs font-semibold ${styles[status] || 'bg-slate-100 text-slate-700'}`}>{status}</span>
}
