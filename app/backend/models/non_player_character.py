from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum, JSON
from database import Base
import enum

class BehaviorState(str, enum.Enum):
    PASSIVE = "passive"
    DEFENSIVE = "defensive"
    AGGRESSIVE = "aggressive"
    HOSTILE = "hostile"
    PROTECTIVE = "protective"

class NonPlayerCharacter(Base):
    __tablename__ = "non_player_character"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    npc_type = Column(String(50))
    health = Column(Integer, default=50)
    max_health = Column(Integer, default=50)
    behavior_state = Column(SQLEnum(BehaviorState), default=BehaviorState.PASSIVE)
    base_disposition = Column(Integer, default=0)
    description = Column(Text)
    dialogue = Column(Text)
    location_id = Column(Integer, ForeignKey("location.id"))
    race_id = Column(Integer, ForeignKey("race.id"))
    faction_id = Column(Integer, ForeignKey("faction.id"))
    personality_traits = Column(JSON, default=dict)
    # Companion system: if set, this NPC follows the player and moves with them
    following_player_id = Column(Integer, ForeignKey("player_character.id"), nullable=True)
