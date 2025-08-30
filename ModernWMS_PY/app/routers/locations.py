from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import List, Optional

from ..database import get_db
from ..models import Location, Warehouse, Inventory
from ..schemas import (
    LocationCreate, LocationInDB, LocationUpdate,
    success_response, error_response, PaginatedResponse, Pagination
)

router = APIRouter(prefix="/api/locations", tags=["locations"])

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_location(location: LocationCreate, db: Session = Depends(get_db)):
    """Create a new location"""
    # Check if warehouse exists
    warehouse = db.get(Warehouse, location.warehouse_id)
    if not warehouse:
        return error_response(f"Warehouse with ID {location.warehouse_id} not found", status.HTTP_404_NOT_FOUND)
    
    # Check if location code already exists in the warehouse
    existing = db.execute(
        select(Location).where(
            and_(
                Location.warehouse_id == location.warehouse_id,
                Location.location_code == location.location_code,
                Location.is_deleted == False
            )
        )
    ).scalar_one_or_none()
    
    if existing:
        return error_response(
            f"Location with code {location.location_code} already exists in this warehouse", 
            status.HTTP_400_BAD_REQUEST
        )
    
    # Create new location
    db_location = Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    return success_response(LocationInDB.from_orm(db_location).dict(), "Location created successfully")

@router.get("/{location_id}", response_model=dict)
async def get_location(location_id: int, db: Session = Depends(get_db)):
    """Get a location by ID"""
    location = db.get(Location, location_id)
    if not location or location.is_deleted:
        return error_response(f"Location with ID {location_id} not found", status.HTTP_404_NOT_FOUND)
    
    return success_response(LocationInDB.from_orm(location).dict())

@router.get("/", response_model=dict)
async def list_locations(
    warehouse_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List locations with filtering and pagination"""
    query = select(Location).where(Location.is_deleted == False)
    
    # Apply filters
    if warehouse_id is not None:
        query = query.where(Location.warehouse_id == warehouse_id)
    
    if is_active is not None:
        query = query.where(Location.is_active == is_active)
    
    # Apply search filter if provided
    if search:
        search = f"%{search}%"
        query = query.where(
            (Location.location_code.ilike(search)) |
            (Location.location_name.ilike(search)) |
            (Location.zone.ilike(search))
        )
    
    # Get total count for pagination
    total = db.scalar(select(Location).select_from(query.subquery()).count())
    
    # Apply pagination
    locations = db.execute(
        query.offset(skip).limit(limit)
    ).scalars().all()
    
    # Format response
    items = [LocationInDB.from_orm(loc).dict() for loc in locations]
    pagination = Pagination(
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit if limit > 0 else 1
    )
    
    return PaginatedResponse(
        data={"items": items},
        pagination=pagination
    )

@router.put("/{location_id}", response_model=dict)
async def update_location(
    location_id: int, 
    location_update: LocationUpdate, 
    db: Session = Depends(get_db)
):
    """Update a location"""
    db_location = db.get(Location, location_id)
    if not db_location or db_location.is_deleted:
        return error_response(f"Location with ID {location_id} not found", status.HTTP_404_NOT_FOUND)
    
    # Check if warehouse exists if being updated
    if location_update.warehouse_id and location_update.warehouse_id != db_location.warehouse_id:
        warehouse = db.get(Warehouse, location_update.warehouse_id)
        if not warehouse:
            return error_response(f"Warehouse with ID {location_update.warehouse_id} not found", status.HTTP_404_NOT_FOUND)
    
    # Check if location code is being changed to an existing one in the same warehouse
    if (location_update.location_code and 
        location_update.location_code != db_location.location_code):
        existing = db.execute(
            select(Location).where(
                and_(
                    Location.warehouse_id == (location_update.warehouse_id or db_location.warehouse_id),
                    Location.location_code == location_update.location_code,
                    Location.id != location_id,
                    Location.is_deleted == False
                )
            )
        ).scalar_one_or_none()
        if existing:
            return error_response(
                f"Location with code {location_update.location_code} already exists in this warehouse", 
                status.HTTP_400_BAD_REQUEST
            )
    
    # Update location fields
    update_data = location_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_location, field, value)
    
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    return success_response(LocationInDB.from_orm(db_location).dict(), "Location updated successfully")

@router.delete("/{location_id}", status_code=status.HTTP_200_OK)
async def delete_location(location_id: int, db: Session = Depends(get_db)):
    """Delete a location (soft delete)"""
    location = db.get(Location, location_id)
    if not location or location.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with ID {location_id} not found"
        )
    
    # Check if location has inventory
    has_inventory = db.execute(
        select(Inventory).where(
            Inventory.location_id == location_id,
            Inventory.quantity > 0
        )
    ).scalar_one_or_none()
    
    if has_inventory:
        return error_response("Cannot delete location with inventory", status.HTTP_400_BAD_REQUEST)
    
    # Soft delete
    location.is_deleted = True
    db.add(location)
    db.commit()
    
    return {"status": "success", "message": "Location deleted successfully"}
