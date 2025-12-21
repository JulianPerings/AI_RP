from pydantic import BaseModel
from typing import Optional, Dict, Any
from models.item_instance import OwnerType

class ItemInstanceCreate(BaseModel):
    template_id: int
    owner_type: Optional[OwnerType] = OwnerType.NONE
    owner_id: Optional[int] = None
    location_id: Optional[int] = None
    is_equipped: bool = False
    quantity: int = 1
    durability: int = 100
    custom_name: Optional[str] = None
    enchantments: Optional[Dict[str, Any]] = None

class ItemInstanceResponse(BaseModel):
    id: int
    template_id: int
    owner_type: OwnerType
    owner_id: Optional[int]
    location_id: Optional[int]
    is_equipped: bool
    quantity: int
    durability: int
    custom_name: Optional[str]
    enchantments: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True
