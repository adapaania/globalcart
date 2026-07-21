import { useState } from 'react'

export default function SearchBar({ onOrderFound }) {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const search = async (e) => {
    e.preventDefault()
    const orderId = query.trim()
    if (!orderId) return

    setLoading(true)
    setError('')
    try {
      const res = await fetch(`/api/orders/${encodeURIComponent(orderId)}`)
      if (res.status === 404) {
        setError(`Order "${orderId}" not found.`)
        onOrderFound(null)
      } else if (!res.ok) {
        setError('Something went wrong while fetching the order.')
        onOrderFound(null)
      } else {
        const data = await res.json()
        onOrderFound(data)
      }
    } catch (err) {
      setError('Unable to reach the server. Is the backend running?')
      onOrderFound(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <form onSubmit={search} className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter Order ID (e.g. GC-1001)"
          className="flex-1 px-4 py-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2.5 rounded-lg bg-accent text-white font-medium hover:bg-blue-600 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>
      {error && (
        <p className="mt-3 text-sm text-red-600 font-medium">{error}</p>
      )}
    </div>
  )
}
