import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import { cartAPI } from '../lib/api'
import { useAuth } from './AuthContext'
import type { Cart } from '../types'

interface CartContextType {
  cart: Cart | null
  addItem: (product_id: number, quantity: number) => Promise<void>
  updateItem: (id: number, quantity: number) => Promise<void>
  removeItem: (id: number) => Promise<void>
  refreshCart: () => Promise<void>
  loading: boolean
}

const CartContext = createContext<CartContextType | null>(null)

export function CartProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(false)
  const { isAuthenticated } = useAuth()

  const refreshCart = useCallback(async () => {
    if (!isAuthenticated) return
    try {
      setLoading(true)
      const res = await cartAPI.get()
      setCart(res.data)
    } catch {
      setCart(null)
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated])

  // Silent refresh — updates cart state without triggering the loading skeleton
  const silentRefresh = useCallback(async () => {
    if (!isAuthenticated) return
    try {
      const res = await cartAPI.get()
      setCart(res.data)
    } catch {
      setCart(null)
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (isAuthenticated) {
      refreshCart()
    } else {
      setCart(null)
    }
  }, [isAuthenticated, refreshCart])

  const addItem = useCallback(async (product_id: number, quantity: number) => {
    await cartAPI.addItem(product_id, quantity)
    await silentRefresh()
  }, [silentRefresh])

  const updateItem = useCallback(async (id: number, quantity: number) => {
    // Optimistic update so the UI responds instantly
    setCart((prev) => {
      if (!prev) return prev
      const items = prev.items.map((it) =>
        it.id === id ? { ...it, quantity } : it
      )
      const total_items = items.reduce((sum, it) => sum + it.quantity, 0)
      return { ...prev, items, total_items }
    })
    await cartAPI.updateItem(id, quantity)
    await silentRefresh()
  }, [silentRefresh])

  const removeItem = useCallback(async (id: number) => {
    // Optimistic update
    setCart((prev) => {
      if (!prev) return prev
      const items = prev.items.filter((it) => it.id !== id)
      const total_items = items.reduce((sum, it) => sum + it.quantity, 0)
      return { ...prev, items, total_items }
    })
    await cartAPI.removeItem(id)
    await silentRefresh()
  }, [silentRefresh])

  return (
    <CartContext.Provider value={{ cart, addItem, updateItem, removeItem, refreshCart, loading }}>
      {children}
    </CartContext.Provider>
  )
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used within CartProvider')
  return ctx
}
