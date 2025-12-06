"""Game event model for tracking player actions and game state changes."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.player import Player


class EventType(str, Enum):
    """Event type enumeration."""
    QUEST_STARTED = "quest_started"
    QUEST_COMPLETED = "quest_completed"
    ITEM_ACQUIRED = "item_acquired"
    ITEM_USED = "item_used"
    LOCATION_CHANGED = "location_changed"
    NPC_INTERACTION = "npc_interaction"
    COMBAT_STARTED = "combat_started"
    COMBAT_ENDED = "combat_ended"
    LEVEL_UP = "level_up"
    PLAYER_DEATH = "player_death"
    CUSTOM = "custom"


class GameEvent(Base):
    """Game event model for tracking player actions."""

    __tablename__ = "game_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False)
    
    # Event Info
    event_type: Mapped[EventType] = mapped_column(SQLEnum(EventType), nullable=False)
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Event Data
    event_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="events")

    def __repr__(self) -> str:
        return f"<GameEvent(id={self.id}, type={self.event_type}, name='{self.event_name}')>"
