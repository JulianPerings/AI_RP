from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from database import get_db
from models import CharacterRelationship
from models.character_relationship import CharacterType
from schemas import CharacterRelationshipCreate, CharacterRelationshipResponse

router = APIRouter(prefix="/relationships", tags=["relationships"])

@router.post("/", response_model=CharacterRelationshipResponse)
def create_relationship(relationship: CharacterRelationshipCreate, db: Session = Depends(get_db)):
    # Validate that source and target are different
    if (relationship.source_character_type == relationship.target_character_type and 
        relationship.source_character_id == relationship.target_character_id):
        raise HTTPException(status_code=400, detail="Character cannot have relationship with itself")
    
    db_relationship = CharacterRelationship(**relationship.model_dump())
    db.add(db_relationship)
    db.commit()
    db.refresh(db_relationship)
    return db_relationship

@router.get("/", response_model=List[CharacterRelationshipResponse])
def get_relationships(
    skip: int = 0, 
    limit: int = 100,
    source_type: Optional[CharacterType] = None,
    source_id: Optional[int] = None,
    target_type: Optional[CharacterType] = None,
    target_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CharacterRelationship)
    
    if source_type:
        query = query.filter(CharacterRelationship.source_character_type == source_type)
    if source_id:
        query = query.filter(CharacterRelationship.source_character_id == source_id)
    if target_type:
        query = query.filter(CharacterRelationship.target_character_type == target_type)
    if target_id:
        query = query.filter(CharacterRelationship.target_character_id == target_id)
    
    relationships = query.offset(skip).limit(limit).all()
    return relationships

@router.get("/{relationship_id}", response_model=CharacterRelationshipResponse)
def get_relationship(relationship_id: int, db: Session = Depends(get_db)):
    relationship = db.query(CharacterRelationship).filter(CharacterRelationship.id == relationship_id).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return relationship

@router.get("/character/{character_type}/{character_id}", response_model=List[CharacterRelationshipResponse])
def get_relationships_for_character(
    character_type: CharacterType, 
    character_id: int, 
    db: Session = Depends(get_db)
):
    """Get all relationships where the character is either source or target"""
    relationships = db.query(CharacterRelationship).filter(
        or_(
            and_(
                CharacterRelationship.source_character_type == character_type,
                CharacterRelationship.source_character_id == character_id
            ),
            and_(
                CharacterRelationship.target_character_type == character_type,
                CharacterRelationship.target_character_id == character_id
            )
        )
    ).all()
    return relationships

@router.get("/between/{source_type}/{source_id}/{target_type}/{target_id}", response_model=CharacterRelationshipResponse)
def get_relationship_between(
    source_type: CharacterType,
    source_id: int,
    target_type: CharacterType,
    target_id: int,
    db: Session = Depends(get_db)
):
    """Get relationship between two specific characters"""
    relationship = db.query(CharacterRelationship).filter(
        CharacterRelationship.source_character_type == source_type,
        CharacterRelationship.source_character_id == source_id,
        CharacterRelationship.target_character_type == target_type,
        CharacterRelationship.target_character_id == target_id
    ).first()
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return relationship

@router.put("/{relationship_id}", response_model=CharacterRelationshipResponse)
def update_relationship(
    relationship_id: int, 
    relationship: CharacterRelationshipCreate, 
    db: Session = Depends(get_db)
):
    db_relationship = db.query(CharacterRelationship).filter(CharacterRelationship.id == relationship_id).first()
    if not db_relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    for key, value in relationship.model_dump().items():
        setattr(db_relationship, key, value)
    
    db.commit()
    db.refresh(db_relationship)
    return db_relationship

@router.delete("/{relationship_id}")
def delete_relationship(relationship_id: int, db: Session = Depends(get_db)):
    db_relationship = db.query(CharacterRelationship).filter(CharacterRelationship.id == relationship_id).first()
    if not db_relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    db.delete(db_relationship)
    db.commit()
    return {"message": "Relationship deleted successfully"}
