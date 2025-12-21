from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Race
from schemas import RaceCreate, RaceResponse

router = APIRouter(prefix="/races", tags=["races"])

@router.post("/", response_model=RaceResponse)
def create_race(race: RaceCreate, db: Session = Depends(get_db)):
    db_race = Race(**race.model_dump())
    db.add(db_race)
    db.commit()
    db.refresh(db_race)
    return db_race

@router.get("/", response_model=List[RaceResponse])
def get_races(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    races = db.query(Race).offset(skip).limit(limit).all()
    return races

@router.get("/{race_id}", response_model=RaceResponse)
def get_race(race_id: int, db: Session = Depends(get_db)):
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return race

@router.put("/{race_id}", response_model=RaceResponse)
def update_race(race_id: int, race: RaceCreate, db: Session = Depends(get_db)):
    db_race = db.query(Race).filter(Race.id == race_id).first()
    if not db_race:
        raise HTTPException(status_code=404, detail="Race not found")
    
    for key, value in race.model_dump().items():
        setattr(db_race, key, value)
    
    db.commit()
    db.refresh(db_race)
    return db_race

@router.delete("/{race_id}")
def delete_race(race_id: int, db: Session = Depends(get_db)):
    db_race = db.query(Race).filter(Race.id == race_id).first()
    if not db_race:
        raise HTTPException(status_code=404, detail="Race not found")
    
    db.delete(db_race)
    db.commit()
    return {"message": "Race deleted successfully"}
