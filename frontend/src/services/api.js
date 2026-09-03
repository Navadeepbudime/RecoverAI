const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!response.ok) throw new Error(`API request failed: ${response.status}`)
  return response.json()
}

export const api = {
  health: () => request('/health'),
  metrics: () => request('/metrics'),
  analytics: () => request('/analytics'),
  evaluation: () => request('/evaluation'),
  cases: (params = {}) => {
    const q = new URLSearchParams()
    if (params.status && params.status !== 'ALL') q.set('status', params.status)
    if (params.search) q.set('search', params.search)
    const qs = q.toString()
    return request(`/cases${qs ? '?' + qs : ''}`)
  },
  caseDetail: (caseId) => request(`/cases/${caseId}`),
  processCase: (caseId) => request(`/cases/${caseId}/process`, { method: 'POST' }),
  simulateLive: (scenario) => request('/simulate-live', { method: 'POST', body: JSON.stringify({ scenario }) }),
  listLiveScenarios: () => request('/simulate-live/scenarios'),
  audit: (eventFilter = null) => request(`/audit${eventFilter ? '?event=' + encodeURIComponent(eventFilter) : ''}`),
  policy: () => request('/policy'),
  updatePolicy: (payload) => request('/policy', { method: 'PUT', body: JSON.stringify(payload) }),
  simulate: (payload) => request('/simulate', { method: 'POST', body: JSON.stringify(payload) }),
}

export function inr(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0)
}
