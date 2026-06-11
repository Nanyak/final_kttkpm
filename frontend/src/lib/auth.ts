import type { User } from '../types'

const TOKEN_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'
const USER_KEY = 'current_user'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(access: string, refresh?: string): void {
  localStorage.setItem(TOKEN_KEY, access)
  if (refresh) {
    localStorage.setItem(REFRESH_KEY, refresh)
  }
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
}

export function saveUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function loadUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

export function isAuthenticated(): boolean {
  const token = getToken()
  if (!token) return false
  try {
    const payload = parseJWT(token)
    if (!payload) return false
    const exp = payload.exp as number
    return exp * 1000 > Date.now()
  } catch {
    return false
  }
}

export function parseJWT(token: string): Record<string, unknown> | null {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch {
    return null
  }
}

export function getCurrentUser(): User | null {
  const stored = loadUser()
  if (stored) return stored

  // Fallback: reconstruct minimal user from JWT (username/first_name absent in JWT)
  const token = getToken()
  if (!token) return null
  const payload = parseJWT(token)
  if (!payload) return null
  return {
    id: payload.user_id as number,
    username: (payload.email as string) || '',
    email: (payload.email as string) || '',
    first_name: '',
    last_name: '',
    role: (payload.role as string) || 'customer',
  }
}
