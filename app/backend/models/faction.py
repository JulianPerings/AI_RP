from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum
from database import Base
import enum

class AlignmentType(str, enum.Enum):
    LAWFUL = "lawful"
    NEUTRAL = "neutral"
    CHAOTIC = "chaotic"

class Faction(Base):
    __tablename__ = "faction"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    alignment = Column(SQLEnum(AlignmentType), default=AlignmentType.NEUTRAL)
