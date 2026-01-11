from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from database import Base

class PlayerCharacter(Base):
    __tablename__ = "player_character"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    character_class = Column(String(50))
    level = Column(Integer, default=1)
    health = Column(Integer, default=100)
    max_health = Column(Integer, default=100)
    experience = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    luck = Column(Integer, default=3)  # Currency for rerolling dice
    description = Column(Text)
    current_location_id = Column(Integer)
    race_id = Column(Integer, ForeignKey("race.id"))
    
    # Story messages as JSON list - simple, no foreign keys
    # Format: [{"role": "gm"|"player", "content": "...", "tags": [...], "timestamp": "..."}]
    story_messages = Column(JSON, default=list)
    primary_faction_id = Column(Integer, ForeignKey("faction.id"))
    reputation = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
