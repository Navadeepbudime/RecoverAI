import { ArrowLeft, Play } from 'lucide-react'
import { api, inr } from '../services/api'
import { useApi } from '../hooks/useApi'
import { StatusBadge } from '../components/StatusBadge'

export function CaseDetails({ caseId, onBack }) {
  const { data, loading, error, setData } = useApi(() => api.caseDetail(caseId), [caseId])
  const process = async () => setData(await api.processCase(caseId))

  if (loading) return <div className="panel">Loading case...</div>
  if (error) return <div className="panel text-coral">Could not load case.</div>

  return (
    <div className="space-y-6">
      <button className="btn-secondary" onClick={onBack}><ArrowLeft size={16} /> Back</button>
      <div className="panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-500">{data.case_id}</p>
            <h3 className="text-2xl font-semibold">{data.customer.name}</h3>
            <p className="text-sm text-slate-500">{data.customer.email}</p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={data.status} />
            <button className="btn" onClick={process}><Play size={16} /> Process</button>
          </div>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Info title="Transaction" rows={[
          ['Payment ID', data.payment.external_id],
          ['Amount', inr(data.payment.amount)],
          ['Method', data.payment.payment_method],
          ['Failure', data.payment.failure_reason],
          ['Retries', data.payment.retry_count],
        ]} />
        <Info title="AI Decision" rows={[
          ['Risk score', data.risk_score],
          ['Recovery probability', `${Math.round(data.recovery_probability * 100)}%`],
          ['Recommended action', data.recommended_action],
          ['Priority', data.priority],
        ]} />
        <Info title="Policy Result" rows={[
          ['Decision', data.policy_decision],
          ['Executed action', data.executed_action],
          ['Outcome', data.outcome],
          ['Reason', data.policy_reason],
        ]} />
      </div>
      <div className="panel">
        <h3 className="mb-2 text-lg font-semibold">AI Explanation</h3>
        <p className="text-sm leading-6 text-slate-600">{data.ai_explanation}</p>
      </div>
      <div className="panel">
        <h3 className="mb-4 text-lg font-semibold">Timeline</h3>
        <div className="space-y-3">
          {(data.timeline || []).map((item, index) => (
            <div key={`${item.timestamp}-${index}`} className="border-l-2 border-mint pl-4">
              <p className="font-semibold">{item.event}</p>
              <p className="text-sm text-slate-500">{new Date(item.timestamp).toLocaleString()} · {item.reason}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Info({ title, rows }) {
  return (
    <div className="panel">
      <h3 className="mb-3 text-lg font-semibold">{title}</h3>
      <dl className="space-y-3 text-sm">
        {rows.map(([key, value]) => (
          <div key={key}>
            <dt className="font-medium text-slate-500">{key}</dt>
            <dd className="mt-1 break-words text-ink">{value || 'None'}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
