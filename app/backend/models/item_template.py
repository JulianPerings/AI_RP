from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum, JSON
from database import Base
import enum

class ItemCategory(str, enum.Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    FOOD = "food"
    QUEST = "quest"
    MATERIAL = "material"
    MISC = "misc"

class ItemRarity(str, enum.Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    ARTIFACT = "artifact"

class ItemTemplate(Base):
    __tablename__ = "item_template"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(SQLEnum(ItemCategory), nullable=False)
    description = Column(Text)
    weight = Column(Integer, default=1)
    rarity = Column(SQLEnum(ItemRarity), default=ItemRarity.COMMON)
    
    properties = Column(JSON, default=dict)
    requirements = Column(JSON, default=dict)
