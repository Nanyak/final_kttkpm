import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
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

export function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    ordersAPI.detail(id).then((res) => setOrder(res.data)).catch(() => setError('Order not found.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="container" style={{ padding: '48px 0' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="skeleton" style={{ height: '48px', width: '40%' }} />
          <div className="skeleton" style={{ height: '200px', borderRadius: 'var(--radius-cards)' }} />
          <div className="skeleton" style={{ height: '200px', borderRadius: 'var(--radius-cards)' }} />
        </div>
      </div>
    )
  }

  if (error || !order) {
    return (
      <div className="container" style={{ padding: '80px 0', textAlign: 'center' }}>
        <p style={{ fontFamily: 'var(--font-headline)', fontSize: '28px', fontWeight: 300, color: 'var(--color-gravel)', marginBottom: '16px' }}>
          {error || 'Order not found'}
        </p>
        <Button variant="ghost" onClick={() => navigate('/orders')}>Back to Orders</Button>
      </div>
    )
  }

  return (
    <div style={{ padding: '48px 0' }}>
      <div className="container">
        <button
          onClick={() => navigate('/orders')}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '13px',
            color: 'var(--color-gravel)',
            fontFamily: 'var(--font-body)',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: 0,
          }}
        >
          ← Back to Orders
        </button>

        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px',
            marginBottom: '32px',
          }}
        >
          <div>
            <h1
              style={{
                fontFamily: 'var(--font-headline)',
                fontWeight: 300,
                fontSize: 'var(--text-heading)',
                letterSpacing: 'var(--tracking-heading)',
                marginBottom: '8px',
              }}
            >
              Order Detail
            </h1>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--color-gravel)' }}>
              #{order.order_number}
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Badge color={getStatusColor(order.status)}>{order.status}</Badge>
            <span style={{ fontSize: '13px', color: 'var(--color-gravel)', fontFamily: 'var(--font-body)' }}>
              {new Date(order.ordered_at).toLocaleString()}
            </span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '32px', alignItems: 'start' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Items */}
            <section
              style={{
                background: 'var(--surface-card)',
                borderRadius: 'var(--radius-cards)',
                border: '1px solid var(--color-chalk)',
                overflow: 'hidden',
              }}
            >
              <h2
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '14px',
                  fontWeight: 600,
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                  color: 'var(--color-gravel)',
                  padding: '16px 20px',
                  borderBottom: '1px solid var(--color-chalk)',
                  background: 'var(--color-powder)',
                }}
              >
                Items
              </h2>
              {order.items && order.items.length > 0 ? (
                order.items.map((item, idx) => (
                  <div
                    key={item.id}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr auto',
                      gap: '16px',
                      padding: '16px 20px',
                      borderBottom: idx < (order.items?.length || 0) - 1 ? '1px solid var(--color-chalk)' : 'none',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <p style={{ fontFamily: 'var(--font-body)', fontSize: '14px', fontWeight: 500 }}>
                        {item.product_name}
                      </p>
                      <p style={{ fontSize: '13px', color: 'var(--color-gravel)', marginTop: '3px' }}>
                        {item.quantity} × {Number(item.unit_price).toLocaleString('vi-VN')} ₫
                      </p>
                    </div>
                    <span style={{ fontFamily: 'var(--font-body)', fontSize: '14px', fontWeight: 500 }}>
                      {(Number(item.unit_price) * item.quantity).toLocaleString('vi-VN')} ₫
                    </span>
                  </div>
                ))
              ) : (
                <p style={{ padding: '20px', fontSize: '13px', color: 'var(--color-gravel)' }}>
                  No item details available
                </p>
              )}
            </section>

            {/* Shipping */}
            {order.shipping_address && (
              <section
                style={{
                  background: 'var(--surface-card)',
                  borderRadius: 'var(--radius-cards)',
                  border: '1px solid var(--color-chalk)',
                  padding: '20px',
                }}
              >
                <h2
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '14px',
                    fontWeight: 600,
                    letterSpacing: '0.5px',
                    textTransform: 'uppercase',
                    color: 'var(--color-gravel)',
                    marginBottom: '12px',
                  }}
                >
                  Shipping Address
                </h2>
                {order.shipping_address && typeof order.shipping_address === 'object' ? (
                  <div style={{ fontSize: '14px', color: 'var(--color-obsidian)', lineHeight: 1.8 }}>
                    {order.shipping_address.name && <p style={{ fontWeight: 500 }}>{order.shipping_address.name}</p>}
                    {order.shipping_address.address && <p>{order.shipping_address.address}</p>}
                    {order.shipping_address.city && <p>{order.shipping_address.city}</p>}
                    {order.shipping_address.phone && <p>Phone: {order.shipping_address.phone}</p>}
                  </div>
                ) : (
                  <p style={{ fontSize: '14px', color: 'var(--color-obsidian)', lineHeight: 1.6 }}>
                    {String(order.shipping_address)}
                  </p>
                )}
              </section>
            )}
          </div>

          {/* Summary */}
          <div
            style={{
              background: 'var(--surface-card)',
              borderRadius: 'var(--radius-cards)',
              boxShadow: 'var(--shadow-card)',
              padding: '24px',
              position: 'sticky',
              top: '80px',
            }}
          >
            <h2
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '14px',
                fontWeight: 600,
                letterSpacing: '0.5px',
                textTransform: 'uppercase',
                color: 'var(--color-gravel)',
                marginBottom: '16px',
              }}
            >
              Order Summary
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
              {order.payment_method && (
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '13px', color: 'var(--color-gravel)' }}>Payment</span>
                  <span style={{ fontSize: '13px', fontWeight: 500, textTransform: 'capitalize' }}>
                    {order.payment_method.replace('_', ' ')}
                  </span>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '13px', color: 'var(--color-gravel)' }}>Payment Status</span>
                <span style={{ fontSize: '13px', fontWeight: 500 }}>{order.payment_status}</span>
              </div>
            </div>

            <div
              style={{
                borderTop: '1px solid var(--color-chalk)',
                paddingTop: '16px',
                display: 'flex',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ fontSize: '15px', fontWeight: 600 }}>Total</span>
              <span style={{ fontSize: '18px', fontWeight: 600 }}>
                {Number(order.total_amount).toLocaleString('vi-VN')} ₫
              </span>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .container > div:last-child { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}
