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
  cases: () => request('/cases'),
  caseDetail: (caseId) => request(`/cases/${caseId}`),
  processCase: (caseId) => request(`/cases/${caseId}/process`, { method: 'POST' }),
  audit: () => request('/audit'),
  policy: () => request('/policy'),
  updatePolicy: (payload) => request('/policy', { method: 'PUT', body: JSON.stringify(payload) }),
  simulate: (payload) => request('/simulate', { method: 'POST', body: JSON.stringify(payload) }),
}

export function inr(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0)
}
