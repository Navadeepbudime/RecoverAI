import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { Bars, Donut } from '../charts/RecoveryCharts'

export function Analytics() {
  const { data, loading, error } = useApi(api.analytics, [])
  if (loading) return <div className="panel">Loading analytics...</div>
  if (error) return <div className="panel text-coral">Could not load analytics.</div>
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="panel">
        <h3 className="text-lg font-semibold">Recovery Actions</h3>
        <Donut data={data.actions} />
      </section>
      <section className="panel">
        <h3 className="text-lg font-semibold">Failure Reasons</h3>
        <Bars data={data.failures} />
      </section>
    </div>
  )
}
