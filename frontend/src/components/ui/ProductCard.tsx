import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from './Button'
import { useCart } from '../../context/CartContext'
import { useAuth } from '../../context/AuthContext'
import type { Product } from '../../types'

interface ProductCardProps {
  product: Product
}

export function ProductCard({ product }: ProductCardProps) {
  const navigate = useNavigate()
  const { addItem } = useCart()
  const { isAuthenticated } = useAuth()
  const [adding, setAdding] = useState(false)

  const imageUrl = product.image_url || `https://picsum.photos/seed/${product.id}/400/300`

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    try {
      setAdding(true)
      await addItem(product.id, 1)
    } catch (err) {
      console.error('Failed to add to cart', err)
    } finally {
      setAdding(false)
    }
  }

  return (
    <div
      onClick={() => navigate(`/products/${product.id}`)}
      style={{
        background: 'var(--surface-card)',
        borderRadius: 'var(--radius-cards)',
        boxShadow: 'var(--shadow-card)',
        overflow: 'hidden',
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)'
        e.currentTarget.style.boxShadow = 'rgba(0,0,0,0.4) 0px 0px 1.143px 0px, rgba(0,0,0,0.08) 0px 6px 12px 0px'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = 'var(--shadow-card)'
      }}
    >
      <div style={{ position: 'relative', paddingTop: '75%', overflow: 'hidden' }}>
        <img
          src={imageUrl}
          alt={product.name}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).src = `https://picsum.photos/seed/${product.id}/400/300`
          }}
        />
      </div>

      <div
        style={{
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          flex: 1,
        }}
      >
        <h3
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            fontWeight: 500,
            color: 'var(--color-obsidian)',
            lineHeight: 1.3,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {product.name}
        </h3>

        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: 'var(--text-body)',
            fontWeight: 400,
            color: 'var(--color-gravel)',
          }}
        >
          {Number(product.base_price).toLocaleString('vi-VN')} ₫
        </p>

        <div style={{ marginTop: 'auto', paddingTop: '8px' }}>
          <Button
            variant="filled"
            size="sm"
            onClick={handleAddToCart}
            disabled={adding || product.stock_quantity === 0}
            style={{ width: '100%' }}
          >
            {product.stock_quantity === 0 ? 'Out of Stock' : adding ? 'Adding...' : 'Add to Cart'}
          </Button>
        </div>
      </div>
    </div>
  )
}
