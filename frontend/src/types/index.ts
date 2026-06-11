export interface Category {
  id: number
  name: string
  slug: string
  description?: string
  parent?: number | null
  is_active?: boolean
}

export interface Product {
  id: number
  name: string
  slug: string
  description: string
  base_price: string
  stock_quantity: number
  is_active: boolean
  category: number
  category_name: string
  image_url?: string | null
}

export interface CartItem {
  id: number
  product_id: number
  product_name: string
  unit_price: string
  quantity: number
  subtotal: string
}

export interface Cart {
  id: number
  items: CartItem[]
  total_amount: number
  total_items: number
}

export interface Order {
  id: number
  order_number: string
  status: string
  total_amount: string
  payment_status: string
  ordered_at: string
  items?: OrderItem[]
  shipping_address?: Record<string, string>
  payment_method?: string
}

export interface OrderItem {
  id: number
  product_id: number
  product_name: string
  product_sku?: string
  quantity: number
  unit_price: string
  discount_per_item?: string
}

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: number | string
  role_name?: string
}
