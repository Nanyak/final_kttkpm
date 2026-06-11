import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { aiAPI } from '../../lib/api'
import { useAuth } from '../../context/AuthContext'

interface Message {
  role: 'user' | 'assistant'
  content: string
  recommended?: { product_id: number; name: string; price: number; category: string }[]
}

export function ChatbotWidget() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      inputRef.current?.focus()
    }
  }, [open, messages])

  const sendMessage = async () => {
    const query = input.trim()
    if (!query || loading) return

    const userMsg: Message = { role: 'user', content: query }
    const history = messages.map((m) => ({ role: m.role, content: m.content }))
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await aiAPI.chatbot({
        query,
        user_id: user?.id,
        history,
      })
      const { answer, recommended } = res.data
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: answer,
          recommended: (recommended ?? []).slice(0, 3),
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: "Sorry, I couldn't process your question right now. Please try again.",
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen((v) => !v)}
        title="Ask about products"
        style={{
          position: 'fixed',
          bottom: '28px',
          right: '28px',
          width: '52px',
          height: '52px',
          borderRadius: '50%',
          background: 'var(--color-obsidian)',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 16px rgba(0,0,0,0.22)',
          zIndex: 1000,
          transition: 'transform 0.15s, box-shadow 0.15s',
          color: '#fff',
          fontSize: '22px',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.08)'
          e.currentTarget.style.boxShadow = '0 6px 24px rgba(0,0,0,0.3)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)'
          e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.22)'
        }}
      >
        {open ? '✕' : '✦'}
      </button>

      {/* Chat panel */}
      {open && (
        <div
          style={{
            position: 'fixed',
            bottom: '92px',
            right: '28px',
            width: '360px',
            maxHeight: '520px',
            background: 'var(--surface-card)',
            borderRadius: 'var(--radius-cards)',
            boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            border: '1px solid var(--color-chalk)',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '16px 20px',
              borderBottom: '1px solid var(--color-chalk)',
              background: 'var(--color-eggshell)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <span style={{ fontSize: '16px' }}>✦</span>
            <div>
              <p
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '14px',
                  fontWeight: 600,
                  color: 'var(--color-obsidian)',
                  marginBottom: '1px',
                }}
              >
                Ask about products
              </p>
              <p style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--color-gravel)' }}>
                Powered by AI · semantic search
              </p>
            </div>
          </div>

          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '24px 0' }}>
                <p
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '13px',
                    color: 'var(--color-gravel)',
                    lineHeight: 1.6,
                  }}
                >
                  Ask me anything about our products — features, recommendations, comparisons, and more.
                </p>
                <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {['Best headphones under 1 triệu?', 'Laptop for students?', 'Warm jacket for winter?'].map((hint) => (
                    <button
                      key={hint}
                      onClick={() => setInput(hint)}
                      style={{
                        background: 'var(--color-powder)',
                        border: '1px solid var(--color-chalk)',
                        borderRadius: 'var(--radius-lg)',
                        padding: '7px 14px',
                        fontSize: '12px',
                        fontFamily: 'var(--font-body)',
                        color: 'var(--color-obsidian)',
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      {hint}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <div
                    style={{
                      maxWidth: '85%',
                      padding: '10px 14px',
                      borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                      background: msg.role === 'user' ? 'var(--color-obsidian)' : 'var(--color-powder)',
                      color: msg.role === 'user' ? '#fff' : 'var(--color-obsidian)',
                      fontFamily: 'var(--font-body)',
                      fontSize: '13px',
                      lineHeight: 1.55,
                    }}
                  >
                    {msg.content}
                  </div>
                </div>

                {/* Recommended products from chatbot */}
                {msg.recommended && msg.recommended.length > 0 && (
                  <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {msg.recommended.map((r) => (
                      <button
                        key={r.product_id}
                        onClick={() => { navigate(`/products/${r.product_id}`); setOpen(false) }}
                        style={{
                          background: 'var(--surface-card)',
                          border: '1px solid var(--color-chalk)',
                          borderRadius: 'var(--radius-lg)',
                          padding: '10px 14px',
                          textAlign: 'left',
                          cursor: 'pointer',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          gap: '8px',
                        }}
                      >
                        <div>
                          <p style={{ fontFamily: 'var(--font-body)', fontSize: '13px', fontWeight: 500, color: 'var(--color-obsidian)', marginBottom: '2px' }}>
                            {r.name}
                          </p>
                          <p style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--color-gravel)' }}>
                            {Number(r.price).toLocaleString('vi-VN')} ₫
                          </p>
                        </div>
                        <span style={{ fontSize: '14px', color: 'var(--color-gravel)', flexShrink: 0 }}>→</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div
                  style={{
                    padding: '10px 16px',
                    borderRadius: '16px 16px 16px 4px',
                    background: 'var(--color-powder)',
                    display: 'flex',
                    gap: '4px',
                    alignItems: 'center',
                  }}
                >
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        background: 'var(--color-gravel)',
                        display: 'inline-block',
                        animation: `chatDot 1.2s ${i * 0.2}s ease-in-out infinite`,
                      }}
                    />
                  ))}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div
            style={{
              padding: '12px 16px',
              borderTop: '1px solid var(--color-chalk)',
              display: 'flex',
              gap: '8px',
              alignItems: 'center',
            }}
          >
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about products…"
              disabled={loading}
              style={{
                flex: 1,
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                padding: '9px 14px',
                border: '1px solid var(--color-chalk)',
                borderRadius: 'var(--radius-lg)',
                background: 'var(--color-eggshell)',
                color: 'var(--color-obsidian)',
                outline: 'none',
              }}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: input.trim() && !loading ? 'var(--color-obsidian)' : 'var(--color-chalk)',
                border: 'none',
                cursor: input.trim() && !loading ? 'pointer' : 'default',
                color: '#fff',
                fontSize: '15px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'background 0.15s',
              }}
            >
              ↑
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes chatDot {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </>
  )
}
