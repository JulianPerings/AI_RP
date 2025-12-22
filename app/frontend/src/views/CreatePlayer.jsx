import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createPlayer, getLocations, getRaces } from '../api'

function CreatePlayer() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [locations, setLocations] = useState([])
  const [races, setRaces] = useState([])
  const [form, setForm] = useState({
    name: '',
    character_class: '',
    description: '',
    current_location_id: null,
    race_id: null,
    gold: 0,
    health: 100,
    max_health: 100
  })

  useEffect(() => {
    loadOptions()
  }, [])

  async function loadOptions() {
    try {
      const [locs, rcs] = await Promise.all([
        getLocations().catch(() => []),
        getRaces().catch(() => [])
      ])
      setLocations(locs)
      setRaces(rcs)
      if (locs.length > 0) {
        setForm(f => ({ ...f, current_location_id: locs[0].id }))
      }
    } catch (err) {
      console.error('Failed to load options:', err)
    }
  }

  function handleChange(e) {
    const { name, value } = e.target
    setForm(f => ({
      ...f,
      [name]: name.endsWith('_id') 
        ? (value ? parseInt(value) : null) 
        : ['gold', 'health', 'max_health'].includes(name)
          ? (value ? parseInt(value) : 0)
          : value
    }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.name.trim()) return

    setLoading(true)
    try {
      // Ensure health equals max_health on creation
      const playerData = { ...form, health: form.max_health }
      const player = await createPlayer(playerData)
      navigate(`/chat/${player.id}?new=true`)
    } catch (err) {
      console.error('Failed to create player:', err)
      setLoading(false)
    }
  }

  return (
    <div>
      <Link to="/" className="nav-back">← Back to Characters</Link>
      
      <header className="header">
        <h1>✨ Create New Character ✨</h1>
        <p>Forge a new hero for your adventure</p>
      </header>

      <div className="two-column">
        <div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Character Name *</label>
              <input
                type="text"
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="Enter your hero's name..."
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Class</label>
              <select
                name="character_class"
                value={form.character_class}
                onChange={handleChange}
                disabled={loading}
              >
                <option value="">Choose a class...</option>
                <option value="Warrior">Warrior</option>
                <option value="Mage">Mage</option>
                <option value="Rogue">Rogue</option>
                <option value="Ranger">Ranger</option>
                <option value="Cleric">Cleric</option>
                <option value="Bard">Bard</option>
                <option value="Paladin">Paladin</option>
              </select>
            </div>

            {races.length > 0 && (
              <div className="form-group">
                <label>Race</label>
                <select
                  name="race_id"
                  value={form.race_id || ''}
                  onChange={handleChange}
                  disabled={loading}
                >
                  <option value="">Choose a race...</option>
                  {races.map(race => (
                    <option key={race.id} value={race.id}>{race.name}</option>
                  ))}
                </select>
              </div>
            )}

            {locations.length > 0 && (
              <div className="form-group">
                <label>Starting Location</label>
                <select
                  name="current_location_id"
                  value={form.current_location_id || ''}
                  onChange={handleChange}
                  disabled={loading}
                >
                  {locations.map(loc => (
                    <option key={loc.id} value={loc.id}>{loc.name}</option>
                  ))}
                </select>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>💰 Starting Gold</label>
                <input
                  type="number"
                  name="gold"
                  value={form.gold}
                  onChange={handleChange}
                  min="0"
                  placeholder="0"
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label>❤️ Max Health</label>
                <input
                  type="number"
                  name="max_health"
                  value={form.max_health}
                  onChange={handleChange}
                  min="1"
                  placeholder="100"
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Backstory & Description</label>
              <textarea
                name="description"
                value={form.description}
                onChange={handleChange}
                placeholder="Describe your character's backstory, items they carry, people they know...

Example: 'A grizzled warrior carrying his father's sword, seeking revenge for his fallen village. His old friend Marcus, a blacksmith, gave him a worn but reliable shield before he left.'"
                rows={6}
                disabled={loading}
              />
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                💡 Tip: Mention items, NPCs, and relationships - the Game Master will bring them to life!
              </p>
            </div>

            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={loading || !form.name.trim()}
              style={{ width: '100%', marginTop: '1rem' }}
            >
              {loading ? 'Creating...' : '⚔️ Begin Adventure'}
            </button>
          </form>
        </div>

        <div className="card" style={{ height: 'fit-content' }}>
          <h3 style={{ color: 'var(--gold)', marginBottom: '1rem' }}>📜 Character Preview</h3>
          
          <div style={{ marginBottom: '1rem' }}>
            <strong style={{ color: 'var(--accent)' }}>{form.name || 'Unnamed Hero'}</strong>
            {form.character_class && (
              <span style={{ color: 'var(--text-secondary)' }}> — {form.character_class}</span>
            )}
          </div>

          {form.description && (
            <p style={{ 
              fontStyle: 'italic', 
              color: 'var(--text-secondary)',
              borderLeft: '2px solid var(--accent)',
              paddingLeft: '1rem'
            }}>
              "{form.description}"
            </p>
          )}

          <div style={{ marginTop: '1.5rem', fontSize: '0.9rem' }}>
            <p>❤️ Health: {form.max_health}/{form.max_health}</p>
            <p>💰 Gold: {form.gold}</p>
            <p>📍 Location: {locations.find(l => l.id === form.current_location_id)?.name || 'Unknown'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CreatePlayer
