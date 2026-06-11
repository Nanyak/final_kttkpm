import axios from 'axios'
import { getToken } from './auth'
import type { Category, Product, Cart, Order, User } from '../types'

export interface AIRecommendResult {
  product_id: number
  final_score: number
  sequence_model_score?: number
  lstm_score?: number
  name: string
  category: string
  price: number
  description: string
}

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Unwrap backend envelope: { status, data } → data
api.interceptors.response.use(
  (response) => {
    if (
      response.data &&
      typeof response.data === 'object' &&
      'status' in response.data &&
      'data' in response.data
    ) {
      response.data = response.data.data
    }
    return response
  },
  (error) => {
    if (error.response?.data && typeof error.response.data === 'object' && 'data' in error.response.data) {
      error.response.data = error.response.data.data
    }
    return Promise.reject(error)
  }
)

// Auth
export const authAPI = {
  login: (username: string, password: string) =>
    api.post<{ access: string; refresh: string; user: import('../types').User }>('/auth/login/', { username, password }),

  register: (data: {
    username: string
    email: string
    password: string
    password_confirm: string
    first_name: string
    last_name: string
  }) => api.post('/auth/register/', data),
}

// Categories
export const categoriesAPI = {
  list: (params?: { parent_id?: number | string; is_active?: boolean }) =>
    api.get<Category[]>('/categories/', { params }),
}

// Products
export const productsAPI = {
  list: (params?: { category_id?: number | string; search?: string; ids?: string; is_active?: boolean }) =>
    api.get<Product[]>('/products/', { params }),

  detail: (id: number | string) => api.get<Product>(`/products/${id}/`),

  create: (data: ProductPayload) => api.post<Product>('/products/', data),

  update: (id: number | string, data: Partial<ProductPayload>) => api.patch<Product>(`/products/${id}/`, data),

  delete: (id: number | string) => api.delete(`/products/${id}/`),
}

// Cart
export const cartAPI = {
  get: () => api.get<Cart>('/carts/me/'),

  addItem: (product_id: number, quantity: number) =>
    api.post('/carts/me/items/', { product_id, quantity }),

  updateItem: (itemId: number, quantity: number) =>
    api.patch(`/carts/me/items/${itemId}/`, { quantity }),

  removeItem: (itemId: number) => api.delete(`/carts/me/items/${itemId}/`),
}

// Orders
export const ordersAPI = {
  list: () => api.get<Order[]>('/orders/'),

  adminList: () => api.get<Order[]>('/orders/admin/'),

  create: (data: { shipping_address: Record<string, string>; payment_method: string }) =>
    api.post<Order>('/orders/', data),

  detail: (id: number | string) => api.get<Order>(`/orders/${id}/`),

  update: (id: number | string, data: Partial<Pick<Order, 'status' | 'payment_status' | 'notes'>>) =>
    api.patch<Order>(`/orders/${id}/`, data),
}

export interface ProductPayload {
  name: string
  description: string
  base_price: string
  stock_quantity: number
  category: number
  is_active: boolean
  image_url?: string | null
}

export const usersAPI = {
  adminList: () => api.get<User[]>('/users/'),

  adminDetail: (id: number | string) => api.get<User>(`/users/${id}/`),

  update: (id: number | string, data: Partial<Pick<User, 'first_name' | 'last_name' | 'email' | 'phone_number' | 'is_active' | 'role' | 'role_name'>>) =>
    api.patch<User>(`/users/${id}/`, data),

  delete: (id: number | string) => api.delete(`/users/${id}/`),
}

// AI Service
export const aiAPI = {
  recommend: (userId: number, query?: string, topN = 6) =>
    api.get<{ user_id: number; count: number; results: AIRecommendResult[] }>('/ai/recommend/', {
      params: { user_id: userId, ...(query ? { query } : {}), top_n: topN },
    }),

  chatbot: (data: {
    query: string
    user_id?: number
    history?: Array<{ role: string; content: string }>
  }) =>
    api.post<{
      query: string
      answer: string
      context_used: string[]
      recommended: AIRecommendResult[]
    }>('/ai/chatbot/', data),

  trackBehavior: (data: {
    user_id: number
    product_id: number
    action: 'view' | 'click' | 'add_to_cart' | 'purchase'
  }) => api.post<{ message: string; behavior_id: number }>('/ai/track/', data),
}

export function aiResultToProduct(r: AIRecommendResult): Product {
  return {
    id: r.product_id,
    name: r.name,
    slug: r.name.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
    description: r.description,
    base_price: String(r.price),
    stock_quantity: 1,
    is_active: true,
    category: 0,
    category_name: r.category,
    image_url: null,
  }
}

export default api
