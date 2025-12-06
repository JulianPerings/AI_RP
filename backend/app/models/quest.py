"""Quest model."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.player import Player


class QuestStatus(str, Enum):
    """Quest status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Quest(Base):
    """Quest model."""

    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False)
    
    # Quest Info
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quest_type: Mapped[str] = mapped_column(String(50), nullable=True)  # main, side, daily, etc.
    
    # Status & Progress
    status: Mapped[QuestStatus] = mapped_column(
        SQLEnum(QuestStatus), default=QuestStatus.NOT_STARTED
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    max_progress: Mapped[int] = mapped_column(Integer, default=100)
    
    # Objectives & Rewards
    objectives: Mapped[dict] = mapped_column(JSON, default=dict)
    rewards: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="quests")

    def __repr__(self) -> str:
        return f"<Quest(id={self.id}, title='{self.title}', status={self.status})>"
