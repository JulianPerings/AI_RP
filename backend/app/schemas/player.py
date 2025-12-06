"""Player schemas."""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, EmailStr, Field


class PlayerBase(BaseModel):
    """Base player schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    character_name: str = Field(..., min_length=2, max_length=100)
    character_class: Optional[str] = None


class PlayerCreate(PlayerBase):
    """Schema for creating a new player."""
    password: str = Field(..., min_length=8)


class PlayerUpdate(BaseModel):
    """Schema for updating player info."""
    character_name: Optional[str] = None
    character_class: Optional[str] = None
    current_location: Optional[str] = None


class PlayerResponse(PlayerBase):
    """Schema for player response."""
    id: int
    level: int
    experience: int
    health: int
    max_health: int
    mana: int
    max_mana: int
    current_location: str
    game_state: Dict
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PlayerStats(BaseModel):
    """Player statistics schema."""
    level: int
    experience: int
    health: int
    max_health: int
    mana: int
    max_mana: int
    current_location: str
