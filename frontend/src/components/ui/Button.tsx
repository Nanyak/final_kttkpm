import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'filled' | 'ghost'
  size?: 'sm' | 'md'
  children: ReactNode
  className?: string
}

export function Button({
  variant = 'filled',
  size = 'md',
  children,
  className = '',
  disabled,
  style,
  ...props
}: ButtonProps) {
  const base: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 'var(--radius-buttons)',
    fontFamily: 'var(--font-body)',
    fontWeight: 500,
    fontSize: 'var(--text-body)',
    letterSpacing: '0.1px',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    transition: 'opacity 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease',
    whiteSpace: 'nowrap',
    textDecoration: 'none',
    outline: 'none',
  }

  const filled: React.CSSProperties = {
    background: 'var(--color-obsidian)',
    color: 'var(--color-eggshell)',
    border: '1px solid var(--color-obsidian)',
    boxShadow: 'var(--shadow-button)',
    padding: size === 'sm' ? '6px 14px' : '8px 18px',
  }

  const ghost: React.CSSProperties = {
    background: 'var(--surface-card)',
    color: 'var(--color-obsidian)',
    border: '1px solid var(--color-chalk)',
    boxShadow: 'var(--shadow-button)',
    padding: size === 'sm' ? '6px 12px' : '8px 14px',
  }

  const variantStyle = variant === 'filled' ? filled : ghost

  return (
    <button
      disabled={disabled}
      style={{ ...base, ...variantStyle, ...style }}
      className={className}
      {...props}
      onMouseEnter={(e) => {
        if (!disabled) {
          (e.currentTarget as HTMLButtonElement).style.opacity = '0.85'
        }
        props.onMouseEnter?.(e)
      }}
      onMouseLeave={(e) => {
        if (!disabled) {
          (e.currentTarget as HTMLButtonElement).style.opacity = '1'
        }
        props.onMouseLeave?.(e)
      }}
    >
      {children}
    </button>
  )
}
