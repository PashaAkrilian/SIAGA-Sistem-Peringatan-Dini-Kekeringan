import { useEffect, useState, useMemo } from 'react'
import {
  ResponsiveContainer, ComposedChart, Area, Line, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ReferenceArea,
} from 'recharts'
import { api } from './api'

const ISLANDS = ['Indo', 'Sumatera', 'Jawa', 'Kalimantan', 'Sulawesi', 'NusaTenggara', 'Maluku', 'Papua']
const ISLAND_LABEL = { Indo: 'Nasional', NusaTenggara: 'Nusa Tenggara' }
const label = (i) => ISLAND_LABEL[i] || i

const fmtDate = (s) => {
  const d = new Date(s)
  return d.toLocaleDateString('id-ID', { month: 'short', year: 'numeric' })
}
const scenarioName = (inc) => {
  if (inc < 0.08) return 'La Niña / netral — pemanasan lambat'
  if (inc < 0.18) return 'El Niño moderat — skenario dasar'
  if (inc < 0.30) return 'El Niño kuat — pemanasan agresif'
  return 'Godzilla El Niño — eskalasi ekstrem'
}

function TrendTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const row = payload[0]?.payload || {}
  return (
    <div className="tt">
      <div className="d">{fmtDate(label)}</div>
      {row.actual != null && <div className="r"><span>Aktual</span><span>{row.actual.toFixed(3)}</span></div>}
      {row.median != null && <div className="r"><span>Prediksi</span><span>{row.median.toFixed(3)}</span></div>}
      {row.lower != null && <div className="r"><span>Rentang</span><span>{row.lower.toFixed(2)}–{row.upper.toFixed(2)}</span></div>}
    </div>
  )
}

