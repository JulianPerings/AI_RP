from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.item_instance import ItemInstance, OwnerType
from schemas.item_instance import ItemInstanceCreate, ItemInstanceResponse

router = APIRouter(prefix="/item-instances", tags=["item-instances"])

@router.post("/", response_model=ItemInstanceResponse)
def create_item_instance(instance: ItemInstanceCreate, db: Session = Depends(get_db)):
    db_instance = ItemInstance(**instance.model_dump())
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    return db_instance

@router.get("/", response_model=List[ItemInstanceResponse])
def get_item_instances(
    skip: int = 0, 
    limit: int = 100,
    owner_type: Optional[OwnerType] = None,
    owner_id: Optional[int] = None,
    location_id: Optional[int] = None,
    template_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ItemInstance)
    
    if owner_type:
        query = query.filter(ItemInstance.owner_type == owner_type)
    if owner_id is not None:
        query = query.filter(ItemInstance.owner_id == owner_id)
    if location_id is not None:
        query = query.filter(ItemInstance.location_id == location_id)
    if template_id is not None:
        query = query.filter(ItemInstance.template_id == template_id)
    
    instances = query.offset(skip).limit(limit).all()
    return instances

@router.get("/{instance_id}", response_model=ItemInstanceResponse)
def get_item_instance(instance_id: int, db: Session = Depends(get_db)):
    instance = db.query(ItemInstance).filter(ItemInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Item instance not found")
    return instance

@router.get("/owner/{owner_type}/{owner_id}", response_model=List[ItemInstanceResponse])
def get_items_by_owner(owner_type: OwnerType, owner_id: int, db: Session = Depends(get_db)):
    """Get all items owned by a specific character (PC or NPC)"""
    instances = db.query(ItemInstance).filter(
        ItemInstance.owner_type == owner_type,
        ItemInstance.owner_id == owner_id
    ).all()
    return instances

@router.get("/location/{location_id}", response_model=List[ItemInstanceResponse])
def get_items_at_location(location_id: int, db: Session = Depends(get_db)):
    """Get all items at a specific location (on the ground)"""
    instances = db.query(ItemInstance).filter(
        ItemInstance.location_id == location_id,
        ItemInstance.owner_type == OwnerType.NONE
    ).all()
    return instances

@router.put("/{instance_id}", response_model=ItemInstanceResponse)
def update_item_instance(instance_id: int, instance: ItemInstanceCreate, db: Session = Depends(get_db)):
    db_instance = db.query(ItemInstance).filter(ItemInstance.id == instance_id).first()
    if not db_instance:
        raise HTTPException(status_code=404, detail="Item instance not found")
    
    for key, value in instance.model_dump().items():
        setattr(db_instance, key, value)
    
    db.commit()
    db.refresh(db_instance)
    return db_instance

@router.patch("/{instance_id}/transfer", response_model=ItemInstanceResponse)
def transfer_item(
    instance_id: int,
    new_owner_type: OwnerType,
    new_owner_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Transfer item ownership (e.g., trade, loot, drop)"""
    db_instance = db.query(ItemInstance).filter(ItemInstance.id == instance_id).first()
    if not db_instance:
        raise HTTPException(status_code=404, detail="Item instance not found")
    
    db_instance.owner_type = new_owner_type
    db_instance.owner_id = new_owner_id
    db_instance.is_equipped = False  # Unequip when transferring
    
    db.commit()
    db.refresh(db_instance)
    return db_instance

@router.patch("/{instance_id}/enchant", response_model=ItemInstanceResponse)
def enchant_item(
    instance_id: int,
    enchantments: dict,
    db: Session = Depends(get_db)
):
    """Add or update enchantments on an item instance"""
    db_instance = db.query(ItemInstance).filter(ItemInstance.id == instance_id).first()
    if not db_instance:
        raise HTTPException(status_code=404, detail="Item instance not found")
    
    # Merge new enchantments with existing ones
    current_enchantments = db_instance.enchantments or {}
    current_enchantments.update(enchantments)
    db_instance.enchantments = current_enchantments
    
    db.commit()
    db.refresh(db_instance)
    return db_instance

@router.delete("/{instance_id}")
def delete_item_instance(instance_id: int, db: Session = Depends(get_db)):
    db_instance = db.query(ItemInstance).filter(ItemInstance.id == instance_id).first()
    if not db_instance:
        raise HTTPException(status_code=404, detail="Item instance not found")
    
    db.delete(db_instance)
    db.commit()
    return {"message": "Item instance deleted successfully"}
