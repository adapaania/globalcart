import { useState, useEffect, useCallback } from 'react'

const LEVEL_STYLES = {
  ERROR: 'bg-red-100 text-red-700 border border-red-200',
  WARN: 'bg-amber-100 text-amber-700 border border-amber-200',
  INFO: 'bg-blue-100 text-blue-700 border border-blue-200',
}

function formatTs(ts) {
  if (!ts) return ''
  try {
    return new Date(ts).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ts
  }
}

export default function SystemLogs({ orderId, onSynced }) {
  const [diag, setDiag] = useState(null)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [syncMsg, setSyncMsg] = useState('')
  const [error, setError] = useState('')

  const loadDiagnostics = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`/api/diagnostics/${encodeURIComponent(orderId)}`)
      if (!res.ok) {
        setError('Unable to load diagnostics for this order.')
        setDiag(null)
      } else {
        setDiag(await res.json())
      }
    } catch {
      setError('Unable to reach the server.')
      setDiag(null)
    } finally {
      setLoading(false)
    }
  }, [orderId])

  useEffect(() => {
    loadDiagnostics()
  }, [loadDiagnostics])

  const handleSync = async () => {
    setSyncing(true)
    setSyncMsg('')
    try {
      const res = await fetch(`/api/orders/${encodeURIComponent(orderId)}/sync`, {
        method: 'POST',
      })
      const data = await res.json()
      setSyncMsg(data.message || 'Sync completed.')
      await loadDiagnostics()
      if (onSynced) onSynced()
    } catch {
      setSyncMsg('Sync failed: unable to reach the server.')
    } finally {
      setSyncing(false)
    }
  }

  const logs = diag?.system_logs || []

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="bg-navy text-white px-6 py-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-wide">
          System Logs &amp; Diagnostics
        </h2>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="px-4 py-1.5 rounded-md bg-accent text-white text-xs font-medium hover:bg-blue-600 transition-colors disabled:opacity-60"
        >
          {syncing ? 'Syncing…' : 'Sync Order'}
        </button>
      </div>

      {syncMsg && (
        <div className="px-6 py-2 bg-blue-50 text-blue-800 text-sm border-b border-blue-100">
          {syncMsg}
        </div>
      )}

      {diag?.recommended_action && (
        <div className="px-6 py-3 bg-slate-50 border-b border-slate-100">
          <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">
            Recommended Action
          </p>
          <p className="text-sm text-slate-800">{diag.recommended_action}</p>
          {diag.error_codes?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {diag.error_codes.map((c, i) => (
                <span
                  key={i}
                  className="inline-block px-2 py-0.5 rounded text-xs font-mono bg-red-50 text-red-700 border border-red-200"
                >
                  {c}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="p-6">
        {loading && <p className="text-sm text-slate-400">Loading diagnostics…</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}

        {!loading && !error && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-100">
                  <th className="py-2 font-medium">Level</th>
                  <th className="py-2 font-medium">Timestamp</th>
                  <th className="py-2 font-medium">Message</th>
                  <th className="py-2 font-medium">Internal Code</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-slate-50 last:border-0 align-top">
                    <td className="py-2 pr-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                          LEVEL_STYLES[log.level] || LEVEL_STYLES.INFO
                        }`}
                      >
                        {log.level}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-slate-500 whitespace-nowrap">
                      {formatTs(log.timestamp)}
                    </td>
                    <td className="py-2 pr-3 text-slate-800">{log.message}</td>
                    <td className="py-2 font-mono text-xs text-slate-500">
                      {log.internal_code || '—'}
                    </td>
                  </tr>
                ))}
                {logs.length === 0 && (
                  <tr>
                    <td colSpan="4" className="py-4 text-center text-slate-400">
                      No system logs for this order.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
