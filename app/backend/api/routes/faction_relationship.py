from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import FactionRelationship
from schemas import FactionRelationshipCreate, FactionRelationshipResponse

router = APIRouter(prefix="/faction-relationships", tags=["faction-relationships"])

@router.post("/", response_model=FactionRelationshipResponse)
def create_faction_relationship(relationship: FactionRelationshipCreate, db: Session = Depends(get_db)):
    db_relationship = FactionRelationship(**relationship.model_dump())
    db.add(db_relationship)
    db.commit()
    db.refresh(db_relationship)
    return db_relationship

@router.get("/", response_model=List[FactionRelationshipResponse])
def get_faction_relationships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    relationships = db.query(FactionRelationship).offset(skip).limit(limit).all()
    return relationships

@router.get("/{relationship_id}", response_model=FactionRelationshipResponse)
def get_faction_relationship(relationship_id: int, db: Session = Depends(get_db)):
    relationship = db.query(FactionRelationship).filter(FactionRelationship.id == relationship_id).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Faction relationship not found")
    return relationship

@router.get("/between/{faction_source_id}/{faction_target_id}", response_model=FactionRelationshipResponse)
def get_faction_relationship_between(faction_source_id: int, faction_target_id: int, db: Session = Depends(get_db)):
    relationship = db.query(FactionRelationship).filter(
        FactionRelationship.faction_source_id == faction_source_id,
        FactionRelationship.faction_target_id == faction_target_id
    ).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Faction relationship not found")
    return relationship

@router.put("/{relationship_id}", response_model=FactionRelationshipResponse)
def update_faction_relationship(relationship_id: int, relationship: FactionRelationshipCreate, db: Session = Depends(get_db)):
    db_relationship = db.query(FactionRelationship).filter(FactionRelationship.id == relationship_id).first()
    if not db_relationship:
        raise HTTPException(status_code=404, detail="Faction relationship not found")
    
    for key, value in relationship.model_dump().items():
        setattr(db_relationship, key, value)
    
    db.commit()
    db.refresh(db_relationship)
    return db_relationship

@router.delete("/{relationship_id}")
def delete_faction_relationship(relationship_id: int, db: Session = Depends(get_db)):
    db_relationship = db.query(FactionRelationship).filter(FactionRelationship.id == relationship_id).first()
    if not db_relationship:
        raise HTTPException(status_code=404, detail="Faction relationship not found")
    
    db.delete(db_relationship)
    db.commit()
    return {"message": "Faction relationship deleted successfully"}
