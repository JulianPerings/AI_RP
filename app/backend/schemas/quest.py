from pydantic import BaseModel
from typing import Optional

class QuestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    is_active: bool = False
    reward_gold: int = 0
    reward_experience: int = 0
    player_id: Optional[int] = None

class QuestResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_completed: bool
    is_active: bool
    reward_gold: int
    reward_experience: int
    player_id: Optional[int]

    class Config:
        from_attributes = True
