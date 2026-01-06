from pydantic import BaseModel
from typing import Optional

class LocationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    location_type: Optional[str] = None
    region_id: Optional[int] = None
    danger_modifier: Optional[int] = None
    wealth_modifier: Optional[int] = None
    climate_override: Optional[str] = None
    population_density: Optional[str] = None
    accessibility: Optional[str] = None
    notes: Optional[str] = None

class LocationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    location_type: Optional[str]
    region_id: Optional[int]
    danger_modifier: Optional[int]
    wealth_modifier: Optional[int]
    climate_override: Optional[str]
    population_density: Optional[str]
    accessibility: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True
