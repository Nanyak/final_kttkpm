import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { useCart } from '../context/CartContext'

export function CartPage() {
  const navigate = useNavigate()
  const { cart, updateItem, removeItem, loading } = useCart()

  if (loading) {
    return (
      <div className="container" style={{ padding: '80px 0' }}>
        <div className="skeleton" style={{ height: '400px', borderRadius: 'var(--radius-cards)' }} />
      </div>
    )
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div
        style={{
          minHeight: '60vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '20px',
          textAlign: 'center',
        }}
      >
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="var(--color-chalk)" strokeWidth="1">
          <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
          <line x1="3" y1="6" x2="21" y2="6" />
          <path d="M16 10a4 4 0 0 1-8 0" />
        </svg>
        <h2
          style={{
            fontFamily: 'var(--font-headline)',
            fontWeight: 300,
            fontSize: '32px',
            color: 'var(--color-gravel)',
          }}
        >
          Your cart is empty
        </h2>
        <p style={{ color: 'var(--color-slate)', fontSize: '14px' }}>
          Add some products to get started.
        </p>
        <Button variant="ghost" onClick={() => navigate('/products')}>
          Continue Shopping
        </Button>
      </div>
    )
  }

  const subtotal = Number(cart.total_amount)
  const shipping = subtotal > 500000 ? 0 : 30000
  const total = subtotal + shipping

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
          Your Cart
        </h1>

        <div style={{ display: 'grid', gridTemplateColumns: '60% 40%', gap: '40px', alignItems: 'start' }}>
          {/* Items */}
          <div
            style={{
              background: 'var(--surface-card)',
              borderRadius: 'var(--radius-cards)',
              border: '1px solid var(--color-chalk)',
              overflow: 'hidden',
            }}
          >
            {cart.items.map((item, idx) => (
              <div
                key={item.id}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr auto',
                  gap: '16px',
                  padding: '24px',
                  borderBottom: idx < cart.items.length - 1 ? '1px solid var(--color-chalk)' : 'none',
                  alignItems: 'center',
                }}
              >
                <div>
                  <h3
                    style={{
                      fontFamily: 'var(--font-body)',
                      fontSize: '15px',
                      fontWeight: 500,
                      marginBottom: '6px',
                    }}
                  >
                    {item.product_name}
                  </h3>
                  <p style={{ fontSize: '13px', color: 'var(--color-gravel)' }}>
                    {Number(item.unit_price).toLocaleString('vi-VN')} ₫ each
                  </p>
                  <p style={{ fontSize: '13px', color: 'var(--color-gravel)', marginTop: '4px' }}>
                    Subtotal: <strong>{(Number(item.unit_price) * item.quantity).toLocaleString('vi-VN')} ₫</strong>
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '12px' }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      border: '1px solid var(--color-chalk)',
                      borderRadius: 'var(--radius-lg)',
                      overflow: 'hidden',
                    }}
                  >
                    <button
                      disabled={item.quantity <= 1}
                      onClick={() => updateItem(item.id, item.quantity - 1)}
                      style={{
                        width: '32px',
                        height: '32px',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '16px',
                        color: 'var(--color-obsidian)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      −
                    </button>
                    <span
                      style={{
                        width: '36px',
                        textAlign: 'center',
                        fontFamily: 'var(--font-body)',
                        fontSize: '14px',
                        fontWeight: 500,
                        borderLeft: '1px solid var(--color-chalk)',
                        borderRight: '1px solid var(--color-chalk)',
                        lineHeight: '32px',
                        height: '32px',
                      }}
                    >
                      {item.quantity}
                    </span>
                    <button
                      onClick={() => updateItem(item.id, item.quantity + 1)}
                      style={{
                        width: '32px',
                        height: '32px',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '16px',
                        color: 'var(--color-obsidian)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      +
                    </button>
                  </div>
                  <button
                    onClick={() => removeItem(item.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '12px',
                      color: 'var(--color-slate)',
                      fontFamily: 'var(--font-body)',
                      textDecoration: 'underline',
                      padding: 0,
                    }}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Order Summary */}
          <div
            style={{
              background: 'var(--surface-card)',
              borderRadius: 'var(--radius-cards)',
              boxShadow: 'var(--shadow-card)',
              padding: '28px',
              position: 'sticky',
              top: '80px',
            }}
          >
            <h2
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '16px',
                fontWeight: 600,
                marginBottom: '20px',
              }}
            >
              Order Summary
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '14px', color: 'var(--color-gravel)' }}>
                  Subtotal ({cart.total_items} item{cart.total_items !== 1 ? 's' : ''})
                </span>
                <span style={{ fontSize: '14px', fontWeight: 500 }}>
                  {subtotal.toLocaleString('vi-VN')} ₫
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '14px', color: 'var(--color-gravel)' }}>Shipping</span>
                <span style={{ fontSize: '14px', fontWeight: 500 }}>
                  {shipping === 0 ? 'Free' : `${shipping.toLocaleString('vi-VN')} ₫`}
                </span>
              </div>
              {shipping === 0 && (
                <p style={{ fontSize: '12px', color: 'var(--color-success)' }}>
                  Free shipping on orders over 500,000 ₫
                </p>
              )}
            </div>

            <div
              style={{
                borderTop: '1px solid var(--color-chalk)',
                paddingTop: '16px',
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: '24px',
              }}
            >
              <span style={{ fontSize: '15px', fontWeight: 600 }}>Total</span>
              <span style={{ fontSize: '18px', fontWeight: 600 }}>
                {total.toLocaleString('vi-VN')} ₫
              </span>
            </div>

            <Button
              variant="filled"
              style={{ width: '100%' }}
              onClick={() => navigate('/checkout')}
            >
              Proceed to Checkout
            </Button>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .container > div { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}
