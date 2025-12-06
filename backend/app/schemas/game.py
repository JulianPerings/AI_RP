"""Game-related schemas."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from app.schemas.player import PlayerStats
from app.schemas.quest import QuestResponse


class ChatMessage(BaseModel):
    """Chat message schema."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str = Field(..., min_length=1)
    context: Optional[Dict] = None


class ChatResponse(BaseModel):
    """Chat response schema."""
    message: str
    npc_name: Optional[str] = None
    actions: List[str] = Field(default_factory=list)
    state_changes: Dict = Field(default_factory=dict)


class GameStateResponse(BaseModel):
    """Complete game state response."""
    player: PlayerStats
    active_quests: List[QuestResponse]
    current_location: str
    available_actions: List[str]
