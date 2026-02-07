import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getPlayers, getAvailableProviders } from '../api'

function PlayerList() {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showSettings, setShowSettings] = useState(false)

  // Provider / model / thinking state (mirrors localStorage)
  const [providers, setProviders] = useState([])
  const [defaultProvider, setDefaultProvider] = useState(null)
  const [selectedProvider, setSelectedProvider] = useState(null)
  const [selectedModel, setSelectedModel] = useState(null)
  const [thinkingEnabled, setThinkingEnabled] = useState(false)
  const [ttsAvailable, setTtsAvailable] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(false)

  const navigate = useNavigate()

  useEffect(() => {
    loadProviders()
    loadPlayers()
  }, [])

  async function loadProviders() {
    try {
      const data = await getAvailableProviders()
      setProviders(data.providers || [])
      setDefaultProvider(data.default || null)
      setTtsAvailable(!!data.tts_available)

      // Restore from localStorage
      const storedProv = localStorage.getItem('llm_provider')
      const storedModel = localStorage.getItem('llm_model')
      const storedThinking = localStorage.getItem('llm_thinking')
      const storedTts = localStorage.getItem('tts_enabled')

      if (storedProv && (data.providers || []).some(p => p.id === storedProv)) {
        setSelectedProvider(storedProv)
        setSelectedModel(storedModel || null)
        setThinkingEnabled(storedThinking === 'true')
      }
      if (storedTts === 'true' && data.tts_available) {
        setTtsEnabled(true)
      }
    } catch {
      console.warn('Could not fetch LLM providers')
    }
  }

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

  // ---- Settings helpers ----

  function selectModel(providerId, modelId) {
    const prov = providers.find(p => p.id === providerId)
    const model = prov?.models?.find(m => m.id === modelId)

    setSelectedProvider(providerId)
    setSelectedModel(modelId)
    localStorage.setItem('llm_provider', providerId)
    localStorage.setItem('llm_model', modelId)

    // Auto-enable thinking for capable models, off for others
    if (model?.thinking) {
      setThinkingEnabled(true)
      localStorage.setItem('llm_thinking', 'true')
    } else {
      setThinkingEnabled(false)
      localStorage.setItem('llm_thinking', 'false')
    }
  }

  function toggleThinking() {
    const next = !thinkingEnabled
    setThinkingEnabled(next)
    localStorage.setItem('llm_thinking', String(next))
  }

  function toggleTts() {
    const next = !ttsEnabled
    setTtsEnabled(next)
    localStorage.setItem('tts_enabled', String(next))
  }

  // Derive the currently active provider + model label for the gear badge
  function getActiveLabel() {
    const prov = providers.find(p => p.id === (selectedProvider || defaultProvider))
    if (!prov) return null
    const model = prov.models?.find(m => m.id === selectedModel)
    return model ? model.label : prov.label
  }

  // Whether the currently selected model supports thinking
  function currentModelSupportsThinking() {
    const prov = providers.find(p => p.id === selectedProvider)
    const model = prov?.models?.find(m => m.id === selectedModel)
    return !!model?.thinking
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
            className="btn-gear"
            onClick={() => setShowSettings(true)}
            title="LLM Settings"
          >
            <span className="gear-icon">⚙</span>
            {getActiveLabel() && (
              <span className="gear-label">{getActiveLabel()}</span>
            )}
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

      {/* ---- Settings Modal ---- */}
      {showSettings && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <div className="modal-content settings-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>⚙ LLM Settings</h2>
              <button className="modal-close" onClick={() => setShowSettings(false)}>×</button>
            </div>
            <div className="modal-body">
              {providers.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)' }}>No providers configured.</p>
              ) : (
                providers.map(prov => (
                  <div key={prov.id} className="settings-provider">
                    <h3 className="settings-provider-label">{prov.label}</h3>
                    <div className="settings-model-list">
                      {prov.models.map(m => {
                        const isActive = selectedProvider === prov.id && selectedModel === m.id
                        return (
                          <button
                            key={m.id}
                            type="button"
                            className={`settings-model-btn ${isActive ? 'active' : ''}`}
                            onClick={() => selectModel(prov.id, m.id)}
                          >
                            <span className="model-name">{m.label}</span>
                            {m.thinking && (
                              <span className="model-thinking-badge" title="Supports thinking mode">
                                🧠
                              </span>
                            )}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                ))
              )}

              {/* Thinking toggle — only show when active model supports it */}
              {currentModelSupportsThinking() && (
                <div className="settings-thinking-row">
                  <span className="settings-thinking-label">🧠 Thinking mode</span>
                  <button
                    type="button"
                    className={`toggle-btn ${thinkingEnabled ? 'on' : 'off'}`}
                    onClick={toggleThinking}
                  >
                    <span className="toggle-thumb" />
                  </button>
                  <span className="settings-thinking-hint">
                    {thinkingEnabled ? 'On (low effort)' : 'Off'}
                  </span>
                </div>
              )}

              {/* TTS toggle — only show when Gemini API key is configured */}
              {ttsAvailable && (
                <div className="settings-thinking-row">
                  <span className="settings-thinking-label">🔊 Text-to-Speech</span>
                  <button
                    type="button"
                    className={`toggle-btn ${ttsEnabled ? 'on' : 'off'}`}
                    onClick={toggleTts}
                  >
                    <span className="toggle-thumb" />
                  </button>
                  <span className="settings-thinking-hint">
                    {ttsEnabled ? 'On (Gemini TTS)' : 'Off'}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PlayerList
