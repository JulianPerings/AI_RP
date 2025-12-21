from sqlalchemy import Column, Integer, String, Text
from database import Base

class Race(Base):
    __tablename__ = "race"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
