import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { ProductCard } from '../components/ui/ProductCard'
import { productsAPI, aiAPI, aiResultToProduct } from '../lib/api'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import type { Product } from '../types'

export function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { addItem } = useCart()
  const { isAuthenticated } = useAuth()

  const [product, setProduct] = useState<Product | null>(null)
  const [related, setRelated] = useState<Product[]>([])
  const [aiRecommended, setAiRecommended] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [quantity, setQuantity] = useState(1)
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const { user } = useAuth()

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setAiRecommended([])
    productsAPI.detail(id).then((res) => {
      const p = res.data
      setProduct(p)

      // Fire-and-forget behavior tracking
      if (user) {
        aiAPI.trackBehavior({ user_id: user.id, product_id: p.id, action: 'view' }).catch(() => {})
      }

      // Fetch AI "You May Also Like" using product name as query
      aiAPI.recommend(user?.id ?? 0, p.name, 4).then((aiRes) => {
        const items = (aiRes.data.results ?? [])
          .filter((r) => r.product_id !== p.id)
          .slice(0, 3)
          .map(aiResultToProduct)
        setAiRecommended(items)
      }).catch(() => {})

      return productsAPI.list({ category_id: p.category })
    }).then((res) => {
      const list = Array.isArray(res.data) ? res.data : []
      setRelated(list.filter((p) => p.id !== Number(id)).slice(0, 3))
    }).catch(() => setError('Product not found')).finally(() => setLoading(false))
  }, [id, user])

  const handleAddToCart = async () => {
    if (!isAuthenticated) { navigate('/login'); return }
    if (!product) return
    try {
      setAdding(true)
      setError('')
      await addItem(product.id, quantity)
      setSuccess('Added to cart!')
      setTimeout(() => setSuccess(''), 3000)
    } catch {
      setError('Failed to add to cart.')
    } finally {
      setAdding(false)
    }
  }

  if (loading) {
    return (
      <div className="container" style={{ padding: '80px 0' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '48px' }}>
          <div className="skeleton" style={{ height: '480px', borderRadius: 'var(--radius-cards)' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="skeleton" style={{ height: '24px', width: '30%' }} />
            <div className="skeleton" style={{ height: '48px', width: '80%' }} />
            <div className="skeleton" style={{ height: '28px', width: '25%' }} />
            <div className="skeleton" style={{ height: '80px' }} />
          </div>
        </div>
      </div>
    )
  }

  if (!product) {
    return (
      <div
        className="container"
        style={{ padding: '80px 0', textAlign: 'center', color: 'var(--color-gravel)' }}
      >
        <p style={{ fontFamily: 'var(--font-headline)', fontSize: '28px', fontWeight: 300, marginBottom: '16px' }}>
          Product not found
        </p>
        <Button variant="ghost" onClick={() => navigate('/products')}>
          Back to Products
        </Button>
      </div>
    )
  }

  const imageUrl = product.image_url || `https://picsum.photos/seed/${product.id}/600/600`

  return (
    <div style={{ padding: '48px 0' }}>
      <div className="container">
        {/* Breadcrumb */}
        <nav style={{ marginBottom: '32px', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => navigate('/')}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-gravel)', fontSize: '13px', fontFamily: 'var(--font-body)' }}
          >
            Home
          </button>
          <span style={{ color: 'var(--color-slate)', fontSize: '13px' }}>/</span>
          <button
            onClick={() => navigate('/products')}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-gravel)', fontSize: '13px', fontFamily: 'var(--font-body)' }}
          >
            Products
          </button>
          <span style={{ color: 'var(--color-slate)', fontSize: '13px' }}>/</span>
          <span style={{ color: 'var(--color-obsidian)', fontSize: '13px', fontFamily: 'var(--font-body)' }}>
            {product.name}
          </span>
        </nav>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '64px', alignItems: 'start' }}>
          {/* Image */}
          <div
            style={{
              background: 'var(--surface-card)',
              borderRadius: 'var(--radius-cards)',
              boxShadow: 'var(--shadow-card)',
              overflow: 'hidden',
            }}
          >
            <img
              src={imageUrl}
              alt={product.name}
              style={{ width: '100%', aspectRatio: '1 / 1', objectFit: 'cover', display: 'block' }}
            />
          </div>

          {/* Details */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <Badge color="default">Product</Badge>
            </div>

            <h1
              style={{
                fontFamily: 'var(--font-headline)',
                fontWeight: 300,
                fontSize: 'var(--text-heading-lg)',
                letterSpacing: 'var(--tracking-heading-lg)',
                lineHeight: 1.15,
                color: 'var(--color-obsidian)',
              }}
            >
              {product.name}
            </h1>

            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '22px',
                fontWeight: 500,
                color: 'var(--color-obsidian)',
              }}
            >
              {Number(product.base_price).toLocaleString('vi-VN')} ₫
            </p>

            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: 'var(--text-body-lg)',
                fontWeight: 400,
                color: 'var(--color-gravel)',
                lineHeight: 1.6,
              }}
            >
              {product.description}
            </p>

            <p
              style={{
                fontSize: '13px',
                color: product.stock_quantity > 0 ? 'var(--color-success)' : 'var(--color-ember)',
                fontFamily: 'var(--font-body)',
                fontWeight: 500,
              }}
            >
              {product.stock_quantity > 0 ? `In stock (${product.stock_quantity} available)` : 'Out of stock'}
            </p>

            {/* Quantity Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '13px', color: 'var(--color-gravel)', fontFamily: 'var(--font-body)' }}>
                Quantity
              </span>
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
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  style={{
                    width: '36px',
                    height: '36px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '18px',
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
                    width: '40px',
                    textAlign: 'center',
                    fontFamily: 'var(--font-body)',
                    fontSize: '14px',
                    fontWeight: 500,
                    borderLeft: '1px solid var(--color-chalk)',
                    borderRight: '1px solid var(--color-chalk)',
                    lineHeight: '36px',
                    height: '36px',
                  }}
                >
                  {quantity}
                </span>
                <button
                  onClick={() => setQuantity(Math.min(product.stock_quantity, quantity + 1))}
                  style={{
                    width: '36px',
                    height: '36px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '18px',
                    color: 'var(--color-obsidian)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  +
                </button>
              </div>
            </div>

            {error && (
              <p style={{ color: 'var(--color-ember)', fontSize: '13px', fontFamily: 'var(--font-body)' }}>
                {error}
              </p>
            )}
            {success && (
              <p style={{ color: 'var(--color-success)', fontSize: '13px', fontFamily: 'var(--font-body)' }}>
                {success}
              </p>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <Button
                variant="filled"
                disabled={adding || product.stock_quantity === 0}
                onClick={handleAddToCart}
              >
                {adding ? 'Adding...' : 'Add to Cart'}
              </Button>
              <Button
                variant="ghost"
                disabled={product.stock_quantity === 0}
                onClick={async () => {
                  await handleAddToCart()
                  navigate('/cart')
                }}
              >
                Buy Now
              </Button>
            </div>
          </div>
        </div>

        {/* Related Products */}
        {related.length > 0 && (
          <section style={{ marginTop: '80px' }}>
            <h2
              style={{
                fontFamily: 'var(--font-headline)',
                fontWeight: 300,
                fontSize: 'var(--text-heading)',
                letterSpacing: 'var(--tracking-heading)',
                marginBottom: '32px',
              }}
            >
              Related Products
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
              {related.map((p) => <ProductCard key={p.id} product={p} />)}
            </div>
          </section>
        )}

        {/* AI "You May Also Like" */}
        {aiRecommended.length > 0 && (
          <section style={{ marginTop: '80px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '32px' }}>
              <h2
                style={{
                  fontFamily: 'var(--font-headline)',
                  fontWeight: 300,
                  fontSize: 'var(--text-heading)',
                  letterSpacing: 'var(--tracking-heading)',
                }}
              >
                You May Also Like
              </h2>
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'var(--font-body)',
                  fontWeight: 600,
                  letterSpacing: '0.6px',
                  textTransform: 'uppercase',
                  color: 'var(--color-gravel)',
                  background: 'var(--color-powder)',
                  border: '1px solid var(--color-chalk)',
                  borderRadius: '20px',
                  padding: '3px 10px',
                }}
              >
                AI Picks
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
              {aiRecommended.map((p) => <ProductCard key={p.id} product={p} />)}
            </div>
          </section>
        )}
      </div>

      <style>{`
        @media (max-width: 768px) {
          .container > div { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}
