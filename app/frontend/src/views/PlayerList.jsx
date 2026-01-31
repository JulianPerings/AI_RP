import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getPlayers } from '../api'

const LLM_PROVIDERS = ['openai', 'xai', 'gemini', 'kimi', 'claude']

function getProviderLabel(provider) {
  if (provider === 'xai') return 'Grok'
  if (provider === 'openai') return 'OpenAI'
  if (provider === 'gemini') return 'Gemini'
  if (provider === 'kimi') return 'Kimi'
  if (provider === 'claude') return 'Claude'
  return provider
}

function PlayerList() {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [llmProvider, setLlmProvider] = useState('openai')
  const navigate = useNavigate()

  useEffect(() => {
    const stored = window.localStorage.getItem('llm_provider')
    if (LLM_PROVIDERS.includes(stored)) {
      setLlmProvider(stored)
    }
    loadPlayers()
  }, [])

  async function loadPlayers() {
    try {
      setLoading(true)
      const data = await getPlayers()
      setPlayers(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handlePlayerClick(player) {
    navigate(`/chat/${player.id}`)
  }

  function cycleProvider() {
    const idx = LLM_PROVIDERS.indexOf(llmProvider)
    const next = LLM_PROVIDERS[(idx + 1) % LLM_PROVIDERS.length]
    setLlmProvider(next)
    window.localStorage.setItem('llm_provider', next)
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p className="loading-text">Loading adventurers...</p>
      </div>
    )
  }

  return (
    <div>
      <header className="header" style={{ position: 'relative' }}>
        <div style={{ position: 'absolute', top: '0.5rem', right: 0 }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={cycleProvider}
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.85rem', whiteSpace: 'nowrap' }}
          >
            LLM: {getProviderLabel(llmProvider)}
          </button>
        </div>
        <h1>⚔️ AI Game Master ⚔️</h1>
        <p>Choose your adventurer or create a new hero</p>
      </header>

      {error && (
        <div className="card" style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }}>
          Error: {error}
        </div>
      )}

      <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
        <Link to="/create" className="btn btn-primary">
          ✨ Create New Character
        </Link>
      </div>

      {players.length === 0 ? (
        <div className="empty-state">
          <h3>No Adventurers Yet</h3>
          <p>Create your first character to begin your journey!</p>
        </div>
      ) : (
        <div className="player-grid">
          {players.map(player => (
            <div 
              key={player.id} 
              className="card card-clickable player-card"
              onClick={() => handlePlayerClick(player)}
            >
              <div className="level-badge">{player.level}</div>
              <h3>{player.name}</h3>
              <p className="class">{player.character_class || 'Adventurer'}</p>
              {player.description && (
                <p style={{ 
                  marginTop: '0.75rem', 
                  fontSize: '0.9rem',
                  color: 'var(--text-secondary)',
                  fontStyle: 'italic'
                }}>
                  "{player.description.substring(0, 100)}{player.description.length > 100 ? '...' : ''}"
                </p>
              )}
              <div className="stats">
                <span className="stat stat-health">❤️ {player.health}/{player.max_health}</span>
                <span className="stat stat-gold">💰 {player.gold}</span>
                <span className="stat stat-exp">✨ {player.experience} XP</span>
              </div>
              {player.story_messages && player.story_messages.length > 0 && (
                <p style={{ 
                  marginTop: '0.75rem', 
                  fontSize: '0.75rem',
                  color: 'var(--success)'
                }}>
                  📖 {player.story_messages.length} story messages
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default PlayerList
