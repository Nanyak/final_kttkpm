import type { InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, id, className = '', style, ...props }: InputProps) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
      {label && (
        <label
          htmlFor={inputId}
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '13px',
            fontWeight: 500,
            color: 'var(--color-obsidian)',
            letterSpacing: '0.1px',
          }}
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        style={{
          width: '100%',
          background: 'var(--surface-card)',
          border: error ? '1px solid var(--color-ember)' : '1px solid var(--color-chalk)',
          borderRadius: 'var(--radius-inputs)',
          padding: '12px 20px',
          fontFamily: 'var(--font-body)',
          fontSize: 'var(--text-body)',
          fontWeight: 400,
          color: 'var(--color-obsidian)',
          outline: 'none',
          transition: 'border-color 0.15s ease',
          boxShadow: 'var(--shadow-subtle)',
          ...style,
        }}
        className={className}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = 'var(--color-obsidian)'
          props.onFocus?.(e)
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = error ? 'var(--color-ember)' : 'var(--color-chalk)'
          props.onBlur?.(e)
        }}
        {...props}
      />
      {error && (
        <span
          style={{
            fontSize: '12px',
            color: 'var(--color-ember)',
            fontFamily: 'var(--font-body)',
          }}
        >
          {error}
        </span>
      )}
    </div>
  )
}
