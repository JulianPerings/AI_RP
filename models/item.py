"""Item model — weapons, armor, consumables, and quest items."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ItemType(str, Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    QUEST = "quest"
    MISC = "misc"


class Item(BaseModel):
    """An item that can exist in the world or a character's inventory."""

    id: str
    name: str
    description: str = ""
    item_type: ItemType = ItemType.MISC

    # Value
    value: int = 0  # gold value

    # Combat properties (optional, depends on type)
    damage: int = 0  # base damage for weapons
    armor_bonus: int = 0  # AC bonus for armor
    heal_amount: int = 0  # HP restored for consumables

    # Stat requirements / bonuses
    stat_requirement: str = ""  # e.g. "strength"
    stat_requirement_value: int = 0
    stat_bonus: dict[str, int] = Field(default_factory=dict)  # e.g. {"strength": 2}

    # Flags
    equippable: bool = False
    consumable: bool = False
    quest_item: bool = False
    stackable: bool = False
    quantity: int = 1
