import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()
  const [form, setForm] = useState({ username: '', password: '' })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState('')

  const from = (location.state as { from?: string })?.from || '/'

  const update = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: '' }))
  }

  const validate = () => {
    const newErrors: Record<string, string> = {}
    if (!form.username.trim()) newErrors.username = 'Username is required'
    if (!form.password) newErrors.password = 'Password is required'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    setServerError('')
    try {
      await login(form.username, form.password)
      navigate(from, { replace: true })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { message?: string; detail?: string } } }
      setServerError(
        axiosErr.response?.data?.message ||
        axiosErr.response?.data?.detail ||
        'Invalid username or password.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '80vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '400px',
          background: 'var(--surface-card)',
          borderRadius: 'var(--radius-cards)',
          boxShadow: 'var(--shadow-card)',
          padding: '40px 36px',
        }}
      >
        <h1
          style={{
            fontFamily: 'var(--font-headline)',
            fontWeight: 300,
            fontSize: '32px',
            letterSpacing: '-0.64px',
            color: 'var(--color-obsidian)',
            marginBottom: '8px',
          }}
        >
          Welcome back
        </h1>
        <p
          style={{
            fontSize: '14px',
            color: 'var(--color-gravel)',
            marginBottom: '32px',
            fontFamily: 'var(--font-body)',
          }}
        >
          Sign in to your ShopEase account
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <Input
            label="Username"
            type="text"
            name="username"
            placeholder="johndoe"
            value={form.username}
            onChange={(e) => update('username', e.target.value)}
            error={errors.username}
            autoComplete="username"
          />
          <Input
            label="Password"
            type="password"
            name="password"
            placeholder="••••••••"
            value={form.password}
            onChange={(e) => update('password', e.target.value)}
            error={errors.password}
            autoComplete="current-password"
          />

          {serverError && (
            <p
              style={{
                fontSize: '13px',
                color: 'var(--color-ember)',
                fontFamily: 'var(--font-body)',
              }}
            >
              {serverError}
            </p>
          )}

          <Button variant="filled" type="submit" disabled={loading} style={{ width: '100%', marginTop: '4px' }}>
            {loading ? 'Signing in...' : 'Log in'}
          </Button>
        </form>

        <p
          style={{
            marginTop: '24px',
            textAlign: 'center',
            fontSize: '14px',
            color: 'var(--color-gravel)',
            fontFamily: 'var(--font-body)',
          }}
        >
          Don't have an account?{' '}
          <Link
            to="/register"
            style={{
              color: 'var(--color-obsidian)',
              fontWeight: 500,
              textDecoration: 'underline',
            }}
          >
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}
