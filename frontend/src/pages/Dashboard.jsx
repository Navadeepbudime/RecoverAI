import { RefreshCw } from 'lucide-react'
import { api, inr } from '../services/api'
import { useApi } from '../hooks/useApi'
import { MetricCard } from '../components/MetricCard'
import { StatusBadge } from '../components/StatusBadge'

export function Dashboard({ onOpenCase }) {
  const metrics = useApi(api.metrics, [])
  const cases = useApi(api.cases, [])

  if (metrics.loading || cases.loading) return <div className="panel">Loading RecoverAI workspace...</div>
  if (metrics.error) return <div className="panel text-coral">Backend is not reachable. Seed and run the Flask API to view live demo data.</div>

  const m = metrics.data
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Revenue At Risk" value={inr(m.revenue_at_risk)} helper="Open failed and abandoned payments" />
        <MetricCard label="Potentially Recoverable" value={inr(m.potentially_recoverable_revenue)} helper="Probability-weighted from cases" />
        <MetricCard label="Revenue Recovered" value={inr(m.revenue_recovered)} helper="Recorded recovered payments" />
        <MetricCard label="Recovery Rate" value={`${m.recovery_rate}%`} helper="Recovered cases over all cases" />
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Failed Payments" value={m.failed_payments} />
        <MetricCard label="Active Cases" value={m.active_recovery_cases} />
        <MetricCard label="Successful Recoveries" value={m.successful_recoveries} />
        <MetricCard label="Stopped/Escalated" value={m.stopped_escalated_cases} />
      </div>
      <div className="panel">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Priority Recovery Queue</h3>
          <RefreshCw size={18} className="text-slate-400" />
        </div>
        <CaseTable cases={(cases.data || []).slice(0, 6)} onOpenCase={onOpenCase} />
      </div>
    </div>
  )
}

export function CaseTable({ cases, onOpenCase }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] border-collapse text-sm">
        <thead className="table-head">
          <tr>
            <th className="px-3 py-2">Case</th>
            <th className="px-3 py-2">Customer</th>
            <th className="px-3 py-2">Amount</th>
            <th className="px-3 py-2">Reason</th>
            <th className="px-3 py-2">Action</th>
            <th className="px-3 py-2">Probability</th>
            <th className="px-3 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((item) => (
            <tr key={item.case_id} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="px-3 py-3"><button className="font-semibold text-mint" onClick={() => onOpenCase(item.case_id)}>{item.case_id}</button></td>
              <td className="px-3 py-3">{item.customer.name}</td>
              <td className="px-3 py-3">{inr(item.payment.amount)}</td>
              <td className="px-3 py-3">{item.payment.failure_reason}</td>
              <td className="px-3 py-3">{item.executed_action || item.recommended_action || 'PENDING'}</td>
              <td className="px-3 py-3">{Math.round((item.recovery_probability || 0) * 100)}%</td>
              <td className="px-3 py-3"><StatusBadge status={item.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
