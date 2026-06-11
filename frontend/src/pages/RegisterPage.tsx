import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { useAuth } from '../context/AuthContext'

export function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    password: '',
    password_confirm: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState('')

  const update = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: '' }))
  }

  const validate = () => {
    const newErrors: Record<string, string> = {}
    if (!form.first_name.trim()) newErrors.first_name = 'First name is required'
    if (!form.last_name.trim()) newErrors.last_name = 'Last name is required'
    if (!form.username.trim()) newErrors.username = 'Username is required'
    if (!form.email.trim()) newErrors.email = 'Email is required'
    if (!form.password) newErrors.password = 'Password is required'
    if (form.password.length < 8) newErrors.password = 'Password must be at least 8 characters'
    if (form.password !== form.password_confirm) newErrors.password_confirm = 'Passwords do not match'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    setServerError('')
    try {
      await register(form)
      navigate('/login', { state: { registered: true } })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { message?: Record<string, string | string[]> } & Record<string, string | string[]> } }
      const data = axiosErr.response?.data
      // Backend field errors come in data.message (after envelope unwrap)
      const fieldSource = data?.message && typeof data.message === 'object' ? data.message : data
      if (fieldSource && typeof fieldSource === 'object') {
        const fieldErrors: Record<string, string> = {}
        for (const [key, value] of Object.entries(fieldSource)) {
          fieldErrors[key] = Array.isArray(value) ? value[0] : String(value)
        }
        if (Object.keys(fieldErrors).length > 0) {
          setErrors(fieldErrors)
          return
        }
      }
      setServerError('Registration failed. Please try again.')
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
          maxWidth: '420px',
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
          Create account
        </h1>
        <p
          style={{
            fontSize: '14px',
            color: 'var(--color-gravel)',
            marginBottom: '32px',
            fontFamily: 'var(--font-body)',
          }}
        >
          Join ShopEase to start shopping
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <Input
              label="First Name"
              name="first_name"
              placeholder="John"
              value={form.first_name}
              onChange={(e) => update('first_name', e.target.value)}
              error={errors.first_name}
            />
            <Input
              label="Last Name"
              name="last_name"
              placeholder="Doe"
              value={form.last_name}
              onChange={(e) => update('last_name', e.target.value)}
              error={errors.last_name}
            />
          </div>
          <Input
            label="Username"
            name="username"
            placeholder="johndoe"
            value={form.username}
            onChange={(e) => update('username', e.target.value)}
            error={errors.username}
            autoComplete="username"
          />
          <Input
            label="Email"
            type="email"
            name="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={(e) => update('email', e.target.value)}
            error={errors.email}
            autoComplete="email"
          />
          <Input
            label="Password"
            type="password"
            name="password"
            placeholder="••••••••"
            value={form.password}
            onChange={(e) => update('password', e.target.value)}
            error={errors.password}
            autoComplete="new-password"
          />
          <Input
            label="Confirm Password"
            type="password"
            name="password_confirm"
            placeholder="••••••••"
            value={form.password_confirm}
            onChange={(e) => update('password_confirm', e.target.value)}
            error={errors.password_confirm}
            autoComplete="new-password"
          />

          {serverError && (
            <p style={{ fontSize: '13px', color: 'var(--color-ember)', fontFamily: 'var(--font-body)' }}>
              {serverError}
            </p>
          )}

          <Button variant="filled" type="submit" disabled={loading} style={{ width: '100%', marginTop: '8px' }}>
            {loading ? 'Creating account...' : 'Create account'}
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
          Already have an account?{' '}
          <Link
            to="/login"
            style={{ color: 'var(--color-obsidian)', fontWeight: 500, textDecoration: 'underline' }}
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
