import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { ordersAPI } from '../lib/api'
import type { Order } from '../types'

function getStatusColor(status: string): 'default' | 'blue' | 'ember' | 'success' {
  switch (status.toLowerCase()) {
    case 'confirmed':
    case 'processing':
      return 'blue'
    case 'delivered':
    case 'completed':
      return 'success'
    case 'cancelled':
      return 'ember'
    default:
      return 'default'
  }
}

export function OrdersPage() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    ordersAPI.list().then((res) => {
      const raw = res.data
      setOrders(Array.isArray(raw) ? raw : [])
    }).catch(() => setError('Failed to load orders.')).finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ padding: '48px 0', minHeight: '70vh' }}>
      <div className="container">
        <h1
          style={{
            fontFamily: 'var(--font-headline)',
            fontWeight: 300,
            fontSize: 'var(--text-heading)',
            letterSpacing: 'var(--tracking-heading)',
            marginBottom: '40px',
          }}
        >
          My Orders
        </h1>

        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="skeleton" style={{ height: '72px', borderRadius: '8px' }} />
            ))}
          </div>
        ) : error ? (
          <p style={{ color: 'var(--color-ember)', fontSize: '14px' }}>{error}</p>
        ) : orders.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '80px 0',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '16px',
            }}
          >
            <p
              style={{
                fontFamily: 'var(--font-headline)',
                fontWeight: 300,
                fontSize: '28px',
                color: 'var(--color-gravel)',
              }}
            >
              No orders yet
            </p>
            <Button variant="ghost" onClick={() => navigate('/products')}>
              Start Shopping
            </Button>
          </div>
        ) : (
          <div
            style={{
              background: 'var(--surface-card)',
              borderRadius: 'var(--radius-cards)',
              border: '1px solid var(--color-chalk)',
              overflow: 'hidden',
            }}
          >
            {/* Header */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 120px 120px 120px 80px',
                gap: '16px',
                padding: '14px 24px',
                borderBottom: '1px solid var(--color-chalk)',
                background: 'var(--color-powder)',
              }}
            >
              {['Order', 'Status', 'Total', 'Date', ''].map((h) => (
                <span
                  key={h}
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '12px',
                    fontWeight: 600,
                    letterSpacing: '0.7px',
                    textTransform: 'uppercase',
                    color: 'var(--color-gravel)',
                  }}
                >
                  {h}
                </span>
              ))}
            </div>

            {orders.map((order, idx) => (
              <div
                key={order.id}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 120px 120px 120px 80px',
                  gap: '16px',
                  padding: '18px 24px',
                  borderBottom: idx < orders.length - 1 ? '1px solid var(--color-chalk)' : 'none',
                  alignItems: 'center',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-powder)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    color: 'var(--color-obsidian)',
                    fontWeight: 500,
                  }}
                >
                  #{order.order_number}
                </span>
                <Badge color={getStatusColor(order.status)}>
                  {order.status}
                </Badge>
                <span style={{ fontFamily: 'var(--font-body)', fontSize: '14px', fontWeight: 500 }}>
                  {Number(order.total_amount).toLocaleString('vi-VN')} ₫
                </span>
                <span style={{ fontFamily: 'var(--font-body)', fontSize: '13px', color: 'var(--color-gravel)' }}>
                  {new Date(order.ordered_at).toLocaleDateString()}
                </span>
                <Button variant="ghost" size="sm" onClick={() => navigate(`/orders/${order.id}`)}>
                  View
                </Button>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  )
}
