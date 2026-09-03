import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { CaseTable } from './Dashboard'

export function RecoveryQueue({ onOpenCase }) {
  const { data, loading, error } = useApi(api.cases, [])
  if (loading) return <div className="panel">Loading queue...</div>
  if (error) return <div className="panel text-coral">Could not load recovery queue.</div>
  return (
    <div className="panel">
      <div className="mb-5">
        <h3 className="text-lg font-semibold">Recovery Queue</h3>
        <p className="text-sm text-slate-500">Cases are ranked by recent updates, with every automated decision auditable.</p>
      </div>
      <CaseTable cases={data || []} onOpenCase={onOpenCase} />
    </div>
  )
}
