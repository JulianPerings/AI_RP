from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.player_character import PlayerCharacter
from schemas.player_character import PlayerCharacterCreate, PlayerCharacterResponse

router = APIRouter(prefix="/player-characters", tags=["player_characters"])

@router.post("/", response_model=PlayerCharacterResponse)
def create_player_character(character: PlayerCharacterCreate, db: Session = Depends(get_db)):
    # Create the player character with empty story
    db_character = PlayerCharacter(**character.model_dump())
    db_character.story_messages = []  # Initialize empty story
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    
    return db_character

@router.get("/", response_model=List[PlayerCharacterResponse])
def get_player_characters(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    characters = db.query(PlayerCharacter).offset(skip).limit(limit).all()
    return characters

@router.get("/{character_id}", response_model=PlayerCharacterResponse)
def get_player_character(character_id: int, db: Session = Depends(get_db)):
    character = db.query(PlayerCharacter).filter(PlayerCharacter.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Player character not found")
    return character

@router.put("/{character_id}", response_model=PlayerCharacterResponse)
def update_player_character(character_id: int, character: PlayerCharacterCreate, db: Session = Depends(get_db)):
    db_character = db.query(PlayerCharacter).filter(PlayerCharacter.id == character_id).first()
    if not db_character:
        raise HTTPException(status_code=404, detail="Player character not found")
    
    for key, value in character.model_dump().items():
        setattr(db_character, key, value)
    
    db.commit()
    db.refresh(db_character)
    return db_character

@router.delete("/{character_id}")
def delete_player_character(character_id: int, db: Session = Depends(get_db)):
    character = db.query(PlayerCharacter).filter(PlayerCharacter.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Player character not found")
    
    db.delete(character)
    db.commit()
    return {"message": "Player character deleted successfully"}
