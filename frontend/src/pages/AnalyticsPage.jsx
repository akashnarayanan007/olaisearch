import React, { useState, useEffect } from 'react'
import {
  BarChart3, Database, Clock, CreditCard,
  TrendingUp, Loader2, RefreshCw,
} from 'lucide-react'
import { getStats, listManuscripts, healthCheck } from '../api/client'

export default function AnalyticsPage() {
  const [stats, setStats] = useState(null)
  const [manuscripts, setManuscripts] = useState([])
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = async () => {
    setRefreshing(true)
    try {
      const [s, ms, h] = await Promise.all([
        getStats().catch(() => ({})),
        listManuscripts(20).catch(() => ({ manuscripts: [] })),
        healthCheck().catch(() => ({ status: 'offline' })),
      ])
      setStats(s)
      setManuscripts(ms.manuscripts ?? [])
      setHealth(h)
    } catch {
      setHealth({ status: 'offline' })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => { load() }, [])

  // Build simple bar chart data from stats
  const statItems = Object.entries(stats ?? {})
    .filter(([, v]) => typeof v === 'number')
  const maxVal = statItems.length > 0 ? Math.max(...statItems.map(([, v]) => v)) : 1

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-serif font-bold text-stone-900">Analytics Dashboard</h1>
          <p className="text-sm text-stone-500 mt-1">
            Archive statistics, provider cost tracking, and system health
          </p>
        </div>
        <button onClick={load} className="btn-secondary text-xs">
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* ─── Health check ─────────────────────────────────────── */}
      <div className="card p-4">
        <div className="flex items-center gap-3">
          <div className={`w-2.5 h-2.5 rounded-full ${
            health?.status === 'healthy' ? 'bg-emerald-500' :
            health?.status === 'offline' ? 'bg-red-500' : 'bg-amber-500'
          }`} />
          <p className="text-sm font-medium text-stone-700">
            {health?.status === 'healthy' ? 'API Healthy' : 'API Offline'}
          </p>
          {health?.database && (
            <span className="text-xs text-stone-400">
              DB: {health.database}
            </span>
          )}
        </div>
      </div>

      {loading ? (
        <div className="card p-12 text-center">
          <Loader2 className="w-8 h-8 mx-auto text-stone-300 animate-spin mb-3" />
          <p className="text-sm text-stone-400">Loading dashboard…</p>
        </div>
      ) : (
        <>
          {/* ─── Stats grid ───────────────────────────────────── */}
          {statItems.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {statItems.map(([key, value]) => (
                <div key={key} className="card p-4 flex flex-col">
                  <div className="flex items-center gap-2 mb-2">
                    {key.toLowerCase().includes('count') && <Database className="w-4 h-4 text-palm-500" />}
                    {key.toLowerCase().includes('time') && <Clock className="w-4 h-4 text-blue-500" />}
                    {key.toLowerCase().includes('cost') && <CreditCard className="w-4 h-4 text-amber-500" />}
                    <p className="text-xs text-stone-400 uppercase tracking-wide">
                      {key.replace(/_/g, ' ')}
                    </p>
                  </div>
                  <p className="text-2xl font-bold text-stone-900">{value}</p>
                  {/* Mini bar */}
                  <div className="mt-2 h-1 bg-stone-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-palm-400 rounded-full transition-all duration-500"
                      style={{ width: `${(value / maxVal) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card p-6 text-center text-sm text-stone-400">
              No statistics available. Run the API with some uploaded manuscripts.
            </div>
          )}

          {/* ─── Recent manuscripts table ─────────────────────── */}
          {manuscripts.length > 0 && (
            <div className="card overflow-hidden">
              <div className="px-4 py-3 border-b border-stone-100 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-stone-400" />
                <p className="text-sm font-medium text-stone-700">
                  Recent Indexed Manuscripts
                </p>
                <span className="text-xs text-stone-400 ml-auto">
                  {manuscripts.length} shown
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-stone-400 border-b border-stone-100">
                      <th className="px-4 py-2 text-left font-medium">ID</th>
                      <th className="px-4 py-2 text-left font-medium">Language</th>
                      <th className="px-4 py-2 text-left font-medium">Lines</th>
                      <th className="px-4 py-2 text-left font-medium">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {manuscripts.map((ms, i) => (
                      <tr key={ms.id ?? i} className="border-b border-stone-50 hover:bg-stone-50/50">
                        <td className="px-4 py-2 font-mono text-xs text-stone-500 truncate max-w-32">
                          {ms.id ?? ms.msscript_id ?? '?'}
                        </td>
                        <td className="px-4 py-2">
                          <span className="badge badge-palm">{ms.language ?? ms.script ?? '—'}</span>
                        </td>
                        <td className="px-4 py-2 text-stone-600">
                          {ms.num_lines ?? ms.lines?.length ?? '—'}
                        </td>
                        <td className="px-4 py-2">
                          <ConfidenceBar value={ms.avg_confidence ?? ms.confidence} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ─── Provider cost section ────────────────────────── */}
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-3">
              <CreditCard className="w-4 h-4 text-amber-500" />
              <p className="text-sm font-medium text-stone-700">Provider Cost Tracking</p>
            </div>
            {stats?.total_cost_usd != null ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <CostCard label="Total Cost (USD)" value={`$${stats.total_cost_usd.toFixed(2)}`} />
                <CostCard label="Total Requests" value={stats.total_requests ?? 0} />
                <CostCard label="Avg Latency (ms)" value={stats.avg_latency_ms?.toFixed(1) ?? '—'} />
                <CostCard label="Cache Hit Rate" value={stats.cache_hit_rate ? `${(stats.cache_hit_rate * 100).toFixed(0)}%` : '—'} />
              </div>
            ) : (
              <p className="text-xs text-stone-400">
                Cost data not yet tracked. This will populate once provider calls are made
                with token/cost accounting enabled.
              </p>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function ConfidenceBar({ value }) {
  const conf = value != null ? value : 0.8
  const color = conf >= 0.8 ? 'bg-emerald-500' : conf >= 0.5 ? 'bg-amber-500' : 'bg-red-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-stone-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${conf * 100}%` }} />
      </div>
      <span className="text-xs font-mono text-stone-500 w-8">
        {(conf * 100).toFixed(0)}%
      </span>
    </div>
  )
}

function CostCard({ label, value }) {
  return (
    <div className="text-center p-3 bg-stone-50 rounded-lg">
      <p className="text-lg font-bold text-stone-900">{value}</p>
      <p className="text-xs text-stone-400">{label}</p>
    </div>
  )
}
