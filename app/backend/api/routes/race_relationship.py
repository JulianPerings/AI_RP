from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import RaceRelationship
from schemas import RaceRelationshipCreate, RaceRelationshipResponse

router = APIRouter(prefix="/race-relationships", tags=["race-relationships"])

@router.post("/", response_model=RaceRelationshipResponse)
def create_race_relationship(relationship: RaceRelationshipCreate, db: Session = Depends(get_db)):
    db_relationship = RaceRelationship(**relationship.model_dump())
    db.add(db_relationship)
    db.commit()
    db.refresh(db_relationship)
    return db_relationship

@router.get("/", response_model=List[RaceRelationshipResponse])
def get_race_relationships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    relationships = db.query(RaceRelationship).offset(skip).limit(limit).all()
    return relationships

@router.get("/{relationship_id}", response_model=RaceRelationshipResponse)
def get_race_relationship(relationship_id: int, db: Session = Depends(get_db)):
    relationship = db.query(RaceRelationship).filter(RaceRelationship.id == relationship_id).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Race relationship not found")
    return relationship

@router.get("/between/{race_source_id}/{race_target_id}", response_model=RaceRelationshipResponse)
def get_race_relationship_between(race_source_id: int, race_target_id: int, db: Session = Depends(get_db)):
    relationship = db.query(RaceRelationship).filter(
        RaceRelationship.race_source_id == race_source_id,
        RaceRelationship.race_target_id == race_target_id
    ).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Race relationship not found")
    return relationship

@router.put("/{relationship_id}", response_model=RaceRelationshipResponse)
def update_race_relationship(relationship_id: int, relationship: RaceRelationshipCreate, db: Session = Depends(get_db)):
    db_relationship = db.query(RaceRelationship).filter(RaceRelationship.id == relationship_id).first()
    if not db_relationship:
        raise HTTPException(status_code=404, detail="Race relationship not found")
    
    for key, value in relationship.model_dump().items():
        setattr(db_relationship, key, value)
    
    db.commit()
    db.refresh(db_relationship)
    return db_relationship

@router.delete("/{relationship_id}")
def delete_race_relationship(relationship_id: int, db: Session = Depends(get_db)):
    db_relationship = db.query(RaceRelationship).filter(RaceRelationship.id == relationship_id).first()
    if not db_relationship:
        raise HTTPException(status_code=404, detail="Race relationship not found")
    
    db.delete(db_relationship)
    db.commit()
    return {"message": "Race relationship deleted successfully"}
