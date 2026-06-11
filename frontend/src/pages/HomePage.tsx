import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { ProductCard } from '../components/ui/ProductCard'
import { categoriesAPI, productsAPI, aiAPI } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import type { Category, Product } from '../types'

export function HomePage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [categories, setCategories] = useState<Category[]>([])
  const [featured, setFeatured] = useState<Product[]>([])
  const [heroProduct, setHeroProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [recommendations, setRecommendations] = useState<Product[]>([])
  const [recsLoading, setRecsLoading] = useState(false)

  useEffect(() => {
    Promise.all([
      categoriesAPI.list({ parent_id: 0, is_active: true }),
      productsAPI.list({ is_active: true }),
    ]).then(([catRes, prodRes]) => {
      setCategories(catRes.data.slice(0, 8))
      const products: Product[] = Array.isArray(prodRes.data) ? prodRes.data : []
      setFeatured(products.slice(0, 3))
      setHeroProduct(products[0] || null)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!user) return
    setRecsLoading(true)
    aiAPI.recommend(user.id, undefined, 6).then((res) => {
      const aiItems = res.data.results ?? []
      const ids = Array.from(new Set(aiItems.map((item) => item.product_id))).filter(Boolean)
      if (ids.length === 0) {
        setRecommendations([])
        return
      }

      return productsAPI.list({ ids: ids.join(','), is_active: true }).then((prodRes) => {
        const productsById = new Map((Array.isArray(prodRes.data) ? prodRes.data : []).map((product) => [product.id, product]))
        const items = aiItems
          .map((item) => productsById.get(item.product_id))
          .filter((product): product is Product => Boolean(product))
        setRecommendations(items)
      })
    }).catch(() => {}).finally(() => setRecsLoading(false))
  }, [user])

  return (
    <main>
      {/* Hero */}
      <section
        style={{
          padding: '120px 0 80px',
          background: 'var(--color-eggshell)',
        }}
      >
        <div
          className="container"
          style={{
            display: 'grid',
            gridTemplateColumns: '55% 45%',
            gap: '48px',
            alignItems: 'center',
          }}
        >
          <div>
            <h1
              style={{
                fontFamily: 'var(--font-headline)',
                fontWeight: 300,
                fontSize: 'clamp(36px, 4vw, 48px)',
                lineHeight: 1.08,
                letterSpacing: '-0.96px',
                color: 'var(--color-obsidian)',
                marginBottom: '16px',
              }}
            >
              Discover Products<br />You'll Love
            </h1>
            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: 'var(--text-body-lg)',
                fontWeight: 400,
                color: 'var(--color-gravel)',
                lineHeight: 1.6,
                marginBottom: '32px',
                maxWidth: '480px',
              }}
            >
              Explore our curated selection of quality products, delivered straight to your door with care.
            </p>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <Button variant="filled" onClick={() => navigate('/products')}>
                Shop Now
              </Button>
              <Button variant="ghost" onClick={() => {
                document.getElementById('categories')?.scrollIntoView({ behavior: 'smooth' })
              }}>
                Browse Categories
              </Button>
            </div>
          </div>

          {/* Hero Product Card */}
          <div>
            {heroProduct && !loading ? (
              <div
                style={{
                  background: 'var(--surface-card)',
                  borderRadius: 'var(--radius-cards)',
                  boxShadow: 'var(--shadow-card)',
                  overflow: 'hidden',
                  cursor: 'pointer',
                }}
                onClick={() => navigate(`/products/${heroProduct.id}`)}
              >
                <img
                  src={heroProduct.image_url || `https://picsum.photos/seed/${heroProduct.id}/600/400`}
                  alt={heroProduct.name}
                  style={{ width: '100%', height: '280px', objectFit: 'cover' }}
                />
                <div style={{ padding: '20px 24px' }}>
                  <h3
                    style={{
                      fontFamily: 'var(--font-body)',
                      fontSize: '16px',
                      fontWeight: 500,
                      marginBottom: '6px',
                    }}
                  >
                    {heroProduct.name}
                  </h3>
                  <p style={{ color: 'var(--color-gravel)', fontSize: '14px' }}>
                    {Number(heroProduct.base_price).toLocaleString('vi-VN')} ₫
                  </p>
                </div>
              </div>
            ) : (
              <div
                className="skeleton"
                style={{ height: '360px', borderRadius: 'var(--radius-cards)' }}
              />
            )}
          </div>
        </div>

        <style>{`
          @media (max-width: 768px) {
            section > .container { grid-template-columns: 1fr !important; }
            section > .container > div:last-child { display: none; }
          }
        `}</style>
      </section>

      {/* Category Band */}
      <section id="categories" style={{ padding: '80px 0', background: 'var(--color-eggshell)' }}>
        <div className="container">
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: 'var(--text-body)',
              fontWeight: 400,
              color: 'var(--color-gravel)',
              marginBottom: '8px',
            }}
          >
            Explore
          </p>
          <h2
            style={{
              fontFamily: 'var(--font-headline)',
              fontWeight: 300,
              fontSize: 'var(--text-heading-lg)',
              letterSpacing: 'var(--tracking-heading-lg)',
              color: 'var(--color-obsidian)',
              marginBottom: '32px',
            }}
          >
            Browse by Category
          </h2>
          <div
            style={{
              display: 'flex',
              gap: '12px',
              overflowX: 'auto',
              paddingBottom: '8px',
              scrollbarWidth: 'none',
            }}
          >
            {loading
              ? Array.from({ length: 6 }).map((_, i) => (
                  <div
                    key={i}
                    className="skeleton"
                    style={{ minWidth: '140px', height: '80px', borderRadius: 'var(--radius-cards)', flexShrink: 0 }}
                  />
                ))
              : categories.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => navigate(`/products?category=${cat.id}`)}
                    style={{
                      minWidth: '140px',
                      padding: '20px 20px',
                      background: 'var(--surface-card)',
                      border: '1px solid var(--color-chalk)',
                      borderRadius: 'var(--radius-cards)',
                      cursor: 'pointer',
                      fontFamily: 'var(--font-body)',
                      fontSize: 'var(--text-body)',
                      fontWeight: 500,
                      color: 'var(--color-obsidian)',
                      textAlign: 'center',
                      transition: 'background 0.15s, border-color 0.15s',
                      flexShrink: 0,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'var(--color-powder)'
                      e.currentTarget.style.borderColor = 'var(--color-gravel)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'var(--surface-card)'
                      e.currentTarget.style.borderColor = 'var(--color-chalk)'
                    }}
                  >
                    {cat.name}
                  </button>
                ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section style={{ padding: '80px 0', background: 'var(--color-eggshell)' }}>
        <div className="container">
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: 'var(--text-body)',
              fontWeight: 400,
              color: 'var(--color-gravel)',
              marginBottom: '8px',
            }}
          >
            Featured
          </p>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '32px',
            }}
          >
            <h2
              style={{
                fontFamily: 'var(--font-headline)',
                fontWeight: 300,
                fontSize: 'var(--text-heading-lg)',
                letterSpacing: 'var(--tracking-heading-lg)',
                color: 'var(--color-obsidian)',
              }}
            >
              Popular Products
            </h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/products')}>
              View all
            </Button>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '20px',
            }}
          >
            {loading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className="skeleton"
                    style={{ height: '320px', borderRadius: 'var(--radius-cards)' }}
                  />
                ))
              : featured.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
          </div>
        </div>
        <style>{`
          @media (max-width: 768px) {
            section .products-grid { grid-template-columns: 1fr 1fr !important; }
          }
          @media (max-width: 480px) {
            section .products-grid { grid-template-columns: 1fr !important; }
          }
        `}</style>
      </section>

      {/* Recommended for You — only shown for logged-in users with results */}
      {(recsLoading || recommendations.length > 0) && (
        <section style={{ padding: '80px 0', background: 'var(--color-eggshell)' }}>
          <div className="container">
            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: 'var(--text-body)',
                fontWeight: 400,
                color: 'var(--color-gravel)',
                marginBottom: '8px',
              }}
            >
              Personalised
            </p>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '32px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h2
                  style={{
                    fontFamily: 'var(--font-headline)',
                    fontWeight: 300,
                    fontSize: 'var(--text-heading-lg)',
                    letterSpacing: 'var(--tracking-heading-lg)',
                    color: 'var(--color-obsidian)',
                  }}
                >
                  Recommended for You
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
              <Button variant="ghost" size="sm" onClick={() => navigate('/products')}>
                View all
              </Button>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '20px',
              }}
            >
              {recsLoading
                ? Array.from({ length: 3 }).map((_, i) => (
                    <div
                      key={i}
                      className="skeleton"
                      style={{ height: '320px', borderRadius: 'var(--radius-cards)' }}
                    />
                  ))
                : recommendations.slice(0, 6).map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
            </div>
          </div>
        </section>
      )}

      {/* Social Proof */}
      <section style={{ padding: '80px 0', background: 'var(--color-powder)' }}>
        <div className="container" style={{ textAlign: 'center' }}>
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: 'var(--text-body)',
              color: 'var(--color-gravel)',
              marginBottom: '8px',
            }}
          >
            Trusted by thousands
          </p>
          <h2
            style={{
              fontFamily: 'var(--font-headline)',
              fontWeight: 300,
              fontSize: 'var(--text-heading-lg)',
              letterSpacing: 'var(--tracking-heading-lg)',
              color: 'var(--color-obsidian)',
              marginBottom: '48px',
            }}
          >
            Why Choose ShopEase
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '32px',
            }}
          >
            {[
              { stat: '10k+', label: 'Products available' },
              { stat: '50k+', label: 'Happy customers' },
              { stat: '99%', label: 'Satisfaction rate' },
              { stat: '24h', label: 'Support response' },
            ].map((item) => (
              <div key={item.stat}>
                <p
                  style={{
                    fontFamily: 'var(--font-headline)',
                    fontWeight: 300,
                    fontSize: '40px',
                    letterSpacing: '-0.8px',
                    color: 'var(--color-obsidian)',
                    marginBottom: '8px',
                  }}
                >
                  {item.stat}
                </p>
                <p
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: 'var(--text-body)',
                    color: 'var(--color-gravel)',
                  }}
                >
                  {item.label}
                </p>
              </div>
            ))}
          </div>
        </div>
        <style>{`
          @media (max-width: 640px) {
            section > .container > div:last-child { grid-template-columns: 1fr 1fr !important; }
          }
        `}</style>
      </section>
    </main>
  )
}
