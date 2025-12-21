from sqlalchemy import Column, Integer, String, Text
from database import Base

class Location(Base):
    __tablename__ = "location"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    location_type = Column(String(50))
