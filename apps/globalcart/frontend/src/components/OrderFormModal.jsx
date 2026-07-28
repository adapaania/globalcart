import { useState } from 'react'

const STATUS_OPTIONS = ['PROCESSING', 'SHIPPED', 'DELIVERED', 'HELD', 'PENDING']
const PAYMENT_OPTIONS = ['SUCCESS', 'PENDING', 'FAILED']

const emptyItem = () => ({ sku: '', name: '', qty: 1, price: 0 })

/**
 * Shared modal for creating and editing an order.
 * - mode "create": POST /api/orders
 * - mode "edit":   PATCH /api/orders/{order_id}
 */
export default function OrderFormModal({ mode, order, onClose, onSaved }) {
  const isEdit = mode === 'edit'

  const [form, setForm] = useState(() => ({
    customer_name: order?.customer_name || '',
    customer_email: order?.customer_email || '',
    total_amount: order?.total_amount ?? 0,
    status: order?.status || 'PROCESSING',
    payment_status: order?.payment_status || 'PENDING',
    items:
      Array.isArray(order?.items) && order.items.length
        ? order.items.map((i) => ({
            sku: i.sku || '',
            name: i.name || '',
            qty: i.qty ?? 1,
            price: i.price ?? 0,
          }))
        : [emptyItem()],
  }))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const setField = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const setItem = (idx, k, v) =>
    setForm((f) => ({
      ...f,
      items: f.items.map((it, i) => (i === idx ? { ...it, [k]: v } : it)),
    }))

  const addItem = () => setForm((f) => ({ ...f, items: [...f.items, emptyItem()] }))
  const removeItem = (idx) =>
    setForm((f) => ({ ...f, items: f.items.filter((_, i) => i !== idx) }))

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')

    // Clean items: drop fully-empty rows, coerce numbers.
    const items = form.items
      .filter((it) => it.sku || it.name || it.price)
      .map((it) => ({
        sku: it.sku,
        name: it.name,
        qty: Number(it.qty) || 0,
        price: Number(it.price) || 0,
      }))

    const payload = {
      customer_name: form.customer_name,
      customer_email: form.customer_email,
      total_amount: Number(form.total_amount) || 0,
      status: form.status,
      payment_status: form.payment_status,
      items,
    }

    try {
      const url = isEdit ? `/api/orders/${encodeURIComponent(order.order_id)}` : '/api/orders'
      const res = await fetch(url, {
        method: isEdit ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        setError('Save failed. Please check the fields and try again.')
        setSaving(false)
        return
      }
      const data = await res.json()
      onSaved(data)
    } catch (err) {
      setError('Unable to reach the server.')
      setSaving(false)
    }
  }

  const inputCls =
    'w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent'
  const labelCls = 'block text-xs uppercase tracking-wide text-slate-500 mb-1 font-medium'

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-bold text-navy">
            {isEdit ? `Edit Order ${order.order_id}` : 'Create New Order'}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 text-2xl leading-none"
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        {/* Body */}
        <form onSubmit={submit} className="px-6 py-5 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>Customer Name</label>
              <input
                required
                className={inputCls}
                value={form.customer_name}
                onChange={(e) => setField('customer_name', e.target.value)}
              />
            </div>
            <div>
              <label className={labelCls}>Customer Email</label>
              <input
                required
                type="email"
                className={inputCls}
                value={form.customer_email}
                onChange={(e) => setField('customer_email', e.target.value)}
              />
            </div>
            <div>
              <label className={labelCls}>Total Amount (USD)</label>
              <input
                type="number"
                step="0.01"
                className={inputCls}
                value={form.total_amount}
                onChange={(e) => setField('total_amount', e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelCls}>Status</label>
                <select
                  className={inputCls}
                  value={form.status}
                  onChange={(e) => setField('status', e.target.value)}
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelCls}>Payment</label>
                <select
                  className={inputCls}
                  value={form.payment_status}
                  onChange={(e) => setField('payment_status', e.target.value)}
                >
                  {PAYMENT_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className={labelCls + ' mb-0'}>Items</label>
              <button
                type="button"
                onClick={addItem}
                className="text-xs font-medium text-accent hover:text-blue-600"
              >
                + Add Item
              </button>
            </div>
            <div className="space-y-2">
              {form.items.map((it, idx) => (
                <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                  <input
                    placeholder="SKU"
                    className={inputCls + ' col-span-3'}
                    value={it.sku}
                    onChange={(e) => setItem(idx, 'sku', e.target.value)}
                  />
                  <input
                    placeholder="Name"
                    className={inputCls + ' col-span-4'}
                    value={it.name}
                    onChange={(e) => setItem(idx, 'name', e.target.value)}
                  />
                  <input
                    placeholder="Qty"
                    type="number"
                    className={inputCls + ' col-span-2'}
                    value={it.qty}
                    onChange={(e) => setItem(idx, 'qty', e.target.value)}
                  />
                  <input
                    placeholder="Price"
                    type="number"
                    step="0.01"
                    className={inputCls + ' col-span-2'}
                    value={it.price}
                    onChange={(e) => setItem(idx, 'price', e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => removeItem(idx)}
                    className="col-span-1 text-slate-400 hover:text-red-600 text-lg"
                    aria-label="Remove item"
                  >
                    &times;
                  </button>
                </div>
              ))}
            </div>
          </div>

          {error && <p className="text-sm text-red-600 font-medium">{error}</p>}

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-blue-600 disabled:opacity-60"
            >
              {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Order'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
