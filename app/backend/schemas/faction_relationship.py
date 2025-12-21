from pydantic import BaseModel, Field
from typing import Optional
from models.faction_relationship import FactionRelationType

class FactionRelationshipCreate(BaseModel):
    faction_source_id: int
    faction_target_id: int
    relationship_modifier: int = Field(default=0, ge=-100, le=100)
    relationship_type: Optional[FactionRelationType] = FactionRelationType.NEUTRAL

class FactionRelationshipResponse(BaseModel):
    id: int
    faction_source_id: int
    faction_target_id: int
    relationship_modifier: int
    relationship_type: FactionRelationType
    
    class Config:
        from_attributes = True
