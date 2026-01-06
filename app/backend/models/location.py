from sqlalchemy import Column, Integer, String, Text, ForeignKey
from database import Base


class Location(Base):
    __tablename__ = "location"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    location_type = Column(String(50))
    
    # Region connection - locations belong to a region
    region_id = Column(Integer, ForeignKey("region.id"), nullable=True)
    
    # Location-specific modifiers (override/adjust region defaults)
    # None = use region value, value = override or add to region
    danger_modifier = Column(Integer, nullable=True)  # Add to region danger (-2 to +2 scale, or absolute if no region)
    wealth_modifier = Column(Integer, nullable=True)  # Add to region wealth
    climate_override = Column(String(20), nullable=True)  # Override region climate (e.g., cave = "underground")
    population_density = Column(String(20), nullable=True)  # sparse, moderate, dense, crowded
    accessibility = Column(String(20), nullable=True)  # public, restricted, hidden, secret
    notes = Column(Text, nullable=True)  # GM notes about this location
