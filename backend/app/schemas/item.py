"""Item schemas."""

from datetime import datetime
from typing import Dict
from pydantic import BaseModel, Field
from app.models.item import ItemType


class ItemBase(BaseModel):
    """Base item schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str
    item_type: ItemType


class ItemCreate(ItemBase):
    """Schema for creating a new item."""
    rarity: str = "common"
    value: int = 0
    weight: int = 1
    stackable: bool = True
    max_stack: int = 99
    stats: Dict = Field(default_factory=dict)
    effects: Dict = Field(default_factory=dict)


class ItemResponse(ItemBase):
    """Schema for item response."""
    id: int
    rarity: str
    value: int
    weight: int
    stackable: bool
    max_stack: int
    stats: Dict
    effects: Dict
    created_at: datetime

    model_config = {"from_attributes": True}


class InventoryItemResponse(BaseModel):
    """Schema for inventory item with quantity."""
    item: ItemResponse
    quantity: int
    equipped: bool
    acquired_at: datetime

    model_config = {"from_attributes": True}
