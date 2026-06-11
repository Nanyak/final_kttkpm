import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { useCart } from '../context/CartContext'
import { ordersAPI } from '../lib/api'

export function CheckoutPage() {
  const navigate = useNavigate()
  const { cart, refreshCart } = useCart()
  const [form, setForm] = useState({
    name: '',
    address: '',
    city: '',
    phone: '',
    payment_method: 'cod',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState('')

  const update = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: '' }))
  }

  const validate = () => {
    const newErrors: Record<string, string> = {}
    if (!form.name.trim()) newErrors.name = 'Name is required'
    if (!form.address.trim()) newErrors.address = 'Address is required'
    if (!form.city.trim()) newErrors.city = 'City is required'
    if (!form.phone.trim()) newErrors.phone = 'Phone is required'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setSubmitting(true)
    setServerError('')
    try {
      const res = await ordersAPI.create({
        shipping_address: {
          name: form.name,
          address: form.address,
          city: form.city,
          phone: form.phone,
        },
        payment_method: form.payment_method,
      })
      await refreshCart()
      navigate(`/orders/${res.data.id}/confirmation`)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string; message?: string } } }
      setServerError(
        axiosErr.response?.data?.detail || axiosErr.response?.data?.message || 'Failed to place order. Please try again.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  const subtotal = cart ? Number(cart.total_amount) : 0
  const shipping = subtotal > 500000 ? 0 : 30000
  const total = subtotal + (cart ? shipping : 0)

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
          Checkout
        </h1>

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '60% 40%', gap: '40px', alignItems: 'start' }}>
            {/* Form */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
              {/* Shipping */}
              <section
                style={{
                  background: 'var(--surface-card)',
                  borderRadius: 'var(--radius-cards)',
                  border: '1px solid var(--color-chalk)',
                  padding: '28px',
                }}
              >
                <h2
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '15px',
                    fontWeight: 600,
                    marginBottom: '20px',
                  }}
                >
                  Shipping Address
                </h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <Input
                    label="Full Name"
                    name="name"
                    placeholder="John Doe"
                    value={form.name}
                    onChange={(e) => update('name', e.target.value)}
                    error={errors.name}
                  />
                  <Input
                    label="Address"
                    name="address"
                    placeholder="123 Main Street"
                    value={form.address}
                    onChange={(e) => update('address', e.target.value)}
                    error={errors.address}
                  />
                  <Input
                    label="City"
                    name="city"
                    placeholder="New York"
                    value={form.city}
                    onChange={(e) => update('city', e.target.value)}
                    error={errors.city}
                  />
                  <Input
                    label="Phone"
                    name="phone"
                    type="tel"
                    placeholder="+1 234 567 8900"
                    value={form.phone}
                    onChange={(e) => update('phone', e.target.value)}
                    error={errors.phone}
                  />
                </div>
              </section>

              {/* Payment */}
              <section
                style={{
                  background: 'var(--surface-card)',
                  borderRadius: 'var(--radius-cards)',
                  border: '1px solid var(--color-chalk)',
                  padding: '28px',
                }}
              >
                <h2
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '15px',
                    fontWeight: 600,
                    marginBottom: '20px',
                  }}
                >
                  Payment Method
                </h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {[
                    { value: 'cod', label: 'Cash on Delivery' },
                    { value: 'bank_transfer', label: 'Bank Transfer' },
                  ].map((opt) => (
                    <label
                      key={opt.value}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '14px 16px',
                        border: `1px solid ${form.payment_method === opt.value ? 'var(--color-obsidian)' : 'var(--color-chalk)'}`,
                        borderRadius: '8px',
                        cursor: 'pointer',
                        transition: 'border-color 0.15s',
                      }}
                    >
                      <input
                        type="radio"
                        name="payment_method"
                        value={opt.value}
                        checked={form.payment_method === opt.value}
                        onChange={() => update('payment_method', opt.value)}
                      />
                      <span style={{ fontFamily: 'var(--font-body)', fontSize: '14px', fontWeight: 500 }}>
                        {opt.label}
                      </span>
                    </label>
                  ))}
                </div>
              </section>
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
                  fontSize: '15px',
                  fontWeight: 600,
                  marginBottom: '20px',
                }}
              >
                Order Summary
              </h2>

              {cart?.items.map((item) => (
                <div
                  key={item.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '12px',
                    paddingBottom: '12px',
                    borderBottom: '1px solid var(--color-chalk)',
                  }}
                >
                  <div>
                    <p style={{ fontSize: '13px', fontWeight: 500 }}>{item.product_name}</p>
                    <p style={{ fontSize: '12px', color: 'var(--color-gravel)' }}>Qty: {item.quantity}</p>
                  </div>
                  <p style={{ fontSize: '13px', fontWeight: 500 }}>
                    {Number(item.subtotal).toLocaleString('vi-VN')} ₫
                  </p>
                </div>
              ))}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '13px', color: 'var(--color-gravel)' }}>Subtotal</span>
                  <span style={{ fontSize: '13px' }}>{subtotal.toLocaleString('vi-VN')} ₫</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '13px', color: 'var(--color-gravel)' }}>Shipping</span>
                  <span style={{ fontSize: '13px' }}>{shipping === 0 ? 'Free' : `${shipping.toLocaleString('vi-VN')} ₫`}</span>
                </div>
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
                <span style={{ fontSize: '18px', fontWeight: 600 }}>{total.toLocaleString('vi-VN')} ₫</span>
              </div>

              {serverError && (
                <p style={{ color: 'var(--color-ember)', fontSize: '13px', marginBottom: '16px' }}>
                  {serverError}
                </p>
              )}

              <Button
                variant="filled"
                type="submit"
                disabled={submitting}
                style={{ width: '100%' }}
              >
                {submitting ? 'Placing Order...' : 'Place Order'}
              </Button>
            </div>
          </div>
        </form>
      </div>

      <style>{`
        @media (max-width: 768px) {
          form > div { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}
