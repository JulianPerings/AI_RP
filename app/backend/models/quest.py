from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from database import Base

class Quest(Base):
    __tablename__ = "quest"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    is_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    reward_gold = Column(Integer, default=0)
    reward_experience = Column(Integer, default=0)
    player_id = Column(Integer, ForeignKey("player_character.id"))
