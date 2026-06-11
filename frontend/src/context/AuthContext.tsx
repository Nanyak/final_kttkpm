import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { authAPI } from '../lib/api'
import { getToken, setToken, removeToken, isAuthenticated, getCurrentUser, saveUser } from '../lib/auth'
import type { User } from '../types'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  register: (data: {
    username: string
    email: string
    password: string
    password_confirm: string
    first_name: string
    last_name: string
  }) => Promise<void>
  loading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    if (token && isAuthenticated()) {
      setUser(getCurrentUser())
    }
    setLoading(false)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const res = await authAPI.login(username, password)
    const { access, refresh, user } = res.data as { access: string; refresh: string; user: User }
    setToken(access, refresh)
    saveUser(user)
    setUser(user)
  }, [])

  const logout = useCallback(() => {
    removeToken()
    setUser(null)
  }, [])

  const register = useCallback(async (data: {
    username: string
    email: string
    password: string
    password_confirm: string
    first_name: string
    last_name: string
  }) => {
    await authAPI.register(data)
  }, [])

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      login,
      logout,
      register,
      loading,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
