"""Quest schemas."""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field
from app.models.quest import QuestStatus


class QuestBase(BaseModel):
    """Base quest schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    quest_type: Optional[str] = "side"


class QuestCreate(QuestBase):
    """Schema for creating a new quest."""
    objectives: Dict = Field(default_factory=dict)
    rewards: Dict = Field(default_factory=dict)
    max_progress: int = 100


class QuestUpdate(BaseModel):
    """Schema for updating quest progress."""
    status: Optional[QuestStatus] = None
    progress: Optional[int] = None


class QuestResponse(QuestBase):
    """Schema for quest response."""
    id: int
    player_id: int
    status: QuestStatus
    progress: int
    max_progress: int
    objectives: Dict
    rewards: Dict
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
