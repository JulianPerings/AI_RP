from pydantic import BaseModel
from typing import Optional

class LocationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    location_type: Optional[str] = None

class LocationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    location_type: Optional[str]

    class Config:
        from_attributes = True
