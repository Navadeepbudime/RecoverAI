import { api } from '../services/api'
import { useApi } from '../hooks/useApi'

export function AuditTrail() {
  const { data, loading, error } = useApi(api.audit, [])
  if (loading) return <div className="panel">Loading audit trail...</div>
  if (error) return <div className="panel text-coral">Could not load audit entries.</div>
  return (
    <div className="panel">
      <h3 className="mb-4 text-lg font-semibold">Audit Trail</h3>
      <div className="space-y-3">
        {(data || []).map((entry, index) => (
          <div key={`${entry.timestamp}-${index}`} className="rounded border border-slate-200 p-4">
            <div className="flex flex-wrap justify-between gap-2">
              <p className="font-semibold">{entry.event} · {entry.case_id}</p>
              <p className="text-xs text-slate-500">{new Date(entry.timestamp).toLocaleString()}</p>
            </div>
            <p className="mt-2 text-sm text-slate-600">{entry.reason}</p>
            <p className="mt-2 text-xs text-slate-500">Action: {entry.executed_action || 'None'} · Result: {entry.result || 'Recorded'}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
