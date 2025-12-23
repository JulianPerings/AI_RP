import { useState, useEffect, useRef } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { getPlayer, startSession, sendMessage, getChatHistory } from '../api'

const LOADING_MESSAGES = [
  "The Game Master is weaving your tale...",
  "Rolling the dice of fate...",
  "Consulting ancient scrolls...",
  "The quill scratches across parchment...",
  "Destiny unfolds before you...",
  "The threads of fate intertwine...",
  "Magic flows through the realm...",
  "Your story takes shape..."
]

function Chat() {
  const { playerId } = useParams()
  const [searchParams] = useSearchParams()
  const isNewCharacter = searchParams.get('new') === 'true'
  
  const [player, setPlayer] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState(LOADING_MESSAGES[0])
  const [error, setError] = useState(null)
  
  const messagesEndRef = useRef(null)
  const loadingIntervalRef = useRef(null)
  const initializedRef = useRef(false)

  useEffect(() => {
    // Prevent double initialization from React StrictMode
    if (initializedRef.current) return
    initializedRef.current = true
    
    initializeChat()
    return () => {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current)
      }
    }
  }, [playerId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (sending || loading) {
      let idx = 0
      loadingIntervalRef.current = setInterval(() => {
        idx = (idx + 1) % LOADING_MESSAGES.length
        setLoadingMessage(LOADING_MESSAGES[idx])
      }, 3000)
    } else {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current)
      }
    }
    return () => {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current)
      }
    }
  }, [sending, loading])

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  async function initializeChat() {
    try {
      setLoading(true)
      const playerData = await getPlayer(playerId)
      setPlayer(playerData)

      if (isNewCharacter || !playerData.current_session_id) {
        // New character - start a fresh session
        const session = await startSession(parseInt(playerId))
        setMessages([{
          role: 'gm',
          content: session.intro,
          toolCalls: session.tool_calls || []
        }])
      } else {
        // Existing character - load chat history
        try {
          const history = await getChatHistory(playerData.current_session_id)
          const formatted = history.messages.map(msg => ({
            role: msg.role === 'human' ? 'player' : 'gm',
            content: msg.content,
            toolCalls: msg.tool_calls || []
          }))
          setMessages(formatted)
        } catch (err) {
          // No history yet, start new session
          const session = await startSession(parseInt(playerId))
          setMessages([{
            role: 'gm',
            content: session.intro,
            toolCalls: session.tool_calls || []
          }])
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSend(e) {
    e.preventDefault()
    if (!input.trim() || sending || !player) return

    const userMessage = input.trim()
    setInput('')
    setSending(true)

    // Add player message immediately
    setMessages(prev => [...prev, { role: 'player', content: userMessage }])

    try {
      const response = await sendMessage(
        parseInt(playerId),
        player.current_session_id,
        userMessage
      )
      
      // Add GM response
      setMessages(prev => [...prev, {
        role: 'gm',
        content: response.response,
        toolCalls: response.tool_calls || []
      }])
      
      // Refresh player stats (health, gold may have changed)
      const updatedPlayer = await getPlayer(playerId)
      setPlayer(updatedPlayer)
    } catch (err) {
      setError(err.message)
      // Remove the player message on error
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setSending(false)
    }
  }

  if (loading) {
    return (
      <div>
        <Link to="/" className="nav-back">← Back to Characters</Link>
        <div className="loading-container" style={{ minHeight: '60vh' }}>
          <div className="loading-quill">🪶</div>
          <div className="loading-spinner"></div>
          <p className="loading-text">{loadingMessage}</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <Link to="/" className="nav-back">← Back to Characters</Link>
        <div className="card" style={{ borderColor: 'var(--accent)', textAlign: 'center' }}>
          <h3 style={{ color: 'var(--accent)' }}>Something went wrong</h3>
          <p>{error}</p>
          <button className="btn btn-secondary" onClick={() => window.location.reload()} style={{ marginTop: '1rem' }}>
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <Link to="/" className="nav-back" style={{ margin: 0 }}>← Exit</Link>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ color: 'var(--gold)', fontSize: '1.3rem', fontFamily: 'Cinzel, serif', fontWeight: 600 }}>{player?.name}</span>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            {player?.character_class || 'Adventurer'} • Lvl {player?.level}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginLeft: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: '#60a5fa' }}>XP</span>
            <div style={{ 
              width: '80px', 
              height: '8px', 
              background: 'rgba(255,255,255,0.1)', 
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{ 
                width: `${player?.experience || 0}%`, 
                height: '100%', 
                background: 'linear-gradient(90deg, #60a5fa, #a78bfa)',
                borderRadius: '4px',
                transition: 'width 0.3s ease'
              }} />
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{player?.experience || 0}/100</span>
          </div>
        </div>
        <div style={{ textAlign: 'right', fontSize: '0.95rem' }}>
          <span className="stat stat-health">❤️ {player?.health}/{player?.max_health}</span>
          <span className="stat stat-gold" style={{ marginLeft: '1rem' }}>💰 {player?.gold}</span>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role === 'gm' ? 'gm' : 'player'}`}>
            <div className="message-label">
              {msg.role === 'gm' ? '📖 Game Master' : '⚔️ You'}
            </div>
            <div className="message-content">{msg.content}</div>
            {msg.toolCalls && msg.toolCalls.length > 0 && (
              <div className="tool-calls">
                {msg.toolCalls.map((tc, i) => (
                  <span key={i} className="tool-call">
                    🔧 {tc.tool}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        
        {sending && (
          <div className="message message-gm">
            <div className="message-label">📖 Game Master</div>
            <div className="loading-container" style={{ padding: '1rem 0' }}>
              <div className="loading-quill">🪶</div>
              <p className="loading-text">{loadingMessage}</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={sending ? "The Game Master is responding..." : "What do you do?"}
          disabled={sending}
          autoFocus
        />
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={sending || !input.trim()}
        >
          {sending ? '...' : 'Send'}
        </button>
      </form>
    </div>
  )
}

export default Chat
