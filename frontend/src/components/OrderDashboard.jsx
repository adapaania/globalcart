import Timeline from './Timeline'

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

export default function OrderDashboard({ order }) {
  const items = Array.isArray(order.items) ? order.items : []

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Top row */}
      <div className="p-6 border-b border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-6">
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
      </div>

      {/* Status badges */}
      <div className="p-6 border-b border-slate-100 flex flex-wrap gap-8">
        <Badge label="Order Status" styleMap={STATUS_STYLES} value={order.status} />
        <Badge label="Payment Status" styleMap={PAYMENT_STYLES} value={order.payment_status} />
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
