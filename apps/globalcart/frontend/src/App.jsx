import { useState, useCallback } from 'react'
import SearchBar from './components/SearchBar'
import OrderDashboard from './components/OrderDashboard'
import SystemLogs from './components/SystemLogs'
import OrderFormModal from './components/OrderFormModal'

export default function App() {
  const [order, setOrder] = useState(null)
  const [showLogs, setShowLogs] = useState(false)
  const [modal, setModal] = useState(null) // { mode: 'create' | 'edit' }

  const handleOrderFound = useCallback((data) => {
    setOrder(data)
    setShowLogs(false)
  }, [])

  const refreshOrder = useCallback(async (orderId) => {
    try {
      const res = await fetch(`/api/orders/${orderId}`)
      if (res.ok) {
        const data = await res.json()
        setOrder(data)
      }
    } catch (e) {
      // ignore refresh failure
    }
  }, [])

  const handleSaved = useCallback((data) => {
    setOrder(data)
    setModal(null)
  }, [])

  const handleDeleted = useCallback(() => {
    setOrder(null)
    setShowLogs(false)
  }, [])

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-navy text-white shadow-md">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-accent font-bold text-lg">
            GC
          </div>
          <div>
            <h1 className="text-xl font-bold leading-tight">GlobalCart</h1>
            <p className="text-sm text-slate-300 leading-tight">
              Order Management System
            </p>
          </div>
          <div className="ml-auto">
            <button
              onClick={() => setModal({ mode: 'create' })}
              className="px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-blue-600 transition-colors"
            >
              + New Order
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-6 py-8">
        <SearchBar onOrderFound={handleOrderFound} />

        {order && (
          <>
            <div className="mt-8">
              <OrderDashboard
                order={order}
                onEdit={() => setModal({ mode: 'edit' })}
                onDeleted={handleDeleted}
                onUpdated={setOrder}
              />
            </div>

            <div className="mt-6">
              <button
                onClick={() => setShowLogs((s) => !s)}
                className="px-4 py-2 rounded-lg bg-navy text-white text-sm font-medium hover:bg-slate-700 transition-colors"
              >
                {showLogs ? 'Hide System Logs' : 'Show System Logs'}
              </button>
            </div>

            {showLogs && (
              <div className="mt-4">
                <SystemLogs
                  orderId={order.order_id}
                  onSynced={() => refreshOrder(order.order_id)}
                />
              </div>
            )}
          </>
        )}

        {!order && (
          <div className="mt-16 text-center text-slate-400">
            <p className="text-lg">Search for an order to get started.</p>
            <p className="text-sm mt-2">
              Try: GC-1001, GC-1042, GC-2020, GC-3030
            </p>
          </div>
        )}
      </main>

      <footer className="text-center text-xs text-slate-400 py-4">
        GlobalCart Internal Tools &middot; Order Management System
      </footer>

      {modal && (
        <OrderFormModal
          mode={modal.mode}
          order={modal.mode === 'edit' ? order : null}
          onClose={() => setModal(null)}
          onSaved={handleSaved}
        />
      )}
    </div>
  )
}
