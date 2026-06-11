import { Link } from 'react-router-dom'

export function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer
      style={{
        background: 'var(--color-eggshell)',
        borderTop: '1px solid var(--color-chalk)',
        padding: '48px 0',
      }}
    >
      <div
        className="container"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              background: 'var(--gradient-voice-spectrum)',
              flexShrink: 0,
            }}
          />
          <span
            style={{
              fontFamily: 'var(--font-headline)',
              fontWeight: 700,
              fontSize: '16px',
              color: 'var(--color-obsidian)',
            }}
          >
            ShopEase
          </span>
        </div>

        <nav style={{ display: 'flex', gap: '24px' }}>
          {[
            { to: '/', label: 'Home' },
            { to: '/products', label: 'Products' },
          ].map((link) => (
            <Link
              key={link.to}
              to={link.to}
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                fontWeight: 400,
                color: 'var(--color-gravel)',
                textDecoration: 'none',
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-obsidian)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-gravel)')}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '13px',
            fontWeight: 400,
            color: 'var(--color-gravel)',
          }}
        >
          &copy; {year} ShopEase. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
