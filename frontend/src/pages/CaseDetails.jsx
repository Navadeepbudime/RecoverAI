import React, { useState } from 'react'
import { ArrowLeft, Check, Loader2, Play, Shield, Sparkles } from 'lucide-react'
import { api, inr } from '../services/api'
import { useApi } from '../hooks/useApi'
import { StatusBadge } from '../components/StatusBadge'

export function CaseDetails({ caseId, onBack }) {
  const { data, loading, error, setData } = useApi(() => api.caseDetail(caseId), [caseId])
  const [processing, setProcessing] = useState(false)
  const [processedMsg, setProcessedMsg] = useState(false)

  const process = async () => {
    try {
      setProcessing(true)
      const updated = await api.processCase(caseId)
      setData(updated)
      setProcessedMsg(true)
      setTimeout(() => setProcessedMsg(false), 3500)
    } catch (err) {
      alert('Error processing case: ' + err.message)
    } finally {
      setProcessing(false)
    }
  }

  if (loading) return <div className="panel">Loading recovery case...</div>
  if (error) return <div className="panel text-coral">Could not load case.</div>

  return (
    <div className="space-y-6">
      <button className="btn-secondary flex items-center gap-1.5" onClick={onBack}>
        <ArrowLeft size={16} /> Back to Queue
      </button>

      <div className="panel">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-mono font-semibold text-slate-400">{data.case_id}</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">{data.customer.name}</h3>
            <p className="text-xs text-slate-500">
              {data.customer.email} · Lifetime Value: {inr(data.customer.lifetime_value_paise / 100 || 0)}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={data.status} />
            <button
              className="btn flex items-center gap-2"
              onClick={process}
              disabled={processing || data.status === 'RECOVERED'}
            >
              {processing ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
              {processing ? 'Processing...' : data.status === 'RECOVERED' ? 'Resolved' : 'Re-Run Agent'}
            </button>
          </div>
        </div>

        {processedMsg && (
          <div className="mt-3 flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded">
            <Check size={14} /> Agent executed pipeline and updated audit log!
          </div>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Info
          title="Payment Incident"
          icon={<Shield size={16} className="text-slate-400" />}
          rows={[
            ['Payment ID', data.payment.external_id],
            ['Amount', inr(data.payment.amount)],
            ['Method', data.payment.payment_method.toUpperCase()],
            ['Failure Reason', data.payment.failure_reason],
            ['Retry Attempts', data.payment.retry_count],
          ]}
        />
        <Info
          title="AI Synthesis"
          icon={<Sparkles size={16} className="text-mint" />}
          rows={[
            ['Risk Score', `${data.risk_score} / 100`],
            ['Recovery Probability', `${Math.round((data.recovery_probability || 0) * 100)}%`],
            ['Recommended Action', data.recommended_action || 'None'],
            ['Priority Level', data.priority || 'MEDIUM'],
          ]}
        />
        <Info
          title="Policy & Execution"
          icon={<Check size={16} className="text-emerald-600" />}
          rows={[
            ['Policy Verdict', data.policy_decision || 'PENDING'],
            ['Executed Action', data.executed_action || 'None'],
            ['Outcome Status', data.outcome || 'PENDING'],
            ['Policy Notes', data.policy_reason || 'Complies with guardrails.'],
          ]}
        />
      </div>

      {/* AI Contextual Explanation */}
      <div className="panel space-y-2">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-mint" />
          <h3 className="text-base font-semibold text-slate-900">AI Decision Rationale & Memory</h3>
        </div>
        <p className="text-sm leading-relaxed text-slate-700 bg-slate-50 p-3.5 rounded border border-slate-100">
          {data.ai_explanation || 'No explanation recorded.'}
        </p>
      </div>

      {/* Decision Audit Timeline */}
      <div className="panel space-y-4">
        <h3 className="text-base font-semibold text-slate-900">Decision & Action Audit Trail</h3>
        <div className="space-y-3">
          {(data.timeline || []).map((item, index) => (
            <div key={`${item.timestamp}-${index}`} className="border-l-2 border-mint pl-4 py-0.5 space-y-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-semibold text-xs text-slate-800 uppercase tracking-wide">
                  {item.event}
                </span>
                <span className="text-[11px] text-slate-400 font-mono">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <p className="text-xs text-slate-600">{item.reason}</p>
              {item.executed_action && (
                <p className="text-[11px] text-slate-500 font-medium">
                  Executed: <strong>{item.executed_action}</strong> · Result: <strong>{item.result}</strong>
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Info({ title, icon, rows }) {
  return (
    <div className="panel space-y-3">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
        {icon}
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      </div>
      <dl className="space-y-2 text-xs">
        {rows.map(([key, value]) => (
          <div key={key} className="flex justify-between items-center py-0.5 border-b border-slate-50">
            <dt className="text-slate-500 font-medium">{key}</dt>
            <dd className="font-semibold text-slate-800">{value || 'None'}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
