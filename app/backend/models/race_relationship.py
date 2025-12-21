from sqlalchemy import Column, Integer, String, Text, ForeignKey, CheckConstraint
from database import Base

class RaceRelationship(Base):
    __tablename__ = "race_relationship"
    
    id = Column(Integer, primary_key=True, index=True)
    race_source_id = Column(Integer, ForeignKey("race.id"), nullable=False)
    race_target_id = Column(Integer, ForeignKey("race.id"), nullable=False)
    base_relationship_modifier = Column(Integer, default=0)
    reason = Column(Text)
    
    __table_args__ = (
        CheckConstraint('base_relationship_modifier >= -100 AND base_relationship_modifier <= 100', 
                       name='check_race_relationship_range'),
    )
