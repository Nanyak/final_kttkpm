import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'
import { Button } from '../ui/Button'

export function Navbar() {
  const { isAuthenticated, user, logout } = useAuth()
  const { cart } = useCart()
  const navigate = useNavigate()
  const location = useLocation()
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    setMenuOpen(false)
  }, [location.pathname])

  const itemCount = cart?.total_items || 0

  const navLinks = [
    { to: '/', label: 'Home' },
    { to: '/products', label: 'Products' },
  ]
  const isAdmin = user?.role === 'admin' || user?.role_name === 'admin'
  const visibleNavLinks = isAdmin ? [...navLinks, { to: '/admin', label: 'Admin' }] : navLinks

  return (
    <nav
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        background: 'var(--color-eggshell)',
        borderBottom: scrolled ? '1px solid var(--color-chalk)' : '1px solid transparent',
        transition: 'border-color 0.2s ease',
      }}
    >
      <div
        className="container"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '60px',
        }}
      >
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'var(--gradient-voice-spectrum)',
              animation: 'spin 4s linear infinite',
              flexShrink: 0,
            }}
          />
          <span
            style={{
              fontFamily: 'var(--font-headline)',
              fontWeight: 700,
              fontSize: '18px',
              color: 'var(--color-obsidian)',
              letterSpacing: '-0.02em',
            }}
          >
            ShopEase
          </span>
        </Link>

        {/* Desktop Nav Links */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '28px',
          }}
          className="nav-links-desktop"
        >
          {visibleNavLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: 'var(--text-body)',
                fontWeight: 400,
                color: location.pathname === link.to ? 'var(--color-obsidian)' : 'var(--color-gravel)',
                textDecoration: 'none',
                transition: 'color 0.15s ease',
              }}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Right side */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Cart Icon */}
          <button
            onClick={() => navigate('/cart')}
            style={{
              position: 'relative',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            aria-label="Cart"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <path d="M16 10a4 4 0 0 1-8 0" />
            </svg>
            {itemCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: '-4px',
                  right: '-4px',
                  background: 'var(--color-obsidian)',
                  color: 'var(--color-eggshell)',
                  borderRadius: '50%',
                  width: '16px',
                  height: '16px',
                  fontSize: '10px',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: 'var(--font-body)',
                }}
              >
                {itemCount > 9 ? '9+' : itemCount}
              </span>
            )}
          </button>

          {isAuthenticated ? (
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                style={{
                  background: 'none',
                  border: '1px solid var(--color-chalk)',
                  borderRadius: 'var(--radius-full)',
                  padding: '6px 14px',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-body)',
                  fontSize: 'var(--text-body)',
                  fontWeight: 500,
                  color: 'var(--color-obsidian)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                {user?.first_name || user?.username || 'Account'}
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>

              {userMenuOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: 'calc(100% + 8px)',
                    right: 0,
                    background: 'var(--surface-card)',
                    border: '1px solid var(--color-chalk)',
                    borderRadius: '12px',
                    boxShadow: 'var(--shadow-card)',
                    padding: '8px',
                    minWidth: '160px',
                    zIndex: 200,
                  }}
                >
                  <Link
                    to="/orders"
                    onClick={() => setUserMenuOpen(false)}
                    style={{
                      display: 'block',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      fontSize: 'var(--text-body)',
                      color: 'var(--color-obsidian)',
                      fontFamily: 'var(--font-body)',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-powder)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    My Orders
                  </Link>
                  {isAdmin && (
                    <Link
                      to="/admin"
                      onClick={() => setUserMenuOpen(false)}
                      style={{
                        display: 'block',
                        padding: '8px 12px',
                        borderRadius: '8px',
                        fontSize: 'var(--text-body)',
                        color: 'var(--color-obsidian)',
                        fontFamily: 'var(--font-body)',
                        transition: 'background 0.15s',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-powder)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      Admin
                    </Link>
                  )}
                  <button
                    onClick={() => { logout(); setUserMenuOpen(false) }}
                    style={{
                      display: 'block',
                      width: '100%',
                      textAlign: 'left',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      fontSize: 'var(--text-body)',
                      color: 'var(--color-gravel)',
                      fontFamily: 'var(--font-body)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-powder)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
                Log in
              </Button>
              <Button variant="filled" size="sm" onClick={() => navigate('/register')}>
                Sign up
              </Button>
            </>
          )}

          {/* Hamburger */}
          <button
            className="hamburger"
            onClick={() => setMenuOpen(!menuOpen)}
            style={{
              display: 'none',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px',
              color: 'var(--color-obsidian)',
            }}
            aria-label="Menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {menuOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </>
              ) : (
                <>
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </>
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {menuOpen && (
        <div
          style={{
            borderTop: '1px solid var(--color-chalk)',
            padding: '16px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            background: 'var(--color-eggshell)',
          }}
        >
          {visibleNavLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '15px',
                fontWeight: 400,
                color: 'var(--color-obsidian)',
              }}
            >
              {link.label}
            </Link>
          ))}
          {!isAuthenticated && (
            <div style={{ display: 'flex', gap: '12px' }}>
              <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>Log in</Button>
              <Button variant="filled" size="sm" onClick={() => navigate('/register')}>Sign up</Button>
            </div>
          )}
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .nav-links-desktop { display: none !important; }
          .hamburger { display: flex !important; }
        }
      `}</style>
    </nav>
  )
}
