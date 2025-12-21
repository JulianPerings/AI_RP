from pydantic import BaseModel
from typing import Optional, Dict, Any
from models.item_template import ItemCategory, ItemRarity

class ItemTemplateCreate(BaseModel):
    name: str
    category: ItemCategory
    description: Optional[str] = None
    weight: int = 1
    rarity: Optional[ItemRarity] = ItemRarity.COMMON
    properties: Optional[Dict[str, Any]] = None
    requirements: Optional[Dict[str, Any]] = None

class ItemTemplateResponse(BaseModel):
    id: int
    name: str
    category: ItemCategory
    description: Optional[str]
    weight: int
    rarity: ItemRarity
    properties: Optional[Dict[str, Any]]
    requirements: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True
