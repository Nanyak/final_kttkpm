import { useState, useEffect, useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ProductCard } from '../components/ui/ProductCard'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { categoriesAPI, productsAPI } from '../lib/api'
import type { Category, Product } from '../types'

type CategoryNode = Category & { children: CategoryNode[] }

const ROOT_CATEGORY_ORDER = ['Books', 'Fashion', 'Electronics', 'Home & Living', 'Sports & Outdoors']

function buildCategoryTree(categories: Category[]): CategoryNode[] {
  const byId = new Map<number, CategoryNode>()
  categories.forEach((category) => {
    byId.set(category.id, { ...category, children: [] })
  })

  const roots: CategoryNode[] = []
  byId.forEach((node) => {
    if (node.parent && byId.has(node.parent)) {
      byId.get(node.parent)?.children.push(node)
    } else {
      roots.push(node)
    }
  })

  const sortNodes = (nodes: CategoryNode[]) => {
    nodes.sort((a, b) => {
      const ai = ROOT_CATEGORY_ORDER.indexOf(a.name)
      const bi = ROOT_CATEGORY_ORDER.indexOf(b.name)
      if (ai !== -1 || bi !== -1) return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
      return a.name.localeCompare(b.name)
    })
    nodes.forEach((node) => sortNodes(node.children))
  }

  sortNodes(roots)
  return roots
}