export default function App() {
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [islands, setIslands] = useState([])
  const [featImp, setFeatImp] = useState(null)
  const [fit, setFit] = useState([])

  const [island, setIsland] = useState('Indo')
  const [series, setSeries] = useState([])

  const [oniInc, setOniInc] = useState(0.15)
  const [sim, setSim] = useState(null)

  // Initial load
  useEffect(() => {
    Promise.all([
      api.metrics(), api.forecast(), api.islands(),
      api.featureImportance(), api.historicalFit(),
    ]).then(([m, f, isl, fi, hf]) => {
      setMetrics(m); setForecast(f); setIslands(isl)
      setFeatImp(fi); setFit(hf.data); setLoading(false)
    }).catch(e => { console.error(e); setLoading(false) })
  }, [])

  // Island series
  useEffect(() => {
    api.historical(island).then(r => setSeries(r.data)).catch(console.error)
  }, [island])

  // Live simulation (debounced)
  useEffect(() => {
    const t = setTimeout(() => {
      api.simulate(oniInc).then(setSim).catch(console.error)
    }, 120)
    return () => clearTimeout(t)
  }, [oniInc])

  // Build combined trend chart data (2020+ actual + fit + forecast)
  const trendData = useMemo(() => {
    if (!fit.length || !forecast) return []
    const byDate = {}
    fit.forEach(p => {
      if (p.date >= '2020-01-01') {
        byDate[p.date] = { date: p.date, median: p.median, lower: p.lower, upper: p.upper }
      }
    })
    series.forEach(p => {
      if (p.date >= '2020-01-01' && island === 'Indo') {
        byDate[p.date] = { ...(byDate[p.date] || { date: p.date }), actual: p.sdci }
      }
    })
    const fc = sim || forecast
    fc.data.forEach(p => {
      byDate[p.date] = { date: p.date, median: p.median, lower: p.lower, upper: p.upper }
    })
    return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date))
  }, [fit, series, forecast, sim, island])

  if (loading) return <div className="loading">Memuat data model…</div>

  const peakScore = sim ? sim.peak_score_median : forecast?.peak_score_median
  const peakMonth = sim ? sim.peak_month : forecast?.peak_month
  const belowCrit = peakScore < (forecast?.critical_threshold ?? 0.3)
  const verdictClass = peakScore < 0.3 ? 'v-crit' : peakScore < 0.45 ? 'v-warn' : 'v-ok'
  const extremeCount = islands.filter(i => i.status === 'extreme').length
  const warnCount = islands.filter(i => i.status === 'warning').length

  const maxShap = Math.max(...(featImp?.shap.map(s => s.value) || [1]))

  return (
    <>
      {/* Masthead */}
      <header className="masthead">
        <div className="masthead-inner">
          <div className="brand">
            <div className="brand-mark">S</div>
            <div>
              <div className="brand-name">SIAGA</div>
              <div className="brand-sub">Sistem Peringatan Dini Kekeringan · SDCI</div>
            </div>
          </div>
          <div className="status-live"><span className="pulse" />MODEL ONLINE</div>
        </div>
      </header>

      <div className="wrap">
        {/* Hero */}
        <section className="hero">
          <div className="eyebrow">Forecasting · Godzilla El Niño 2026</div>
          <h1>Membaca sinyal <em>Samudra Pasifik</em> sebelum tanahnya mengering.</h1>
          <p>
            Model XGBoost quantile membaca anomali suhu laut (ONI) dan mengubahnya
            menjadi proyeksi indeks kekeringan nasional. Geser skenario pemanasan
            di bawah untuk melihat kapan Indonesia menembus ambang kritis.
          </p>

          {/* Verdict banner */}
          <div className="verdict">
            <div className="verdict-cell">
              <div className="verdict-label">Puncak Ancaman</div>
              <div className="verdict-value">{fmtDate(peakMonth)}</div>
              <div className="verdict-note">Bulan skor SDCI terendah</div>
            </div>
            <div className="verdict-cell">
              <div className="verdict-label">Skor SDCI Median</div>
              <div className={`verdict-value ${verdictClass}`}>{peakScore?.toFixed(3)}</div>
              <div className="verdict-note">{belowCrit ? 'Di bawah ambang kritis' : 'Ambang kritis 0.30'}</div>
            </div>
            <div className="verdict-cell">
              <div className="verdict-label">Pulau Waspada</div>
              <div className="verdict-value">{warnCount + extremeCount}<span style={{fontSize:16,color:'var(--ink-faint)'}}>/8</span></div>
              <div className="verdict-note">{extremeCount} ekstrem · {warnCount} peringatan</div>
            </div>
            <div className="verdict-cell">
              <div className="verdict-label">Akurasi Model (R²)</div>
              <div className="verdict-value v-ok">{metrics?.test.r2.toFixed(3)}</div>
              <div className="verdict-note">Pada data uji tersembunyi</div>
            </div>
          </div>
        </section>

        {/* Simulator + trend */}
        <section className="block">
          <div className="section-head">
            <span className="section-index">01</span>
            <span className="section-title">Simulator Proyeksi</span>
            <span className="section-desc">
              Ubah laju pemanasan Pasifik dan model menghitung ulang proyeksi 2026 secara langsung.
            </span>
          </div>

          <div className="grid-main">
            <div className="panel">
              <div className="panel-title">Trajektori SDCI Nasional</div>
              <div className="panel-sub">Aktual (titik) · prediksi model (garis) · rentang ketidakpastian 10–90%</div>
              <ResponsiveContainer width="100%" height={360}>
                <ComposedChart data={trendData} margin={{ top: 10, right: 10, bottom: 0, left: -10 }}>
                  <CartesianGrid stroke="#1c3a4a" strokeDasharray="2 4" />
                  <XAxis dataKey="date" tickFormatter={fmtDate} stroke="#557381"
                    tick={{ fontFamily: 'IBM Plex Mono', fontSize: 11 }} minTickGap={40} />
                  <YAxis domain={[0, 1]} stroke="#557381"
                    tick={{ fontFamily: 'IBM Plex Mono', fontSize: 11 }} />
                  <Tooltip content={<TrendTooltip />} />
                  <ReferenceArea x1="2026-01-01" x2={trendData[trendData.length-1]?.date}
                    fill="#38bdf8" fillOpacity={0.04} />
                  <Area dataKey="upper" stroke="none" fill="#38bdf8" fillOpacity={0.12} />
                  <Area dataKey="lower" stroke="none" fill="#05141f" fillOpacity={1} />
                  <Line dataKey="median" stroke="#38bdf8" strokeWidth={2.5} dot={false} />
                  <Scatter dataKey="actual" fill="#eaf4f7" />
                  <ReferenceLine y={0.3} stroke="#ff5a4d" strokeDasharray="4 4"
                    label={{ value: 'Ambang kritis 0.30', fill: '#ff5a4d', fontSize: 11, position: 'insideBottomRight', fontFamily: 'IBM Plex Mono' }} />
                  <ReferenceLine x="2026-01-01" stroke="#557381" strokeDasharray="3 3" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            <div className="panel sim-controls">
              <div>
                <div className="panel-title">Skenario Pemanasan</div>
                <div className="panel-sub">Kenaikan indeks ONI per bulan</div>
              </div>
              <div className="slider-row">
                <label>Laju ONI <b>+{oniInc.toFixed(2)}/bln</b></label>
                <input type="range" min="0.02" max="0.40" step="0.01"
                  value={oniInc} onChange={e => setOniInc(parseFloat(e.target.value))} />
                <div className="scenario-hint">{scenarioName(oniInc)}</div>
              </div>

              <div className="sim-readout">
                <div className="verdict-label">Proyeksi Skor Terendah</div>
                <div className={`verdict-value ${verdictClass}`} style={{ fontSize: 40 }}>
                  {peakScore?.toFixed(3)}
                </div>
                <div className="verdict-note">pada {fmtDate(peakMonth)}</div>
                <div className="scenario-hint" style={{ marginTop: 14, color: belowCrit ? 'var(--scorch)' : 'var(--verdant)' }}>
                  {belowCrit
                    ? '⚠ Menembus ambang kekeringan ekstrem'
                    : '✓ Masih di atas ambang kritis'}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Islands */}
        <section className="block">
          <div className="section-head">
            <span className="section-index">02</span>
            <span className="section-title">Peta Sensitivitas Pulau</span>
            <span className="section-desc">
              Skor SDCI terkini tiap pulau dan korelasinya dengan anomali Pasifik.
            </span>
          </div>
          <div className="island-grid">
            {islands.map(i => (
              <div key={i.island} className={`island-card ${i.status}`}>
                <div className="island-name">{label(i.island)}</div>
                <div className="island-score">{i.current_score.toFixed(3)}</div>
                <div className="island-meta">korelasi ONI: {i.correlation_with_oni.toFixed(2)}</div>
                <span className={`tag ${i.status}`}>
                  {i.status === 'extreme' ? 'Ekstrem' : i.status === 'warning' ? 'Waspada' : 'Normal'}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Historical explorer */}
        <section className="block">
          <div className="section-head">
            <span className="section-index">03</span>
            <span className="section-title">Rekam Jejak Historis</span>
            <span className="section-desc">
              25 tahun data satelit. Perhatikan skor jatuh saat ONI melonjak (El Niño).
            </span>
          </div>
          <div className="panel">
            <div className="chips">
              {ISLANDS.map(i => (
                <button key={i} className={`chip ${island === i ? 'active' : ''}`}
                  onClick={() => setIsland(i)}>{label(i)}</button>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={series} margin={{ top: 10, right: 10, bottom: 0, left: -10 }}>
                <CartesianGrid stroke="#1c3a4a" strokeDasharray="2 4" />
                <XAxis dataKey="date" tickFormatter={fmtDate} stroke="#557381"
                  tick={{ fontFamily: 'IBM Plex Mono', fontSize: 11 }} minTickGap={50} />
                <YAxis yAxisId="l" domain={[0, 1]} stroke="#38bdf8"
                  tick={{ fontFamily: 'IBM Plex Mono', fontSize: 11 }} />
                <YAxis yAxisId="r" orientation="right" stroke="#d94f3d"
                  tick={{ fontFamily: 'IBM Plex Mono', fontSize: 11 }} />
                <Tooltip content={<TrendTooltip />} />
                <Line yAxisId="l" dataKey="sdci" name="SDCI" stroke="#38bdf8" strokeWidth={2} dot={false} />
                <Line yAxisId="r" dataKey="oni" name="ONI" stroke="#d94f3d" strokeWidth={1.5} dot={false} strokeOpacity={0.7} />
                <ReferenceLine yAxisId="l" y={0.3} stroke="#ff5a4d" strokeDasharray="4 4" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Feature importance + metrics */}
        <section className="block">
          <div className="section-head">
            <span className="section-index">04</span>
            <span className="section-title">Apa yang Model Perhatikan</span>
            <span className="section-desc">
              Kontribusi tiap fitur (SHAP) dan performa model secara keseluruhan.
            </span>
          </div>
          <div className="grid-2">
            <div className="panel">
              <div className="panel-title">Feature Importance (SHAP)</div>
              <div className="panel-sub">15 pendorong utama kekeringan nasional</div>
              <div className="bars">
                {featImp?.shap.slice(0, 15).map(s => (
                  <div key={s.feature} className="bar-row">
                    <div className="bar-label">{s.feature}</div>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${(s.value / maxShap) * 100}%` }} />
                    </div>
                    <div className="bar-val">{s.value.toFixed(4)}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="panel" style={{ marginBottom: 20 }}>
                <div className="panel-title">Performa Model</div>
                <div className="panel-sub">Diuji pada periode tersembunyi 2021–2025</div>
                <div className="metrics-strip">
                  <div className="metric-box">
                    <div className="k">R² Score</div>
                    <div className="v v-ok">{metrics?.test.r2.toFixed(3)}</div>
                    <div className="sub">varians terjelaskan</div>
                  </div>
                  <div className="metric-box">
                    <div className="k">RMSE</div>
                    <div className="v">{metrics?.test.rmse.toFixed(3)}</div>
                    <div className="sub">galat akar kuadrat</div>
                  </div>
                  <div className="metric-box">
                    <div className="k">MAE</div>
                    <div className="v">{metrics?.test.mae.toFixed(3)}</div>
                    <div className="sub">galat absolut</div>
                  </div>
                </div>
              </div>
              <div className="panel">
                <div className="panel-title">Cara Membaca</div>
                <div className="panel-sub" style={{ marginBottom: 0, lineHeight: 1.7 }}>
                  Fitur <code style={{fontFamily:'var(--mono)',color:'var(--signal)'}}>lst_Jawa</code> dan
                  {' '}<code style={{fontFamily:'var(--mono)',color:'var(--signal)'}}>ndvi_NusaTenggara</code> mendominasi —
                  wilayah monsunal ini paling sensitif terhadap sinyal Pasifik. Kehadiran
                  {' '}<code style={{fontFamily:'var(--mono)',color:'var(--signal)'}}>sst_anomaly_lag</code> membuktikan
                  model menangkap efek jeda laut-ke-darat.
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <footer>
        <div className="wrap">
          <div>SIAGA · Early Warning System · Data satelit CHIRPS · MODIS · NOAA OISST (2000–2025)</div>
          <div><code>XGBoost Quantile · FastAPI · React</code></div>
        </div>
      </footer>
    </>
  )
}
