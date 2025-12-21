from pydantic import BaseModel
from typing import Optional

class RaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class RaceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True
