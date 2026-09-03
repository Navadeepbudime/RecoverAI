import React, { useEffect, useState } from 'react'
import { Filter, RefreshCw, Search } from 'lucide-react'
import { api } from '../services/api'
import { CaseTable } from './Dashboard'

const STATUS_FILTERS = [
  { id: 'ALL', label: 'All Incidents' },
  { id: 'ACTIVE', label: 'Active' },
  { id: 'RECOVERED', label: 'Recovered' },
  { id: 'ESCALATED', label: 'Escalated' },
  { id: 'STOPPED', label: 'Stopped' },
]

export function RecoveryQueue({ onOpenCase }) {
  const [status, setStatus] = useState('ALL')
  const [searchTerm, setSearchTerm] = useState('')
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadCases = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.cases({ status, search: searchTerm })
      setCases(data || [])
    } catch (err) {
      setError(err.message || 'Failed to load cases')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      loadCases()
    }, 150)
    return () => clearTimeout(timer)
  }, [status, searchTerm])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Recovery Incidents Queue</h2>
          <p className="text-sm text-slate-500">
            Real-time feed of all revenue risk incidents, orchestrated actions, and outcomes.
          </p>
        </div>
        <button
          type="button"
          onClick={loadCases}
          disabled={loading}
          className="btn-secondary text-xs flex items-center gap-1.5"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      <div className="panel space-y-4">
        {/* Filter Controls & Search */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
          {/* Status Tabs */}
          <div className="flex flex-wrap gap-1.5">
            {STATUS_FILTERS.map((tab) => {
              const active = status === tab.id
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setStatus(tab.id)}
                  className={`rounded px-3 py-1.5 text-xs font-semibold transition ${
                    active
                      ? 'bg-ink text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              )
            })}
          </div>

          {/* Search Box */}
          <div className="relative min-w-[240px]">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              className="input pl-8 py-1.5 text-xs w-full"
              placeholder="Search customer, case, or payment ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Results Info */}
        <div className="text-xs text-slate-500 flex justify-between items-center">
          <span>
            Showing <strong>{cases.length}</strong> incident{cases.length === 1 ? '' : 's'}
            {status !== 'ALL' ? ` with status '${status}'` : ''}
            {searchTerm ? ` matching "${searchTerm}"` : ''}
          </span>
        </div>

        {/* Table */}
        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading cases...</div>
        ) : error ? (
          <div className="py-8 text-center text-sm text-coral">{error}</div>
        ) : (
          <CaseTable cases={cases} onOpenCase={onOpenCase} />
        )}
      </div>
    </div>
  )
}
