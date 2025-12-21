from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.non_player_character import NonPlayerCharacter
from schemas.non_player_character import NonPlayerCharacterCreate, NonPlayerCharacterResponse

router = APIRouter(prefix="/npcs", tags=["npcs"])

@router.post("/", response_model=NonPlayerCharacterResponse)
def create_npc(npc: NonPlayerCharacterCreate, db: Session = Depends(get_db)):
    db_npc = NonPlayerCharacter(**npc.model_dump())
    db.add(db_npc)
    db.commit()
    db.refresh(db_npc)
    return db_npc

@router.get("/", response_model=List[NonPlayerCharacterResponse])
def get_npcs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    npcs = db.query(NonPlayerCharacter).offset(skip).limit(limit).all()
    return npcs

@router.get("/{npc_id}", response_model=NonPlayerCharacterResponse)
def get_npc(npc_id: int, db: Session = Depends(get_db)):
    npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")
    return npc

@router.put("/{npc_id}", response_model=NonPlayerCharacterResponse)
def update_npc(npc_id: int, npc: NonPlayerCharacterCreate, db: Session = Depends(get_db)):
    db_npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
    if not db_npc:
        raise HTTPException(status_code=404, detail="NPC not found")
    
    for key, value in npc.model_dump().items():
        setattr(db_npc, key, value)
    
    db.commit()
    db.refresh(db_npc)
    return db_npc

@router.delete("/{npc_id}")
def delete_npc(npc_id: int, db: Session = Depends(get_db)):
    npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")
    
    db.delete(npc)
    db.commit()
    return {"message": "NPC deleted successfully"}
