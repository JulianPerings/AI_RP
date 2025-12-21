from pydantic import BaseModel, Field
from typing import Optional

class RaceRelationshipCreate(BaseModel):
    race_source_id: int
    race_target_id: int
    base_relationship_modifier: int = Field(default=0, ge=-100, le=100)
    reason: Optional[str] = None

class RaceRelationshipResponse(BaseModel):
    id: int
    race_source_id: int
    race_target_id: int
    base_relationship_modifier: int
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True
