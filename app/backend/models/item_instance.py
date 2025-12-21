from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum as SQLEnum, JSON
from database import Base
import enum

class OwnerType(str, enum.Enum):
    PC = "PC"
    NPC = "NPC"
    NONE = "NONE"

class ItemInstance(Base):
    __tablename__ = "item_instance"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("item_template.id"), nullable=False)
    
    owner_type = Column(SQLEnum(OwnerType), default=OwnerType.NONE)
    owner_id = Column(Integer, nullable=True)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=True)
    
    is_equipped = Column(Boolean, default=False)
    quantity = Column(Integer, default=1)
    durability = Column(Integer, default=100)
    
    custom_name = Column(String(100), nullable=True)
    enchantments = Column(JSON, default=dict)
