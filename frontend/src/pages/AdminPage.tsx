import { useCallback, useEffect, useMemo, useState, type CSSProperties, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { useAuth } from '../context/AuthContext'
import { categoriesAPI, ordersAPI, productsAPI, usersAPI, type ProductPayload } from '../lib/api'
import type { Category, Order, Product, User } from '../types'

type AdminTab = 'products' | 'orders' | 'users'

const emptyProductForm: ProductPayload = {
  name: '',
  description: '',
  base_price: '',
  stock_quantity: 0,
  category: 0,
  is_active: true,
  image_url: '',
}

const tableShell: CSSProperties = {
  background: 'var(--surface-card)',
  border: '1px solid var(--color-chalk)',
  borderRadius: '8px',
  overflowX: 'auto',
}

const thStyle: CSSProperties = {
  padding: '12px 14px',
  textAlign: 'left',
  fontSize: '12px',
  fontWeight: 700,
  color: 'var(--color-gravel)',
  textTransform: 'uppercase',
  letterSpacing: '0.7px',
  whiteSpace: 'nowrap',
  borderBottom: '1px solid var(--color-chalk)',
}

const tdStyle: CSSProperties = {
  padding: '12px 14px',
  borderBottom: '1px solid var(--color-chalk)',
  verticalAlign: 'middle',
  fontSize: '13px',
}

const selectStyle: CSSProperties = {
  minHeight: '34px',
  border: '1px solid var(--color-chalk)',
  background: 'var(--surface-card)',
  color: 'var(--color-obsidian)',
  padding: '6px 10px',
  fontSize: '13px',
  boxShadow: 'var(--shadow-subtle)',
}

function isAdmin(user: User | null) {
  return user?.role === 'admin' || user?.role_name === 'admin'
}

function statusColor(status: string): 'default' | 'blue' | 'ember' | 'success' {
  switch (status.toLowerCase()) {
    case 'confirmed':
    case 'processing':
    case 'shipped':
    case 'paid':
      return 'blue'
    case 'delivered':
    case 'completed':
      return 'success'
    case 'cancelled':
    case 'failed':
    case 'refunded':
      return 'ember'
    default:
      return 'default'
  }
}

function formatMoney(value: string | number | undefined) {
  return Number(value || 0).toLocaleString('vi-VN') + ' ₫'
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString()
}

export function AdminPage() {
  const { user, loading: authLoading } = useAuth()
  const [activeTab, setActiveTab] = useState<AdminTab>('products')
  const [products, setProducts] = useState<Product[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [productForm, setProductForm] = useState<ProductPayload>(emptyProductForm)
  const [productSearch, setProductSearch] = useState('')

  const loadAdminData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [productRes, orderRes, userRes, categoryRes] = await Promise.all([
        productsAPI.list(),
        ordersAPI.adminList(),
        usersAPI.adminList(),
        categoriesAPI.list(),
      ])
      setProducts(Array.isArray(productRes.data) ? productRes.data : [])
      setOrders(Array.isArray(orderRes.data) ? orderRes.data : [])
      setUsers(Array.isArray(userRes.data) ? userRes.data : [])
      setCategories(Array.isArray(categoryRes.data) ? categoryRes.data : [])
    } catch {
      setError('Failed to load admin data.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!authLoading && isAdmin(user)) {
      const timeout = window.setTimeout(() => {
        loadAdminData()
      }, 0)
      return () => window.clearTimeout(timeout)
    }
  }, [authLoading, loadAdminData, user])

  const visibleProducts = useMemo(() => {
    const needle = productSearch.trim().toLowerCase()
    if (!needle) return products
    return products.filter((product) =>
      [product.name, product.category_name, product.description].some((value) =>
        value?.toLowerCase().includes(needle)
      )
    )
  }, [productSearch, products])

  if (authLoading) {
    return <div style={{ minHeight: '70vh' }} />
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: '/admin' }} replace />
  }

  if (!isAdmin(user)) {
    return <Navigate to="/" replace />
  }

  const resetProductForm = () => {
    setEditingProduct(null)
    setProductForm(emptyProductForm)
  }

  const editProduct = (product: Product) => {
    setEditingProduct(product)
    setProductForm({
      name: product.name,
      description: product.description || '',
      base_price: String(product.base_price),
      stock_quantity: product.stock_quantity,
      category: product.category,
      is_active: product.is_active,
      image_url: product.image_url || '',
    })
  }

  const submitProduct = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    setMessage('')
    try {
      const payload = {
        ...productForm,
        category: Number(productForm.category),
        stock_quantity: Number(productForm.stock_quantity),
        image_url: productForm.image_url || null,
      }
      if (editingProduct) {
        const res = await productsAPI.update(editingProduct.id, payload)
        setProducts((current) => current.map((product) => product.id === editingProduct.id ? res.data : product))
        setMessage('Product updated.')
      } else {
        const res = await productsAPI.create(payload)
        setProducts((current) => [res.data, ...current])
        setMessage('Product created.')
      }
      resetProductForm()
    } catch {
      setError('Could not save product.')
    } finally {
      setSaving(false)
    }
  }

  const deleteProduct = async (product: Product) => {
    if (!window.confirm(`Delete ${product.name}?`)) return
    setSaving(true)
    setError('')
    try {
      await productsAPI.delete(product.id)
      setProducts((current) => current.filter((item) => item.id !== product.id))
      if (editingProduct?.id === product.id) resetProductForm()
      setMessage('Product deleted.')
    } catch {
      setError('Could not delete product.')
    } finally {
      setSaving(false)
    }
  }

  const updateOrder = async (order: Order, field: 'status' | 'payment_status', value: string) => {
    setSaving(true)
    setError('')
    try {
      const res = await ordersAPI.update(order.id, { [field]: value })
      setOrders((current) => current.map((item) => item.id === order.id ? res.data : item))
      setMessage('Order updated.')
    } catch {
      setError('Could not update order.')
    } finally {
      setSaving(false)
    }
  }

  const updateUser = async (target: User, patch: Partial<User>) => {
    setSaving(true)
    setError('')
    try {
      const res = await usersAPI.update(target.id, patch)
      setUsers((current) => current.map((item) => item.id === target.id ? res.data : item))
      setMessage('User updated.')
    } catch {
      setError('Could not update user.')
    } finally {
      setSaving(false)
    }
  }

  const deleteUser = async (target: User) => {
    if (!window.confirm(`Delete ${target.username}?`)) return
    setSaving(true)
    setError('')
    try {
      await usersAPI.delete(target.id)
      setUsers((current) => current.filter((item) => item.id !== target.id))
      setMessage('User deleted.')
    } catch {
      setError('Could not delete user.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ minHeight: '80vh', padding: '40px 0' }}>
      <div className="container">
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            gap: '16px',
            marginBottom: '24px',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <h1
              style={{
                fontSize: 'var(--text-heading)',
                letterSpacing: 'var(--tracking-heading)',
                marginBottom: '6px',
              }}
            >
              Admin
            </h1>
            <p style={{ color: 'var(--color-gravel)', fontSize: '14px' }}>
              Manage catalog, orders, and customer accounts.
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={loadAdminData} disabled={loading || saving}>
            Refresh
          </Button>
        </div>

        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
          {(['products', 'orders', 'users'] as AdminTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                minHeight: '36px',
                borderRadius: '999px',
                border: '1px solid var(--color-chalk)',
                background: activeTab === tab ? 'var(--color-obsidian)' : 'var(--surface-card)',
                color: activeTab === tab ? 'var(--color-eggshell)' : 'var(--color-obsidian)',
                padding: '8px 14px',
                fontSize: '13px',
                fontWeight: 600,
                textTransform: 'capitalize',
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        {(error || message) && (
          <div
            style={{
              marginBottom: '16px',
              padding: '12px 14px',
              border: `1px solid ${error ? 'var(--color-ember)' : 'var(--color-chalk)'}`,
              color: error ? 'var(--color-ember)' : 'var(--color-success)',
              background: 'var(--surface-card)',
              borderRadius: '8px',
              fontSize: '13px',
            }}
          >
            {error || message}
          </div>
        )}

        {loading ? (
          <div className="skeleton" style={{ height: '360px', borderRadius: '8px' }} />
        ) : activeTab === 'products' ? (
          <section className="admin-products-layout" style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '20px' }}>
            <form onSubmit={submitProduct} style={{ background: 'var(--surface-card)', border: '1px solid var(--color-chalk)', borderRadius: '8px', padding: '18px', alignSelf: 'start' }}>
              <h2 style={{ fontSize: '22px', marginBottom: '16px' }}>{editingProduct ? 'Edit Product' : 'New Product'}</h2>
              <div style={{ display: 'grid', gap: '12px' }}>
                <Input label="Name" value={productForm.name} required onChange={(e) => setProductForm((current) => ({ ...current, name: e.target.value }))} />
                <label style={{ display: 'grid', gap: '6px', fontSize: '13px', fontWeight: 500 }}>
                  Description
                  <textarea
                    value={productForm.description}
                    onChange={(e) => setProductForm((current) => ({ ...current, description: e.target.value }))}
                    rows={4}
                    style={{ border: '1px solid var(--color-chalk)', padding: '12px', resize: 'vertical', boxShadow: 'var(--shadow-subtle)' }}
                  />
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <Input label="Price" type="number" min="0" step="1000" value={productForm.base_price} required onChange={(e) => setProductForm((current) => ({ ...current, base_price: e.target.value }))} />
                  <Input label="Stock" type="number" min="0" value={productForm.stock_quantity} required onChange={(e) => setProductForm((current) => ({ ...current, stock_quantity: Number(e.target.value) }))} />
                </div>
                <label style={{ display: 'grid', gap: '6px', fontSize: '13px', fontWeight: 500 }}>
                  Category
                  <select required value={productForm.category || ''} onChange={(e) => setProductForm((current) => ({ ...current, category: Number(e.target.value) }))} style={selectStyle}>
                    <option value="">Select category</option>
                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>{category.name}</option>
                    ))}
                  </select>
                </label>
                <Input label="Image URL" value={productForm.image_url || ''} onChange={(e) => setProductForm((current) => ({ ...current, image_url: e.target.value }))} />
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
                  <input type="checkbox" checked={productForm.is_active} onChange={(e) => setProductForm((current) => ({ ...current, is_active: e.target.checked }))} />
                  Active
                </label>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <Button type="submit" disabled={saving}>{editingProduct ? 'Save Product' : 'Create Product'}</Button>
                  {editingProduct && <Button type="button" variant="ghost" onClick={resetProductForm}>Cancel</Button>}
                </div>
              </div>
            </form>

            <div>
              <div style={{ marginBottom: '12px', maxWidth: '360px' }}>
                <Input label="" placeholder="Search products" value={productSearch} onChange={(e) => setProductSearch(e.target.value)} />
              </div>
              <div style={tableShell}>
                <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '760px' }}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Product</th>
                      <th style={thStyle}>Category</th>
                      <th style={thStyle}>Price</th>
                      <th style={thStyle}>Stock</th>
                      <th style={thStyle}>State</th>
                      <th style={thStyle}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleProducts.map((product) => (
                      <tr key={product.id}>
                        <td style={tdStyle}>
                          <strong>{product.name}</strong>
                          <div style={{ color: 'var(--color-gravel)', marginTop: '4px', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{product.description}</div>
                        </td>
                        <td style={tdStyle}>{product.category_name}</td>
                        <td style={tdStyle}>{formatMoney(product.base_price)}</td>
                        <td style={tdStyle}>{product.stock_quantity}</td>
                        <td style={tdStyle}><Badge color={product.is_active ? 'success' : 'default'}>{product.is_active ? 'Active' : 'Hidden'}</Badge></td>
                        <td style={tdStyle}>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <Button size="sm" variant="ghost" onClick={() => editProduct(product)}>Edit</Button>
                            <Button size="sm" variant="ghost" onClick={() => deleteProduct(product)} disabled={saving}>Delete</Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        ) : activeTab === 'orders' ? (
          <div style={tableShell}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '900px' }}>
              <thead>
                <tr>
                  <th style={thStyle}>Order</th>
                  <th style={thStyle}>User</th>
                  <th style={thStyle}>Total</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Payment</th>
                  <th style={thStyle}>Date</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td style={tdStyle}><span style={{ fontFamily: 'var(--font-mono)' }}>#{order.order_number}</span></td>
                    <td style={tdStyle}>{order.user_id || '-'}</td>
                    <td style={tdStyle}>{formatMoney(order.total_amount)}</td>
                    <td style={tdStyle}>
                      <select value={order.status} onChange={(e) => updateOrder(order, 'status', e.target.value)} style={selectStyle} disabled={saving}>
                        {['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'].map((status) => <option key={status} value={status}>{status}</option>)}
                      </select>
                    </td>
                    <td style={tdStyle}>
                      <select value={order.payment_status} onChange={(e) => updateOrder(order, 'payment_status', e.target.value)} style={selectStyle} disabled={saving}>
                        {['pending', 'paid', 'failed', 'refunded'].map((status) => <option key={status} value={status}>{status}</option>)}
                      </select>
                      <span style={{ marginLeft: '8px' }}><Badge color={statusColor(order.payment_status)}>{order.payment_status}</Badge></span>
                    </td>
                    <td style={tdStyle}>{formatDate(order.ordered_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={tableShell}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '920px' }}>
              <thead>
                <tr>
                  <th style={thStyle}>User</th>
                  <th style={thStyle}>Contact</th>
                  <th style={thStyle}>Role</th>
                  <th style={thStyle}>State</th>
                  <th style={thStyle}>Joined</th>
                  <th style={thStyle}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((target) => (
                  <tr key={target.id}>
                    <td style={tdStyle}>
                      <strong>{target.username}</strong>
                      <div style={{ color: 'var(--color-gravel)', marginTop: '4px' }}>{[target.first_name, target.last_name].filter(Boolean).join(' ') || '-'}</div>
                    </td>
                    <td style={tdStyle}>
                      <div>{target.email}</div>
                      <div style={{ color: 'var(--color-gravel)', marginTop: '4px' }}>{target.phone_number || '-'}</div>
                    </td>
                    <td style={tdStyle}>
                      <select value={target.role_name || target.role} onChange={(e) => updateUser(target, { role_name: e.target.value })} style={selectStyle} disabled={saving}>
                        <option value="customer">customer</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                    <td style={tdStyle}>
                      <select value={target.is_active === false ? 'inactive' : 'active'} onChange={(e) => updateUser(target, { is_active: e.target.value === 'active' })} style={selectStyle} disabled={saving}>
                        <option value="active">active</option>
                        <option value="inactive">inactive</option>
                      </select>
                    </td>
                    <td style={tdStyle}>{formatDate(target.created_at)}</td>
                    <td style={tdStyle}>
                      <Button size="sm" variant="ghost" onClick={() => deleteUser(target)} disabled={saving || target.id === user.id}>Delete</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <style>{`
        @media (max-width: 900px) {
          .admin-products-layout {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  )
}
