import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getPlayers } from '../api'

function PlayerList() {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
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
      <header className="header">
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
