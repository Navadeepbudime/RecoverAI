import { api, inr } from '../services/api'
import { useApi } from '../hooks/useApi'
import { Bars, ComparativeCategoryChart, Donut } from '../charts/RecoveryCharts'

export function Analytics() {
  const { data, loading, error } = useApi(api.analytics, [])

  if (loading) return <div className="panel">Loading analytics insights...</div>
  if (error) return <div className="panel text-coral">Could not load analytics. Please check backend.</div>

  const ev = data?.evaluation || {}

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight">Recovery Performance & ROI Analytics</h2>
        <p className="text-sm text-slate-500">
          Simulation-based benchmark comparing naive retries against RecoverAI multi-action orchestration.
        </p>
      </div>

      {/* Comparative Revenue by Category Chart */}
      <section className="panel space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2">
          <div>
            <h3 className="font-semibold text-slate-900">
              Recovered Revenue by Failure Type: Naive Retry vs. RecoverAI
            </h3>
            <p className="text-xs text-slate-500">
              Notice RecoverAI rescues revenue on Insufficient Funds & Expired Cards where naive retry yields ₹0.
            </p>
          </div>
          <div className="text-right text-xs">
            <span className="font-semibold text-emerald-700">
              Total Incremental Lift: +{inr(ev.incremental_revenue || 0)}
            </span>
          </div>
        </div>
        <ComparativeCategoryChart data={ev.categories || []} />
      </section>

      {/* Breakdown Grid */}
      <div className="grid gap-6 xl:grid-cols-2">
        <section className="panel space-y-2">
          <h3 className="text-base font-semibold text-slate-900">Recovery Action Distribution</h3>
          <p className="text-xs text-slate-500">Breakdown of next-best-actions orchestrated across incidents</p>
          <Donut data={data.actions} />
        </section>

        <section className="panel space-y-2">
          <h3 className="text-base font-semibold text-slate-900">Failure Reasons Frequency</h3>
          <p className="text-xs text-slate-500">Root causes detected at time of payment failure</p>
          <Bars data={data.failures} />
        </section>
      </div>
    </div>
  )
}
