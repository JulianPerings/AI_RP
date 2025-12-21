from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.character_relationship import CharacterType, RelationType

class CharacterRelationshipCreate(BaseModel):
    source_character_type: CharacterType
    source_character_id: int
    target_character_type: CharacterType
    target_character_id: int
    relationship_value: int = Field(default=0, ge=-100, le=100)
    relationship_type: Optional[RelationType] = RelationType.NEUTRAL
    notes: Optional[str] = None

class CharacterRelationshipResponse(BaseModel):
    id: int
    source_character_type: CharacterType
    source_character_id: int
    target_character_type: CharacterType
    target_character_id: int
    relationship_value: int
    relationship_type: RelationType
    last_interaction: datetime
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True
