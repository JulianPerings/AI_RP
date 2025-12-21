from pydantic import BaseModel
from typing import Optional, Dict
from models.non_player_character import BehaviorState

class NonPlayerCharacterCreate(BaseModel):
    name: str
    npc_type: Optional[str] = None
    health: int = 50
    max_health: int = 50
    behavior_state: Optional[BehaviorState] = BehaviorState.PASSIVE
    base_disposition: int = 0
    description: Optional[str] = None
    dialogue: Optional[str] = None
    location_id: Optional[int] = None
    race_id: Optional[int] = None
    faction_id: Optional[int] = None
    personality_traits: Optional[Dict[str, bool]] = None

class NonPlayerCharacterResponse(BaseModel):
    id: int
    name: str
    npc_type: Optional[str]
    health: int
    max_health: int
    behavior_state: BehaviorState
    base_disposition: int
    description: Optional[str]
    dialogue: Optional[str]
    location_id: Optional[int]
    race_id: Optional[int]
    faction_id: Optional[int]
    personality_traits: Optional[Dict[str, bool]]

    class Config:
        from_attributes = True
