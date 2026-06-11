import type { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  color?: 'default' | 'blue' | 'ember' | 'success'
}

const colorMap: Record<string, { bg: string; text: string }> = {
  default: { bg: 'var(--color-chalk)', text: 'var(--color-obsidian)' },
  blue: { bg: 'var(--color-signal-blue)', text: '#ffffff' },
  ember: { bg: 'var(--color-ember)', text: '#ffffff' },
  success: { bg: '#2d6a4f', text: '#ffffff' },
}

export function Badge({ children, color = 'default' }: BadgeProps) {
  const { bg, text } = colorMap[color] || colorMap.default

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '4px 10px',
        borderRadius: 'var(--radius-full)',
        background: bg,
        color: text,
        fontSize: '12px',
        fontWeight: 500,
        fontFamily: 'var(--font-body)',
        letterSpacing: '0.1px',
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </span>
  )
}
