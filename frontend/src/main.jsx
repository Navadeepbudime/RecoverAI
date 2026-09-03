import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, BarChart3, FileClock, Gauge, ListChecks, ShieldCheck, SlidersHorizontal } from 'lucide-react'
import './styles.css'
import { api } from './services/api'
import { Dashboard } from './pages/Dashboard'
import { RecoveryQueue } from './pages/RecoveryQueue'
import { CaseDetails } from './pages/CaseDetails'
import { Analytics } from './pages/Analytics'
import { AuditTrail } from './pages/AuditTrail'
import { Policy } from './pages/Policy'
import { Simulator } from './pages/Simulator'

const nav = [
  { id: 'dashboard', label: 'Dashboard', icon: Gauge },
  { id: 'queue', label: 'Recovery Queue', icon: ListChecks },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'audit', label: 'Audit Trail', icon: FileClock },
  { id: 'policy', label: 'Recovery Policy', icon: ShieldCheck },
  { id: 'simulator', label: 'Simulator', icon: SlidersHorizontal },
]

function App() {
  const [page, setPage] = useState('dashboard')
  const [selectedCase, setSelectedCase] = useState(null)
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ demo_mode: true, ai_provider: 'offline', payment_provider: 'offline' }))
  }, [])

  const content = useMemo(() => {
    if (selectedCase) return <CaseDetails caseId={selectedCase} onBack={() => setSelectedCase(null)} />
    if (page === 'queue') return <RecoveryQueue onOpenCase={setSelectedCase} />
    if (page === 'analytics') return <Analytics />
    if (page === 'audit') return <AuditTrail />
    if (page === 'policy') return <Policy />
    if (page === 'simulator') return <Simulator />
    return <Dashboard onOpenCase={setSelectedCase} />
  }, [page, selectedCase])

  return (
    <div className="min-h-screen bg-[#f7f8fa] text-ink">
      <aside className="fixed inset-y-0 left-0 z-10 hidden w-72 border-r border-slate-200 bg-white px-4 py-5 lg:block">
        <div className="flex items-center gap-3 px-2">
          <div className="grid h-10 w-10 place-items-center rounded bg-mint text-white">
            <Activity size={22} />
          </div>
          <div>
            <h1 className="text-lg font-semibold">RecoverAI</h1>
            <p className="text-xs text-slate-500">Revenue Recovery Agent</p>
          </div>
        </div>
        <nav className="mt-8 space-y-1">
          {nav.map((item) => {
            const Icon = item.icon
            const active = page === item.id && !selectedCase
            return (
              <button key={item.id} onClick={() => { setSelectedCase(null); setPage(item.id) }} className={`nav-item ${active ? 'nav-item-active' : ''}`}>
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>
      </aside>
      <main className="lg:pl-72">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 px-5 py-4 backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-mint">{health?.demo_mode ? 'DEMO MODE' : 'LIVE MODE'}</p>
              <h2 className="text-2xl font-semibold tracking-normal">Autonomous Revenue Recovery Orchestrator</h2>
            </div>
            <div className="flex gap-2 text-xs">
              <span className="pill">AI: {health?.ai_provider || 'loading'}</span>
              <span className="pill">Payments: {health?.payment_provider || 'loading'}</span>
            </div>
          </div>
          <div className="mt-4 flex gap-2 overflow-x-auto lg:hidden">
            {nav.map((item) => <button key={item.id} onClick={() => { setSelectedCase(null); setPage(item.id) }} className="mobile-nav">{item.label}</button>)}
          </div>
        </header>
        <section className="px-5 py-6">{content}</section>
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
