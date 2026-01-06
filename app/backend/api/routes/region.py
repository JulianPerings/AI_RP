from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.region import Region, ClimateType, WealthLevel, DangerLevel
from models.location import Location
from schemas.region import RegionCreate, RegionUpdate, RegionResponse

router = APIRouter(prefix="/regions", tags=["regions"])


@router.post("/", response_model=RegionResponse)
def create_region(region: RegionCreate, db: Session = Depends(get_db)):
    """Create a new region."""
    region_data = region.model_dump()
    
    # Convert string enums to actual enums
    if region_data.get("climate"):
        try:
            region_data["climate"] = ClimateType(region_data["climate"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid climate type. Valid: {[e.value for e in ClimateType]}")
    
    if region_data.get("wealth_level"):
        try:
            region_data["wealth_level"] = WealthLevel(region_data["wealth_level"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid wealth level. Valid: {[e.value for e in WealthLevel]}")
    
    if region_data.get("danger_level"):
        try:
            region_data["danger_level"] = DangerLevel(region_data["danger_level"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid danger level. Valid: {[e.value for e in DangerLevel]}")
    
    db_region = Region(**region_data)
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region


@router.get("/", response_model=List[RegionResponse])
def get_regions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all regions."""
    regions = db.query(Region).offset(skip).limit(limit).all()
    return regions


@router.get("/{region_id}", response_model=RegionResponse)
def get_region(region_id: int, db: Session = Depends(get_db)):
    """Get a specific region by ID."""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.get("/{region_id}/locations")
def get_region_locations(region_id: int, db: Session = Depends(get_db)):
    """Get all locations within a region."""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    locations = db.query(Location).filter(Location.region_id == region_id).all()
    return {
        "region_id": region_id,
        "region_name": region.name,
        "locations": [
            {"id": loc.id, "name": loc.name, "type": loc.location_type, "description": loc.description}
            for loc in locations
        ]
    }


@router.put("/{region_id}", response_model=RegionResponse)
def update_region(region_id: int, region: RegionUpdate, db: Session = Depends(get_db)):
    """Update a region."""
    db_region = db.query(Region).filter(Region.id == region_id).first()
    if not db_region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    update_data = region.model_dump(exclude_unset=True)
    
    # Convert string enums to actual enums
    if "climate" in update_data and update_data["climate"]:
        try:
            update_data["climate"] = ClimateType(update_data["climate"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid climate type")
    
    if "wealth_level" in update_data and update_data["wealth_level"]:
        try:
            update_data["wealth_level"] = WealthLevel(update_data["wealth_level"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid wealth level")
    
    if "danger_level" in update_data and update_data["danger_level"]:
        try:
            update_data["danger_level"] = DangerLevel(update_data["danger_level"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid danger level")
    
    for key, value in update_data.items():
        setattr(db_region, key, value)
    
    db.commit()
    db.refresh(db_region)
    return db_region


@router.delete("/{region_id}")
def delete_region(region_id: int, db: Session = Depends(get_db)):
    """Delete a region."""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    db.delete(region)
    db.commit()
    return {"message": "Region deleted successfully"}
