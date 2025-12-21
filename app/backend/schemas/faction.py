from pydantic import BaseModel
from typing import Optional
from models.faction import AlignmentType

class FactionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    alignment: Optional[AlignmentType] = AlignmentType.NEUTRAL

class FactionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    alignment: AlignmentType
    
    class Config:
        from_attributes = True
