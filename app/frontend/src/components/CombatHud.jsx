import { useMemo, useState } from 'react'

function hpPercent(member) {
  const hp = typeof member?.hp === 'number' ? member.hp : 0
  const maxHp = typeof member?.max_hp === 'number' ? member.max_hp : 1
  const pct = Math.round((hp / Math.max(maxHp, 1)) * 100)
  return Math.max(0, Math.min(100, pct))
}

function memberStatus(member) {
  const hp = typeof member?.hp === 'number' ? member.hp : 0
  if (hp <= 0) return 'DOWN'
  return 'OK'
}

function TeamPanel({ title, members, accentClass, compact }) {
  return (
    <div className={`combat-team ${accentClass}`}>
      <div className="combat-team-title">{title}</div>
      {(!members || members.length === 0) ? (
        <div className="combat-empty">None</div>
      ) : (
        <div className={`combat-team-list ${compact ? 'compact' : ''}`}>
          {members.map((m) => {
            const pct = hpPercent(m)
            const status = memberStatus(m)
            return (
              <div key={`${m.type}-${m.id}`} className={`combatant ${status === 'DOWN' ? 'down' : ''} ${compact ? 'compact' : ''}`}>
                <div className="combatant-top">
                  <div className="combatant-name">
                    {m.name || 'Unknown'}
                    <span className="combatant-meta"> ({m.type} {m.id})</span>
                  </div>
                  <div className={`combatant-status ${status === 'DOWN' ? 'down' : 'ok'}`}>{status}</div>
                </div>
                <div className="combatant-hp-row">
                  <div className="combatant-hp-bar">
                    <div
                      className="combatant-hp-fill"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="combatant-hp-text">{m.hp}/{m.max_hp}</div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function CombatHud({ combatState }) {
  if (!combatState?.in_combat) return null

  const [collapsed, setCollapsed] = useState(true)

  const counts = useMemo(() => {
    const playerTeam = combatState.player_team || []
    const enemyTeam = combatState.enemy_team || []
    const down = (m) => (typeof m?.hp === 'number' ? m.hp : 0) <= 0
    return {
      player: playerTeam.length,
      enemy: enemyTeam.length,
      playerDown: playerTeam.filter(down).length,
      enemyDown: enemyTeam.filter(down).length,
    }
  }, [combatState])

  return (
    <div className={`combat-hud ${collapsed ? 'collapsed' : ''}`}>
      <div className="combat-hud-header">
        <div className="combat-hud-title">⚔️ Combat</div>
        <div className="combat-hud-desc">{combatState.description || 'Battle in progress'}</div>
        <div className="combat-hud-stats">
          <span className="combat-pill">Allies: {counts.player} ({counts.playerDown} down)</span>
          <span className="combat-pill enemy">Enemies: {counts.enemy} ({counts.enemyDown} down)</span>
        </div>
        <button type="button" className="btn btn-secondary combat-toggle" onClick={() => setCollapsed(v => !v)}>
          {collapsed ? 'Show' : 'Hide'}
        </button>
      </div>

      {!collapsed && (
        <div className="combat-hud-grid">
          <TeamPanel title="Your Team" members={combatState.player_team || []} accentClass="team-player" compact />
          <TeamPanel title="Enemy Team" members={combatState.enemy_team || []} accentClass="team-enemy" compact />
        </div>
      )}
    </div>
  )
}

export default CombatHud
