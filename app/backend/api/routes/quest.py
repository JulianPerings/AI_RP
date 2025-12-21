from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.quest import Quest
from schemas.quest import QuestCreate, QuestResponse

router = APIRouter(prefix="/quests", tags=["quests"])

@router.post("/", response_model=QuestResponse)
def create_quest(quest: QuestCreate, db: Session = Depends(get_db)):
    db_quest = Quest(**quest.model_dump())
    db.add(db_quest)
    db.commit()
    db.refresh(db_quest)
    return db_quest

@router.get("/", response_model=List[QuestResponse])
def get_quests(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    quests = db.query(Quest).offset(skip).limit(limit).all()
    return quests

@router.get("/{quest_id}", response_model=QuestResponse)
def get_quest(quest_id: int, db: Session = Depends(get_db)):
    quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    return quest

@router.put("/{quest_id}", response_model=QuestResponse)
def update_quest(quest_id: int, quest: QuestCreate, db: Session = Depends(get_db)):
    db_quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not db_quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    for key, value in quest.model_dump().items():
        setattr(db_quest, key, value)
    
    db.commit()
    db.refresh(db_quest)
    return db_quest

@router.delete("/{quest_id}")
def delete_quest(quest_id: int, db: Session = Depends(get_db)):
    quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    db.delete(quest)
    db.commit()
    return {"message": "Quest deleted successfully"}
