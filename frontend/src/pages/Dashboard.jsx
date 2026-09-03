import React, { useState } from 'react'
import {
  ArrowUpRight,
  CheckCircle2,
  ChevronRight,
  Loader2,
  Play,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  X,
  Zap,
} from 'lucide-react'
import { api, inr } from '../services/api'
import { useApi } from '../hooks/useApi'
import { MetricCard } from '../components/MetricCard'
import { StatusBadge } from '../components/StatusBadge'

export function Dashboard({ onOpenCase }) {
  const metrics = useApi(api.metrics, [])
  const evaluation = useApi(api.evaluation, [])
  const cases = useApi(api.cases, [])

  const [activeSimulating, setActiveSimulating] = useState(false)
  const [simResult, setSimResult] = useState(null)
  const [simScenario, setSimScenario] = useState(null)

  const reloadData = async () => {
    try {
      const [m, e, c] = await Promise.all([api.metrics(), api.evaluation(), api.cases()])
      metrics.setData(m)
      evaluation.setData(e)
      cases.setData(c)
    } catch (err) {
      console.error('Failed to reload dashboard data', err)
    }
  }

  const handleSimulateLive = async (scenarioKey) => {
    try {
      setActiveSimulating(true)
      setSimScenario(scenarioKey)
      setSimResult(null)
      const res = await api.simulateLive(scenarioKey)
      setSimResult(res)
      await reloadData()
    } catch (err) {
      alert('Live simulation error: ' + err.message)
    } finally {
      setActiveSimulating(false)
    }
  }

  if (metrics.loading || cases.loading || evaluation.loading) {
    return <div className="panel">Loading RecoverAI Command Center...</div>
  }

  if (metrics.error) {
    return (
      <div className="panel text-coral">
        Backend is not reachable. Ensure the Flask API is running on port 5000.
      </div>
    )
  }

  const m = metrics.data || {}
  const ev = evaluation.data || {}

  const liftPct = ev.incremental_lift_percentage ?? 0
  const incrementalRev = ev.incremental_revenue ?? 0

  return (
    <div className="space-y-6">
      {/* Primary Hero Section: Revenue Recovered & Incremental Lift */}
      <div className="rounded-xl border border-emerald-200 bg-gradient-to-r from-emerald-50 via-teal-50/40 to-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <p className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                Primary Recovery Metric
              </p>
            </div>
            <h1 className="mt-2 text-4xl font-extrabold tracking-tight text-slate-900">
              {inr(m.revenue_recovered)}
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Actual recovered revenue captured through intelligent intervention
            </p>
          </div>

          <div className="flex flex-col items-start sm:items-end gap-2">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-800">
              <TrendingUp size={16} />
              +{liftPct}% vs. Naive Retry
            </div>
            <p className="text-xs text-slate-500 font-medium">
              Incremental Lift: <span className="font-bold text-slate-700">+{inr(incrementalRev)}</span>
            </p>
            <p className="text-[11px] text-slate-400">
              Compared to dumb retry baseline ({inr(ev.baseline_recovered_revenue || 0)})
            </p>
          </div>
        </div>

        {/* Secondary KPI Bar */}
        <div className="mt-6 grid grid-cols-2 gap-3 border-t border-emerald-100/80 pt-4 md:grid-cols-4">
          <div>
            <p className="text-xs text-slate-500">Revenue At Risk</p>
            <p className="text-lg font-bold text-slate-800">{inr(m.revenue_at_risk)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Potential Recovery</p>
            <p className="text-lg font-bold text-slate-800">{inr(m.potentially_recoverable_revenue)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">RecoverAI Win Rate</p>
            <p className="text-lg font-bold text-emerald-700">
              {ev.recoverai_recovery_rate ?? m.recovery_rate}%{' '}
              <span className="text-xs font-normal text-slate-400">
                (vs {ev.baseline_recovery_rate || 12}% baseline)
              </span>
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Successful Recoveries</p>
            <p className="text-lg font-bold text-slate-800">
              {m.successful_recoveries}{' '}
              <span className="text-xs font-normal text-slate-400">
                ({m.active_recovery_cases} active cases)
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Live Simulation Action Bar (Priority 4 for Buildathon Demo) */}
      <div className="panel border-2 border-indigo-100 bg-indigo-50/20">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <Zap size={18} className="text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Live Pipeline Demonstration · Trigger Instant Failure Event
            </h3>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            Test how RecoverAI orchestrates in real time
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {[
            { key: 'BANK_TIMEOUT', label: '⚡ Bank Timeout (₹8,499)' },
            { key: 'INSUFFICIENT_FUNDS', label: '⚡ Insufficient Funds (₹24,999)' },
            { key: 'EXPIRED_CARD', label: '⚡ Expired Card (₹4,999)' },
            { key: 'CHECKOUT_ABANDONED', label: '⚡ Abandoned Cart (₹3,299)' },
            { key: 'HIGH_VALUE_TIMEOUT', label: '⚡ High-Value Escalation (₹75,000)' },
          ].map((sc) => (
            <button
              key={sc.key}
              type="button"
              disabled={activeSimulating}
              onClick={() => handleSimulateLive(sc.key)}
              className="btn-secondary text-xs hover:border-indigo-300 hover:text-indigo-700 flex items-center gap-1.5"
            >
              {activeSimulating && simScenario === sc.key ? (
                <Loader2 size={13} className="animate-spin text-indigo-600" />
              ) : null}
              {sc.label}
            </button>
          ))}
        </div>

        {/* Live Simulation Pipeline Trace Modal / Drawer */}
        {simResult && (
          <div className="mt-4 rounded-lg border border-indigo-200 bg-white p-4 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-emerald-600" />
                <p className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Live Event Pipeline Progression: {simResult.case?.case_id}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSimResult(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={16} />
              </button>
            </div>

            {/* Step-by-Step Pipeline View */}
            <div className="grid gap-2 sm:grid-cols-5 text-xs">
              {(simResult.pipeline_trace || []).map((step, idx) => (
                <div key={idx} className="rounded border border-slate-100 bg-slate-50/60 p-2.5 space-y-1">
                  <p className="font-bold text-slate-700">{step.stage}</p>
                  <p className="text-[11px] text-slate-500 leading-snug line-clamp-3" title={step.detail}>
                    {step.detail}
                  </p>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between pt-1 text-xs">
              <span className="text-slate-500">
                Action Executed: <strong>{simResult.case?.executed_action}</strong> · Outcome:{' '}
                <strong>{simResult.case?.outcome}</strong>
              </span>
              <button
                type="button"
                onClick={() => onOpenCase(simResult.case?.case_id)}
                className="text-mint font-semibold hover:underline flex items-center gap-1"
              >
                Inspect Full Case Details <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Comparative Evaluation Card: Baseline vs RecoverAI */}
      <div className="panel border border-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-3 mb-4">
          <div>
            <h3 className="font-semibold text-slate-900">Baseline Retry vs. RecoverAI Next-Best-Action</h3>
            <p className="text-xs text-slate-500">
              Evaluated over the identical dataset of {ev.total_cases_evaluated || 35} payment incidents
            </p>
          </div>
          <span className="rounded bg-indigo-50 border border-indigo-200 px-2.5 py-1 text-xs font-semibold text-indigo-700">
            Incremental Revenue: +{inr(incrementalRev)}
          </span>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded border border-slate-200 p-4">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Naive Retry Baseline
            </p>
            <p className="mt-1 text-2xl font-bold text-slate-700">
              {inr(ev.baseline_recovered_revenue || 0)}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Recovery Rate: <strong>{ev.baseline_recovery_rate}%</strong>
            </p>
            <p className="text-[11px] text-slate-400 mt-1">
              Fails 100% of expired cards, abandonments, and insufficient funds.
            </p>
          </div>

          <div className="rounded border-2 border-mint/40 bg-mint/[0.02] p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-mint uppercase tracking-wider">
                RecoverAI Orchestrator
              </p>
              <Sparkles size={14} className="text-mint" />
            </div>
            <p className="mt-1 text-2xl font-bold text-mint">
              {inr(ev.recoverai_recovered_revenue || 0)}
            </p>
            <p className="mt-2 text-xs text-slate-600">
              Recovery Rate: <strong className="text-mint">{ev.recoverai_recovery_rate}%</strong>
            </p>
            <p className="text-[11px] text-slate-500 mt-1">
              Next-best action: payment links, method switches, reminders & timed retries.
            </p>
          </div>

          <div className="rounded border border-emerald-200 bg-emerald-50/30 p-4">
            <p className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">
              Net Merchant Advantage
            </p>
            <p className="mt-1 text-2xl font-bold text-emerald-700">
              +{inr(incrementalRev)}
            </p>
            <p className="mt-2 text-xs text-emerald-800 font-medium">
              +{liftPct}% Revenue Lift
            </p>
            <p className="text-[11px] text-emerald-700/80 mt-1">
              Zero additional gateway fee burn from blind retries.
            </p>
          </div>
        </div>
      </div>

      {/* Priority Recovery Queue Table */}
      <div className="panel">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Priority Recovery Queue</h3>
            <p className="text-xs text-slate-500">Most recent payment incidents and orchestrated actions</p>
          </div>
          <button
            type="button"
            onClick={reloadData}
            title="Refresh cases"
            className="p-1.5 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition"
          >
            <RefreshCw size={16} />
          </button>
        </div>
        <CaseTable cases={(cases.data || []).slice(0, 8)} onOpenCase={onOpenCase} />
      </div>
    </div>
  )
}

export function CaseTable({ cases, onOpenCase }) {
  if (!cases || cases.length === 0) {
    return <div className="py-8 text-center text-sm text-slate-400">No cases found.</div>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] border-collapse text-sm">
        <thead className="table-head">
          <tr>
            <th className="px-3 py-2">Case ID</th>
            <th className="px-3 py-2">Customer</th>
            <th className="px-3 py-2">Amount</th>
            <th className="px-3 py-2">Failure Reason</th>
            <th className="px-3 py-2">Action</th>
            <th className="px-3 py-2">Probability</th>
            <th className="px-3 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((item) => (
            <tr key={item.case_id} className="border-b border-slate-100 hover:bg-slate-50 transition">
              <td className="px-3 py-3">
                <button className="font-semibold text-mint hover:underline" onClick={() => onOpenCase(item.case_id)}>
                  {item.case_id}
                </button>
              </td>
              <td className="px-3 py-3">
                <p className="font-medium text-slate-800">{item.customer.name}</p>
                <p className="text-xs text-slate-400">{item.customer.email}</p>
              </td>
              <td className="px-3 py-3 font-semibold text-slate-800">{inr(item.payment.amount)}</td>
              <td className="px-3 py-3">
                <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600 font-mono">
                  {item.payment.failure_reason}
                </span>
              </td>
              <td className="px-3 py-3">
                <span className="font-medium text-xs text-slate-700">
                  {item.executed_action || item.recommended_action || 'PENDING'}
                </span>
              </td>
              <td className="px-3 py-3 font-medium text-slate-600">
                {Math.round((item.recovery_probability || 0) * 100)}%
              </td>
              <td className="px-3 py-3">
                <StatusBadge status={item.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
