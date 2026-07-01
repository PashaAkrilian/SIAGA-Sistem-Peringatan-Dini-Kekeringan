// Tipis: satu tempat untuk semua panggilan ke backend.
// Saat dev, Vite proxy meneruskan /api ke http://localhost:8000
const BASE = import.meta.env.VITE_API_URL || ''

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${path} → ${res.status}`)
  return res.json()
}

export const api = {
  metrics: () => get('/api/metrics'),
  historical: (island) => get(`/api/historical?island=${island}`),
  historicalFit: () => get('/api/historical-fit'),
  forecast: () => get('/api/forecast'),
  featureImportance: () => get('/api/feature-importance'),
  islands: () => get('/api/islands'),
  simulate: (inc) => get(`/api/simulate?oni_increment=${inc}`),
}
