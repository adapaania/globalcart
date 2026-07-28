import { useState } from 'react'
import Timeline from './Timeline'

const STATUS_OPTIONS = ['PROCESSING', 'SHIPPED', 'DELIVERED', 'HELD', 'PENDING']

const STATUS_STYLES = {
  PROCESSING: 'bg-blue-100 text-blue-700 border border-blue-200',
  SHIPPED: 'bg-indigo-100 text-indigo-700 border border-indigo-200',
  DELIVERED: 'bg-green-100 text-green-700 border border-green-200',
  HELD: 'bg-amber-100 text-amber-700 border border-amber-200',
  PENDING: 'bg-slate-100 text-slate-700 border border-slate-200',
}

const PAYMENT_STYLES = {
  SUCCESS: 'bg-green-100 text-green-700 border border-green-200',
  PENDING: 'bg-amber-100 text-amber-700 border border-amber-200',
  FAILED: 'bg-red-100 text-red-700 border border-red-200',
}

function Badge({ label, styleMap, value }) {
  const cls = styleMap[value] || 'bg-slate-100 text-slate-700 border border-slate-200'
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{label}</p>
      <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${cls}`}>
        {value}
      </span>
    </div>
  )
}

function money(n) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(n ?? 0)
}

export default function OrderDashboard({ order, onEdit, onDeleted, onUpdated }) {
  const items = Array.isArray(order.items) ? order.items : []
  const [busy, setBusy] = useState(false)

  const quickStatusChange = async (newStatus) => {
    if (newStatus === order.status) return
    setBusy(true)
    try {
      const res = await fetch(`/api/orders/${encodeURIComponent(order.order_id)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
      if (res.ok) {
        const data = await res.json()
        onUpdated && onUpdated(data)
      }
    } catch (e) {
      // ignore
    } finally {
      setBusy(false)
    }
  }

  const deleteOrder = async () => {
    if (!window.confirm(`Are you sure you want to delete ${order.order_id}?`)) return
    setBusy(true)
    try {
      const res = await fetch(`/api/orders/${encodeURIComponent(order.order_id)}`, {
        method: 'DELETE',
      })
      if (res.ok) {
        onDeleted && onDeleted()
      }
    } catch (e) {
      // ignore
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Top row */}
      <div className="p-6 border-b border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-6 relative">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Order ID</p>
          <p className="text-lg font-bold text-navy">{order.order_id}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Customer</p>
          <p className="text-sm font-semibold text-slate-800">{order.customer_name}</p>
          <p className="text-sm text-slate-500">{order.customer_email}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Total Amount</p>
          <p className="text-lg font-bold text-navy">{money(order.total_amount)}</p>
        </div>

        {/* Edit / Delete actions */}
        <div className="absolute top-4 right-4 flex items-center gap-2">
          <button
            onClick={onEdit}
            disabled={busy}
            title="Edit order"
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-accent transition-colors disabled:opacity-50"
          >
            {/* pencil icon */}
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={deleteOrder}
            disabled={busy}
            title="Delete order"
            className="p-2 rounded-lg text-slate-500 hover:bg-red-50 hover:text-red-600 transition-colors disabled:opacity-50"
          >
            {/* trash icon */}
            <svg xmlns="https://shadcn.io/og?iconName=trash&iconLibrary=heroicons" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Status badges + quick status update */}
      <div className="p-6 border-b border-slate-100 flex flex-wrap items-end gap-8">
        <Badge label="Order Status" styleMap={STATUS_STYLES} value={order.status} />
        <Badge label="Payment Status" styleMap={PAYMENT_STYLES} value={order.payment_status} />
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Quick Update</p>
          <select
            value={order.status}
            disabled={busy}
            onChange={(e) => quickStatusChange(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent disabled:opacity-50"
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Items */}
      <div className="p-6 border-b border-slate-100">
        <p className="text-sm font-semibold text-slate-700 mb-3">Items Ordered</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-100">
                <th className="py-2 font-medium">SKU</th>
                <th className="py-2 font-medium">Item</th>
                <th className="py-2 font-medium text-center">Qty</th>
                <th className="py-2 font-medium text-right">Price</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it, idx) => (
                <tr key={idx} className="border-b border-slate-50 last:border-0">
                  <td className="py-2 font-mono text-slate-500">{it.sku}</td>
                  <td className="py-2 text-slate-800">{it.name}</td>
                  <td className="py-2 text-center text-slate-600">{it.qty}</td>
                  <td className="py-2 text-right text-slate-800">{money(it.price)}</td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan="4" className="py-4 text-center text-slate-400">
                    No items on this order.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Timeline */}
      <div className="p-6">
        <p className="text-sm font-semibold text-slate-700 mb-4">Order Timeline</p>
        <Timeline events={order.events || []} />
      </div>
    </div>
  )
}
