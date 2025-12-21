from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum, DateTime, CheckConstraint
from sqlalchemy.sql import func
from database import Base
import enum

class CharacterType(str, enum.Enum):
    PC = "PC"
    NPC = "NPC"

class RelationType(str, enum.Enum):
    ALLY = "ally"
    ENEMY = "enemy"
    RIVAL = "rival"
    FAMILY = "family"
    NEUTRAL = "neutral"
    FRIEND = "friend"
    BUSINESS = "business"

class CharacterRelationship(Base):
    __tablename__ = "character_relationship"
    
    id = Column(Integer, primary_key=True, index=True)
    
    source_character_type = Column(SQLEnum(CharacterType), nullable=False)
    source_character_id = Column(Integer, nullable=False)
    
    target_character_type = Column(SQLEnum(CharacterType), nullable=False)
    target_character_id = Column(Integer, nullable=False)
    
    relationship_value = Column(Integer, default=0)
    relationship_type = Column(SQLEnum(RelationType), default=RelationType.NEUTRAL)
    last_interaction = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    notes = Column(Text)
    
    __table_args__ = (
        CheckConstraint('relationship_value >= -100 AND relationship_value <= 100', 
                       name='check_character_relationship_range'),
        CheckConstraint(
            '(source_character_type != target_character_type) OR (source_character_id != target_character_id)',
            name='check_different_characters'
        ),
    )
