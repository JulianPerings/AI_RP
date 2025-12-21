from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Faction
from schemas import FactionCreate, FactionResponse

router = APIRouter(prefix="/factions", tags=["factions"])

@router.post("/", response_model=FactionResponse)
def create_faction(faction: FactionCreate, db: Session = Depends(get_db)):
    db_faction = Faction(**faction.model_dump())
    db.add(db_faction)
    db.commit()
    db.refresh(db_faction)
    return db_faction

@router.get("/", response_model=List[FactionResponse])
def get_factions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    factions = db.query(Faction).offset(skip).limit(limit).all()
    return factions

@router.get("/{faction_id}", response_model=FactionResponse)
def get_faction(faction_id: int, db: Session = Depends(get_db)):
    faction = db.query(Faction).filter(Faction.id == faction_id).first()
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    return faction

@router.put("/{faction_id}", response_model=FactionResponse)
def update_faction(faction_id: int, faction: FactionCreate, db: Session = Depends(get_db)):
    db_faction = db.query(Faction).filter(Faction.id == faction_id).first()
    if not db_faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    
    for key, value in faction.model_dump().items():
        setattr(db_faction, key, value)
    
    db.commit()
    db.refresh(db_faction)
    return db_faction

@router.delete("/{faction_id}")
def delete_faction(faction_id: int, db: Session = Depends(get_db)):
    db_faction = db.query(Faction).filter(Faction.id == faction_id).first()
    if not db_faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    
    db.delete(db_faction)
    db.commit()
    return {"message": "Faction deleted successfully"}
