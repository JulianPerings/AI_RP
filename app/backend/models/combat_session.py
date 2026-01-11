"""
Combat Session model for tracking team-based combat encounters.

Stores two teams with participant stats, combat status, and generates
summaries when combat ends.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from database import Base


class CombatSession(Base):
    """Tracks an active or completed combat encounter."""
    __tablename__ = "combat_session"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("player_character.id"), nullable=False, index=True)
    
    # Combat status: active, ended, fled
    status = Column(String(20), default="active", nullable=False)
    
    # Description of the combat encounter
    description = Column(Text)
    
    # Teams as JSON arrays with full stats for context
    # Format: [{"type": "PC"|"NPC", "id": int, "name": str, "hp": int, "max_hp": int, "role": str}]
    team_player = Column(JSON, default=list)  # Player's side (PC + companions + allies)
    team_enemy = Column(JSON, default=list)   # Enemy side
    
    # Combat outcome when ended
    outcome = Column(String(50))  # victory, defeat, fled, negotiated, interrupted
    
    # LLM-generated summary when combat ends
    summary = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    
    def get_combatant(self, char_type: str, char_id: int) -> dict | None:
        """Find a combatant in either team."""
        for member in (self.team_player or []):
            if member.get("type") == char_type and member.get("id") == char_id:
                return member
        for member in (self.team_enemy or []):
            if member.get("type") == char_type and member.get("id") == char_id:
                return member
        return None
    
    def is_active(self) -> bool:
        return self.status == "active"
    
    def format_for_prompt(self) -> str:
        """Format combat state for inclusion in system prompt."""
        lines = [f"## ⚔️ ACTIVE COMBAT: {self.description or 'Battle in progress'}"]
        
        # Player team
        lines.append("\n**Your Team:**")
        for m in (self.team_player or []):
            hp_pct = int((m.get("hp", 0) / max(m.get("max_hp", 1), 1)) * 100)
            status = "💀 DOWN" if m.get("hp", 0) <= 0 else f"{hp_pct}% HP"
            role = f" [{m.get('role')}]" if m.get("role") else ""
            lines.append(f"- {m.get('name', 'Unknown')} ({m.get('type')}){role}: {m.get('hp')}/{m.get('max_hp')} ({status})")
        
        # Enemy team
        lines.append("\n**Enemy Team:**")
        for m in (self.team_enemy or []):
            hp_pct = int((m.get("hp", 0) / max(m.get("max_hp", 1), 1)) * 100)
            status = "💀 DOWN" if m.get("hp", 0) <= 0 else f"{hp_pct}% HP"
            role = f" [{m.get('role')}]" if m.get("role") else ""
            lines.append(f"- {m.get('name', 'Unknown')} ({m.get('type')}){role}: {m.get('hp')}/{m.get('max_hp')} ({status})")
        
        lines.append("\n*Use combat tools to track damage, add/remove combatants, or end combat.*")
        return "\n".join(lines)
