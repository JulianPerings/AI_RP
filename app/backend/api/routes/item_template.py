from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.item_template import ItemTemplate, ItemCategory
from schemas.item_template import ItemTemplateCreate, ItemTemplateResponse

router = APIRouter(prefix="/item-templates", tags=["item-templates"])

@router.post("/", response_model=ItemTemplateResponse)
def create_item_template(template: ItemTemplateCreate, db: Session = Depends(get_db)):
    db_template = ItemTemplate(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/", response_model=List[ItemTemplateResponse])
def get_item_templates(
    skip: int = 0, 
    limit: int = 100,
    category: Optional[ItemCategory] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ItemTemplate)
    if category:
        query = query.filter(ItemTemplate.category == category)
    templates = query.offset(skip).limit(limit).all()
    return templates

@router.get("/{template_id}", response_model=ItemTemplateResponse)
def get_item_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(ItemTemplate).filter(ItemTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Item template not found")
    return template

@router.put("/{template_id}", response_model=ItemTemplateResponse)
def update_item_template(template_id: int, template: ItemTemplateCreate, db: Session = Depends(get_db)):
    db_template = db.query(ItemTemplate).filter(ItemTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Item template not found")
    
    for key, value in template.model_dump().items():
        setattr(db_template, key, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/{template_id}")
def delete_item_template(template_id: int, db: Session = Depends(get_db)):
    db_template = db.query(ItemTemplate).filter(ItemTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Item template not found")
    
    db.delete(db_template)
    db.commit()
    return {"message": "Item template deleted successfully"}
