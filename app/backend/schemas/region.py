from pydantic import BaseModel
from typing import Optional


class RegionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dominant_race_description: Optional[str] = None
    wealth_level: Optional[str] = "modest"
    wealth_description: Optional[str] = None
    climate: Optional[str] = "temperate"
    terrain_description: Optional[str] = None
    political_description: Optional[str] = None
    dominant_faction_id: Optional[int] = None
    danger_level: Optional[str] = "low"
    threats_description: Optional[str] = None
    history_description: Optional[str] = None
    notable_features: Optional[str] = None


class RegionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dominant_race_description: Optional[str] = None
    wealth_level: Optional[str] = None
    wealth_description: Optional[str] = None
    climate: Optional[str] = None
    terrain_description: Optional[str] = None
    political_description: Optional[str] = None
    dominant_faction_id: Optional[int] = None
    danger_level: Optional[str] = None
    threats_description: Optional[str] = None
    history_description: Optional[str] = None
    notable_features: Optional[str] = None


class RegionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    dominant_race_description: Optional[str]
    wealth_level: Optional[str]
    wealth_description: Optional[str]
    climate: Optional[str]
    terrain_description: Optional[str]
    political_description: Optional[str]
    dominant_faction_id: Optional[int]
    danger_level: Optional[str]
    threats_description: Optional[str]
    history_description: Optional[str]
    notable_features: Optional[str]

    class Config:
        from_attributes = True
