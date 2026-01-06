from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum
from database import Base
import enum


class ClimateType(str, enum.Enum):
    TEMPERATE = "temperate"
    TROPICAL = "tropical"
    ARID = "arid"
    ARCTIC = "arctic"
    MOUNTAINOUS = "mountainous"
    COASTAL = "coastal"
    SWAMP = "swamp"
    FOREST = "forest"


class WealthLevel(str, enum.Enum):
    DESTITUTE = "destitute"      # Extreme poverty, ruins
    POOR = "poor"                # Struggling, few resources
    MODEST = "modest"            # Average, sustainable
    PROSPEROUS = "prosperous"    # Wealthy, thriving trade
    OPULENT = "opulent"          # Extremely rich, luxury


class DangerLevel(str, enum.Enum):
    SAFE = "safe"                # Peaceful, law-abiding
    LOW = "low"                  # Minor threats, petty crime
    MODERATE = "moderate"        # Some dangers, bandits
    HIGH = "high"                # Frequent threats, monsters
    DEADLY = "deadly"            # Constant danger, war zone


class Region(Base):
    __tablename__ = "region"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    
    # Core description - sets the tone for all locations within
    description = Column(Text)
    
    # Cultural/racial tendencies - guides NPC generation
    dominant_race_description = Column(Text)  # e.g., "Mostly human farmers with scattered elven enclaves"
    
    # Economic character - guides item availability, prices, quest rewards
    wealth_level = Column(SQLEnum(WealthLevel), default=WealthLevel.MODEST)
    wealth_description = Column(Text)  # e.g., "Rich farmland supports comfortable villages"
    
    # Environmental character - guides location descriptions
    climate = Column(SQLEnum(ClimateType), default=ClimateType.TEMPERATE)
    terrain_description = Column(Text)  # e.g., "Rolling hills dotted with ancient oak forests"
    
    # Political/faction context - guides NPC affiliations
    political_description = Column(Text)  # e.g., "Under the loose rule of Baron Aldric"
    dominant_faction_id = Column(Integer, nullable=True)  # Optional link to dominant faction
    
    # Danger/adventure hooks
    danger_level = Column(SQLEnum(DangerLevel), default=DangerLevel.LOW)
    threats_description = Column(Text)  # e.g., "Wolves in winter, occasional goblin raids"
    
    # Lore/history hooks
    history_description = Column(Text)  # e.g., "Once part of the ancient Elven kingdom of Silvanus"
    notable_features = Column(Text)  # e.g., "The Whispering Stones, Old Mill ruins"
