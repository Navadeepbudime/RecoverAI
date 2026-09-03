import { useEffect, useState } from 'react'
import { ArrowRight, CheckCircle2, Play, RotateCcw, ShieldAlert, Sparkles, TrendingDown, TrendingUp } from 'lucide-react'
import { api, inr } from '../services/api'
import { useApi } from '../hooks/useApi'

export function Simulator() {
  const policy = useApi(api.policy, [])
  const [result, setResult] = useState(null)
  const [form, setForm] = useState(null)
  const [simulating, setSimulating] = useState(false)
  const [errorMsg, setErrorMsg] = useState(null)

  useEffect(() => {
    if (policy.data) {
      setForm({
        max_automatic_retries: policy.data.max_automatic_retries ?? 2,
        retry_delay_minutes: policy.data.retry_delay_minutes ?? 30,
        high_value_threshold: policy.data.high_value_threshold ?? 20000,
        escalation_threshold: policy.data.escalation_threshold ?? 50000,
        repeated_failure_limit: policy.data.repeated_failure_limit ?? 3,
        auto_retry_enabled: policy.data.auto_retry_enabled ?? true,
      })
    }
  }, [policy.data])

  if (policy.loading || !form) return <div className="panel">Loading recovery simulator...</div>
  if (policy.error) return <div className="panel text-coral">Could not load policy baseline. Please ensure backend is running.</div>

  const update = (field, value) => setForm((prev) => ({ ...prev, [field]: value }))

  const applyPreset = (preset) => {
    if (preset === 'conservative') {
      setForm({
        ...form,
        max_automatic_retries: 1,
        retry_delay_minutes: 45,
        high_value_threshold: 10000,
        escalation_threshold: 25000,
        repeated_failure_limit: 2,
        auto_retry_enabled: true,
      })
    } else if (preset === 'aggressive') {
      setForm({
        ...form,
        max_automatic_retries: 3,
        retry_delay_minutes: 25,
        high_value_threshold: 50000,
        escalation_threshold: 100000,
        repeated_failure_limit: 4,
        auto_retry_enabled: true,
      })
    } else if (preset === 'reset' && policy.data) {
      setForm({
        max_automatic_retries: policy.data.max_automatic_retries ?? 2,
        retry_delay_minutes: policy.data.retry_delay_minutes ?? 30,
        high_value_threshold: policy.data.high_value_threshold ?? 20000,
        escalation_threshold: policy.data.escalation_threshold ?? 50000,
        repeated_failure_limit: policy.data.repeated_failure_limit ?? 3,
        auto_retry_enabled: policy.data.auto_retry_enabled ?? true,
      })
    }
  }

  const run = async () => {
    try {
      setSimulating(true)
      setErrorMsg(null)
      const data = await api.simulate(form)
      setResult(data)
    } catch (err) {
      setErrorMsg(err.message || 'Simulation failed. Please check inputs.')
    } finally {
      setSimulating(false)
    }
  }

  const delta = result?.delta
  const isPositive = delta ? delta.recovery_diff > 0 : false
  const isNegative = delta ? delta.recovery_diff < 0 : false

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Recovery Policy Simulator</h2>
          <p className="text-sm text-slate-500">
            Test policy parameter changes against all failed transactions without risking live revenue.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn-secondary text-xs"
            onClick={() => applyPreset('conservative')}
          >
            Strict Guardrails
          </button>
          <button
            type="button"
            className="btn-secondary text-xs"
            onClick={() => applyPreset('aggressive')}
          >
            Maximize Recovery
          </button>
          <button
            type="button"
            className="btn-secondary text-xs"
            onClick={() => applyPreset('reset')}
            title="Reset to current saved policy"
          >
            <RotateCcw size={13} /> Reset
          </button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[400px_1fr]">
        {/* Policy Configuration Controls */}
        <section className="panel space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-semibold text-slate-800">Simulated Policy Parameters</h3>
            <span className="text-xs font-medium text-mint bg-mint/10 px-2 py-0.5 rounded">Deterministic</span>
          </div>

          <div className="space-y-3.5">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500">
                Max Automatic Retries
              </label>
              <input
                className="input mt-1"
                type="number"
                min="0"
                max="10"
                value={form.max_automatic_retries}
                onChange={(e) => update('max_automatic_retries', e.target.value)}
              />
              <p className="mt-1 text-xs text-slate-400">Stop automatic attempts after this retry count.</p>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500">
                Retry Delay (Minutes)
              </label>
              <input
                className="input mt-1"
                type="number"
                min="1"
                max="1440"
                value={form.retry_delay_minutes}
                onChange={(e) => update('retry_delay_minutes', e.target.value)}
              />
              <p className="mt-1 text-xs text-slate-400">Optimal delay between 15-45m for temporary bank timeouts.</p>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500">
                High-Value Threshold (₹)
              </label>
              <input
                className="input mt-1"
                type="number"
                min="0"
                step="1000"
                value={form.high_value_threshold}
                onChange={(e) => update('high_value_threshold', e.target.value)}
              />
              <p className="mt-1 text-xs text-slate-400">Requires extra verification before automatic retry.</p>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500">
                Escalation Threshold (₹)
              </label>
              <input
                className="input mt-1"
                type="number"
                min="0"
                step="5000"
                value={form.escalation_threshold}
                onChange={(e) => update('escalation_threshold', e.target.value)}
              />
              <p className="mt-1 text-xs text-slate-400">Transactions above this strictly require human review.</p>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500">
                Repeated Failure Limit
              </label>
              <input
                className="input mt-1"
                type="number"
                min="1"
                max="10"
                value={form.repeated_failure_limit}
                onChange={(e) => update('repeated_failure_limit', e.target.value)}
              />
              <p className="mt-1 text-xs text-slate-400">Stop recovery if customer has this many historical failures.</p>
            </div>

            <label className="flex items-center gap-3 rounded border border-slate-200 p-3 text-sm font-medium hover:bg-slate-50 cursor-pointer">
              <input
                type="checkbox"
                className="rounded border-slate-300 text-mint focus:ring-mint h-4 w-4"
                checked={form.auto_retry_enabled}
                onChange={(e) => update('auto_retry_enabled', e.target.checked)}
              />
              <div>
                <p className="text-slate-800 text-xs font-semibold uppercase">Auto-Retry Enabled</p>
                <p className="text-xs text-slate-500 font-normal">When off, links are sent instead of retrying.</p>
              </div>
            </label>
          </div>

          {errorMsg && <div className="p-3 rounded bg-red-50 text-coral text-xs">{errorMsg}</div>}

          <button
            type="button"
            className="btn w-full mt-2 flex items-center justify-center gap-2 py-2.5"
            onClick={run}
            disabled={simulating}
          >
            <Play size={16} className={simulating ? 'animate-spin' : ''} />
            {simulating ? 'Simulating...' : 'Run Simulation'}
          </button>
        </section>

        {/* Simulation Results & Impact Analysis */}
        <section className="space-y-6">
          {result ? (
            <>
              {/* Impact Banner */}
              <div
                className={`panel border-l-4 ${
                  isPositive
                    ? 'border-l-emerald-500 bg-emerald-50/40'
                    : isNegative
                    ? 'border-l-amber-500 bg-amber-50/40'
                    : 'border-l-slate-400 bg-slate-50/40'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={`grid h-10 w-10 place-items-center rounded-full ${
                        isPositive
                          ? 'bg-emerald-100 text-emerald-700'
                          : isNegative
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {isPositive ? (
                        <TrendingUp size={20} />
                      ) : isNegative ? (
                        <TrendingDown size={20} />
                      ) : (
                        <Sparkles size={20} />
                      )}
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Net Recovery Impact
                      </p>
                      <p className="text-xl font-bold">
                        {isPositive ? `+${inr(delta.recovery_diff)}` : inr(delta.recovery_diff)}{' '}
                        <span className="text-sm font-medium text-slate-600">
                          ({delta.recovery_pct >= 0 ? `+${delta.recovery_pct}%` : `${delta.recovery_pct}%`})
                        </span>
                      </p>
                    </div>
                  </div>
                  <div className="text-right text-xs text-slate-500">
                    Calculated over {result.total_at_risk_payments} at-risk payments
                  </div>
                </div>
              </div>

              {/* Side-by-side comparison table / cards */}
              <div className="grid gap-4 sm:grid-cols-2">
                {/* Current Baseline Card */}
                <div className="panel border border-slate-200">
                  <div className="border-b border-slate-100 pb-2 mb-3 flex justify-between items-center">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Current Policy Baseline
                    </span>
                    <span className="text-xs text-slate-500">Max Retries: {result.current?.max_retries}</span>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs text-slate-500">Expected Recovery</p>
                      <p className="text-2xl font-bold text-slate-700">
                        {inr(result.current?.expected_recovery || 0)}
                      </p>
                    </div>
                    <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100 text-xs">
                      <div>
                        <p className="text-slate-400">Recoverable</p>
                        <p className="font-semibold text-slate-700">{result.current?.recoverable_cases}</p>
                      </div>
                      <div>
                        <p className="text-slate-400">Stopped</p>
                        <p className="font-semibold text-slate-700">{result.current?.stopped_cases}</p>
                      </div>
                      <div>
                        <p className="text-slate-400">Escalated</p>
                        <p className="font-semibold text-slate-700">{result.current?.escalated_cases}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Simulated Policy Card */}
                <div className="panel border-2 border-mint/40 bg-mint/[0.02]">
                  <div className="border-b border-mint/20 pb-2 mb-3 flex justify-between items-center">
                    <span className="text-xs font-bold uppercase tracking-wider text-mint">
                      Simulated Policy Result
                    </span>
                    <span className="text-xs text-slate-500">Max Retries: {result.simulated?.max_retries}</span>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs text-slate-500">Simulated Recovery</p>
                      <p className="text-2xl font-bold text-mint">
                        {inr(result.simulated?.expected_recovery || result.expected_recovery || 0)}
                      </p>
                    </div>
                    <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100 text-xs">
                      <div>
                        <p className="text-slate-400">Recoverable</p>
                        <p className="font-semibold text-slate-700">
                          {result.simulated?.recoverable_cases ?? result.recoverable_cases}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400">Stopped</p>
                        <p className="font-semibold text-slate-700">
                          {result.simulated?.stopped_cases ?? result.stopped_cases}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400">Escalated</p>
                        <p className="font-semibold text-slate-700">
                          {result.simulated?.escalated_cases ?? result.escalated_cases}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Policy Shift Diagnostics */}
              <div className="panel space-y-3">
                <h4 className="font-semibold text-sm text-slate-800">Policy Shift Summary</h4>
                <div className="grid gap-3 sm:grid-cols-3 text-sm">
                  <div className="rounded border border-slate-200 p-3">
                    <div className="flex items-center gap-2 text-slate-500 text-xs">
                      <CheckCircle2 size={15} className="text-mint" /> Recoverable Cases
                    </div>
                    <p className="mt-1 text-lg font-semibold text-slate-800">
                      {result.simulated?.recoverable_cases ?? result.recoverable_cases}{' '}
                      <span className="text-xs font-normal text-slate-500">
                        ({(result.simulated?.recoverable_cases ?? 0) - (result.current?.recoverable_cases ?? 0) >= 0 ? '+' : ''}
                        {(result.simulated?.recoverable_cases ?? 0) - (result.current?.recoverable_cases ?? 0)} shift)
                      </span>
                    </p>
                  </div>
                  <div className="rounded border border-slate-200 p-3">
                    <div className="flex items-center gap-2 text-slate-500 text-xs">
                      <ShieldAlert size={15} className="text-coral" /> Guardrail Stops
                    </div>
                    <p className="mt-1 text-lg font-semibold text-slate-800">
                      {result.simulated?.stopped_cases ?? result.stopped_cases}{' '}
                      <span className="text-xs font-normal text-slate-500">
                        {delta.stopped_diff >= 0 ? `+${delta.stopped_diff}` : delta.stopped_diff} vs baseline
                      </span>
                    </p>
                  </div>
                  <div className="rounded border border-slate-200 p-3">
                    <div className="flex items-center gap-2 text-slate-500 text-xs">
                      <ArrowRight size={15} className="text-amber-600" /> Human Escalations
                    </div>
                    <p className="mt-1 text-lg font-semibold text-slate-800">
                      {result.simulated?.escalated_cases ?? result.escalated_cases}{' '}
                      <span className="text-xs font-normal text-slate-500">
                        {delta.escalated_diff >= 0 ? `+${delta.escalated_diff}` : delta.escalated_diff} vs baseline
                      </span>
                    </p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="panel py-12 text-center text-slate-500 space-y-3">
              <div className="grid h-12 w-12 place-items-center rounded-full bg-slate-100 mx-auto text-slate-400">
                <Play size={20} />
              </div>
              <h4 className="font-semibold text-slate-700">Ready to simulate</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Adjust the policy parameters on the left or choose a preset, then click <strong>Run Simulation</strong> to compute expected recovery against the live synthetic dataset.
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
