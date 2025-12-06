"""Item model."""

from datetime import datetime
from enum import Enum
from sqlalchemy import String, Integer, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ItemType(str, Enum):
    """Item type enumeration."""
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    QUEST_ITEM = "quest_item"
    MATERIAL = "material"
    MISC = "misc"


class Item(Base):
    """Item template model."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Item Info
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[ItemType] = mapped_column(SQLEnum(ItemType), nullable=False)
    
    # Properties
    rarity: Mapped[str] = mapped_column(String(20), default="common")  # common, uncommon, rare, epic, legendary
    value: Mapped[int] = mapped_column(Integer, default=0)  # Gold value
    weight: Mapped[int] = mapped_column(Integer, default=1)
    stackable: Mapped[bool] = mapped_column(default=True)
    max_stack: Mapped[int] = mapped_column(Integer, default=99)
    
    # Stats & Effects
    stats: Mapped[dict] = mapped_column(JSON, default=dict)  # damage, defense, etc.
    effects: Mapped[dict] = mapped_column(JSON, default=dict)  # buffs, healing, etc.
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, name='{self.name}', type={self.item_type})>"
