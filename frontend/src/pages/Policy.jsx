import { useEffect, useState } from 'react'
import { Check, Loader2, Save } from 'lucide-react'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'

export function Policy() {
  const { data, loading, error, setData } = useApi(api.policy, [])
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [savedSuccess, setSavedSuccess] = useState(false)

  useEffect(() => setForm(data), [data])
  if (loading || !form) return <div className="panel">Loading policy...</div>
  if (error) return <div className="panel text-coral">Could not load policy. Please check backend.</div>

  const update = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setSavedSuccess(false)
  }

  const save = async () => {
    try {
      setSaving(true)
      const updated = await api.updatePolicy(form)
      setData(updated)
      setSavedSuccess(true)
      setTimeout(() => setSavedSuccess(false), 3500)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="panel max-w-3xl space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Merchant Recovery Policy</h3>
        <p className="mt-1 text-sm text-slate-500">
          Deterministic guardrails stored in the database. Every AI recommendation must pass through these rules before execution.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Max automatic retries" value={form.max_automatic_retries} onChange={(v) => update('max_automatic_retries', v)} />
        <Field label="Retry delay minutes" value={form.retry_delay_minutes} onChange={(v) => update('retry_delay_minutes', v)} />
        <Field label="High-value threshold (₹)" value={form.high_value_threshold} onChange={(v) => update('high_value_threshold', v)} />
        <Field label="Escalation threshold (₹)" value={form.escalation_threshold} onChange={(v) => update('escalation_threshold', v)} />
        <Field label="Repeated failure limit" value={form.repeated_failure_limit} onChange={(v) => update('repeated_failure_limit', v)} />
        <label className="flex items-center gap-3 rounded border border-slate-200 px-3 py-2 text-sm font-medium hover:bg-slate-50 cursor-pointer">
          <input
            type="checkbox"
            className="rounded border-slate-300 text-mint focus:ring-mint h-4 w-4"
            checked={form.auto_retry_enabled}
            onChange={(e) => update('auto_retry_enabled', e.target.checked)}
          />
          <div>
            <p className="text-slate-800 text-xs font-semibold uppercase">Automatic retries enabled</p>
            <p className="text-xs text-slate-500 font-normal">Allow AI to auto-retry temporary timeouts</p>
          </div>
        </label>
      </div>

      <div className="flex items-center gap-3 pt-2">
        <button className="btn flex items-center gap-2" onClick={save} disabled={saving}>
          {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          {saving ? 'Saving...' : 'Save Policy'}
        </button>

        {savedSuccess && (
          <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded">
            <Check size={14} /> Policy saved to database!
          </span>
        )}
      </div>
    </div>
  )
}

function Field({ label, value, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-600 block">
      {label}
      <input
        className="input mt-1"
        type="number"
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  )
}