export function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || '')
  const [expandedCategories, setExpandedCategories] = useState<Record<number, boolean>>({})

  useEffect(() => {
    categoriesAPI.list({ is_active: true }).then((res) => setCategories(res.data)).catch(() => {})
  }, [])

  const categoryTree = useMemo(() => buildCategoryTree(categories), [categories])
  const categoryById = useMemo(() => {
    const map = new Map<number, Category>()
    categories.forEach((category) => map.set(category.id, category))
    return map
  }, [categories])

  useEffect(() => {
    if (!categoryTree.length) return
    setExpandedCategories((current) => {
      const next = { ...current }
      categoryTree.forEach((category) => {
        if (next[category.id] === undefined) next[category.id] = true
      })
      return next
    })
  }, [categoryTree])

  const fetchProducts = useCallback(() => {
    setLoading(true)
    productsAPI.list({
      search: search || undefined,
      category_id: selectedCategory || undefined,
      is_active: true,
    }).then((res) => {
      const list: Product[] = Array.isArray(res.data) ? res.data : []
      setProducts(list)
      setTotal(list.length)
    }).catch(() => {
      setProducts([])
    }).finally(() => setLoading(false))
  }, [search, selectedCategory])

  useEffect(() => {
    fetchProducts()
  }, [fetchProducts])

  useEffect(() => {
    const params: Record<string, string> = {}
    if (search) params.search = search
    if (selectedCategory) params.category = selectedCategory
    setSearchParams(params)
  }, [search, selectedCategory, setSearchParams])

  const toggleCategory = (id: number) => {
    setExpandedCategories((current) => ({ ...current, [id]: !current[id] }))
  }

  const renderCategory = (category: CategoryNode, depth = 0) => {
    const hasChildren = category.children.length > 0
    const isExpanded = expandedCategories[category.id] ?? false
    const isSelected = selectedCategory === String(category.id)

    return (
      <div key={category.id}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '24px 1fr',
            alignItems: 'center',
            gap: '4px',
            paddingLeft: `${depth * 14}px`,
          }}
        >
          <button
            type="button"
            aria-label={hasChildren ? `${isExpanded ? 'Collapse' : 'Expand'} ${category.name}` : category.name}
            onClick={() => hasChildren && toggleCategory(category.id)}
            disabled={!hasChildren}
            style={{
              width: '24px',
              height: '24px',
              border: 'none',
              background: 'transparent',
              color: hasChildren ? 'var(--color-gravel)' : 'transparent',
              cursor: hasChildren ? 'pointer' : 'default',
              fontSize: '14px',
              lineHeight: 1,
            }}
          >
            {hasChildren ? (isExpanded ? '-' : '+') : '-'}
          </button>
          <button
            type="button"
            onClick={() => { setSelectedCategory(String(category.id)) }}
            style={{
              width: '100%',
              minHeight: '32px',
              border: 'none',
              borderRadius: '6px',
              background: isSelected ? 'var(--color-powder)' : 'transparent',
              color: isSelected ? 'var(--color-obsidian)' : 'var(--color-gravel)',
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
              fontSize: depth === 0 ? '14px' : '13px',
              fontWeight: isSelected || depth === 0 ? 600 : 400,
              textAlign: 'left',
              padding: '7px 8px',
            }}
          >
            {category.name}
          </button>
        </div>
        {hasChildren && isExpanded && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '2px' }}>
            {category.children.map((child) => renderCategory(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={{ minHeight: '80vh', padding: '48px 0' }}>
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
          All Products
        </h1>

        <div className="products-layout" style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '40px' }}>
          {/* Sidebar */}
          <aside>
            <div
              style={{
                background: 'var(--surface-card)',
                borderRadius: 'var(--radius-cards)',
                border: '1px solid var(--color-chalk)',
                padding: '24px',
                position: 'sticky',
                top: '80px',
              }}
            >
              <h3
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '13px',
                  fontWeight: 600,
                  letterSpacing: '0.7px',
                  textTransform: 'uppercase',
                  color: 'var(--color-gravel)',
                  marginBottom: '16px',
                }}
              >
                Search
              </h3>
              <Input
                placeholder="Search products…"
                value={search}
                onChange={(e) => { setSearch(e.target.value) }}
                label=""
              />

              <div style={{ height: '1px', background: 'var(--color-chalk)', margin: '24px 0' }} />

              <h3
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '13px',
                  fontWeight: 600,
                  letterSpacing: '0.7px',
                  textTransform: 'uppercase',
                  color: 'var(--color-gravel)',
                  marginBottom: '16px',
                }}
              >
                Category
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => { setSelectedCategory('') }}
                  style={{
                    width: '100%',
                    minHeight: '34px',
                    border: 'none',
                    borderRadius: '6px',
                    background: selectedCategory === '' ? 'var(--color-powder)' : 'transparent',
                    color: 'var(--color-obsidian)',
                    cursor: 'pointer',
                    fontFamily: 'var(--font-body)',
                    fontSize: '14px',
                    fontWeight: 600,
                    textAlign: 'left',
                    padding: '8px',
                  }}
                >
                  All Products
                </button>
                {categoryTree.map((cat) => renderCategory(cat))}
              </div>
              {selectedCategory && (
                <p style={{ color: 'var(--color-gravel)', fontSize: '12px', marginTop: '16px', lineHeight: 1.5 }}>
                  Showing {categoryById.get(Number(selectedCategory))?.name || 'selected category'} and its subcategories.
                </p>
              )}
            </div>
          </aside>

          {/* Main Grid */}
          <div>
            {loading ? (
              <div
                className="product-grid"
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '20px',
                }}
              >
                {Array.from({ length: 9 }).map((_, i) => (
                  <div
                    key={i}
                    className="skeleton"
                    style={{ height: '300px', borderRadius: 'var(--radius-cards)' }}
                  />
                ))}
              </div>
            ) : products.length === 0 ? (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '80px 0',
                  gap: '16px',
                  textAlign: 'center',
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
                  No products found
                </p>
                <p style={{ color: 'var(--color-slate)', fontSize: '14px' }}>
                  Try adjusting your filters or search query.
                </p>
                <Button
                  variant="ghost"
                  onClick={() => { setSearch(''); setSelectedCategory('') }}
                >
                  Clear filters
                </Button>
              </div>
            ) : (
              <>
                <p style={{ fontSize: '13px', color: 'var(--color-gravel)', marginBottom: '20px' }}>
                  {total} product{total !== 1 ? 's' : ''} found
                </p>
                <div
                  className="product-grid"
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: '20px',
                  }}
                >
                  {products.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>

              </>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .products-layout { grid-template-columns: 1fr !important; }
          .products-layout aside > div { position: static !important; }
          .product-grid { grid-template-columns: 1fr 1fr !important; }
        }
        @media (max-width: 480px) {
          .product-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}
