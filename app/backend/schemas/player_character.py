from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class PlayerCharacterCreate(BaseModel):
    name: str
    character_class: Optional[str] = None
    level: int = 1
    health: int = 100
    max_health: int = 100
    experience: int = 0
    gold: int = 0
    luck: int = 3
    description: Optional[str] = None
    current_location_id: Optional[int] = None
    race_id: Optional[int] = None
    primary_faction_id: Optional[int] = None
    reputation: Optional[Dict[str, int]] = None

class PlayerCharacterResponse(BaseModel):
    id: int
    name: str
    character_class: Optional[str]
    level: int
    health: int
    max_health: int
    experience: int
    gold: int
    luck: int
    description: Optional[str]
    current_location_id: Optional[int]
    current_session_id: Optional[str]
    race_id: Optional[int]
    primary_faction_id: Optional[int]
    reputation: Optional[Dict[str, int]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
