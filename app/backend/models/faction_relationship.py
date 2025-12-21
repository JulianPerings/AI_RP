from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum, CheckConstraint
from database import Base
import enum

class FactionRelationType(str, enum.Enum):
    ALLIED = "allied"
    ENEMY = "enemy"
    NEUTRAL = "neutral"
    RIVAL = "rival"

class FactionRelationship(Base):
    __tablename__ = "faction_relationship"
    
    id = Column(Integer, primary_key=True, index=True)
    faction_source_id = Column(Integer, ForeignKey("faction.id"), nullable=False)
    faction_target_id = Column(Integer, ForeignKey("faction.id"), nullable=False)
    relationship_modifier = Column(Integer, default=0)
    relationship_type = Column(SQLEnum(FactionRelationType), default=FactionRelationType.NEUTRAL)
    
    __table_args__ = (
        CheckConstraint('relationship_modifier >= -100 AND relationship_modifier <= 100', 
                       name='check_faction_relationship_range'),
    )
