"""Player model."""

from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.inventory import Inventory
    from app.models.quest import Quest
    from app.models.event import GameEvent


class Player(Base):
    """Player/Character model."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Character Info
    character_name: Mapped[str] = mapped_column(String(100), nullable=False)
    character_class: Mapped[str] = mapped_column(String(50), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience: Mapped[int] = mapped_column(Integer, default=0)
    
    # Stats
    health: Mapped[int] = mapped_column(Integer, default=100)
    max_health: Mapped[int] = mapped_column(Integer, default=100)
    mana: Mapped[int] = mapped_column(Integer, default=50)
    max_mana: Mapped[int] = mapped_column(Integer, default=50)
    
    # Location & State
    current_location: Mapped[str] = mapped_column(String(100), default="Starting Village")
    game_state: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Conversation Context (for LLM memory)
    conversation_history: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    inventory: Mapped[List["Inventory"]] = relationship(
        "Inventory", back_populates="player", cascade="all, delete-orphan"
    )
    quests: Mapped[List["Quest"]] = relationship(
        "Quest", back_populates="player", cascade="all, delete-orphan"
    )
    events: Mapped[List["GameEvent"]] = relationship(
        "GameEvent", back_populates="player", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Player(id={self.id}, username='{self.username}', character_name='{self.character_name}')>"
