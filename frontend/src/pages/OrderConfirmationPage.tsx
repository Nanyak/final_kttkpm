import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { ordersAPI } from '../lib/api'
import type { Order } from '../types'

export function OrderConfirmationPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)

  useEffect(() => {
    if (!id) return
    ordersAPI.detail(id).then((res) => setOrder(res.data)).catch(() => {})
  }, [id])

  return (
    <div
      style={{
        minHeight: '80vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
      }}
    >
      <div style={{ textAlign: 'center', maxWidth: '520px', width: '100%' }}>
        {/* Checkmark */}
        <div
          style={{
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            background: 'var(--color-chalk)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 32px',
          }}
        >
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--color-obsidian)" strokeWidth="2" strokeLinecap="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>

        <h1
          style={{
            fontFamily: 'var(--font-headline)',
            fontWeight: 300,
            fontSize: '36px',
            letterSpacing: '-0.72px',
            color: 'var(--color-obsidian)',
            marginBottom: '12px',
          }}
        >
          Order Confirmed!
        </h1>

        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '16px',
            color: 'var(--color-gravel)',
            lineHeight: 1.6,
            marginBottom: '8px',
          }}
        >
          Thank you for your purchase. Your order has been placed successfully.
        </p>

        {order && (
          <p
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '14px',
              color: 'var(--color-obsidian)',
              background: 'var(--color-powder)',
              padding: '10px 16px',
              borderRadius: '8px',
              display: 'inline-block',
              marginBottom: '8px',
            }}
          >
            Order #{order.order_number}
          </p>
        )}

        <p style={{ fontSize: '13px', color: 'var(--color-slate)', marginBottom: '40px' }}>
          We'll send you updates as your order is processed.
        </p>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button variant="ghost" onClick={() => navigate(`/orders/${id}`)}>
            View Order Details
          </Button>
          <Button variant="filled" onClick={() => navigate('/products')}>
            Continue Shopping
          </Button>
        </div>
      </div>
    </div>
  )
}
