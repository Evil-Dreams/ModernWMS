from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional

from ..database import get_db
from ..models import Warehouse, Location
from ..schemas import (
    WarehouseCreate, WarehouseInDB, WarehouseUpdate,
    success_response, error_response, PaginatedResponse, Pagination
)

router = APIRouter(prefix="/api/warehouses", tags=["warehouses"])

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_warehouse(warehouse: WarehouseCreate, db: Session = Depends(get_db)):
    """Create a new warehouse"""
    # Check if warehouse code already exists
    existing = db.execute(
        select(Warehouse).where(Warehouse.code == warehouse.code)
    ).scalar_one_or_none()
    if existing:
        return error_response(f"Warehouse with code {warehouse.code} already exists", status.HTTP_400_BAD_REQUEST)
    
    # Create new warehouse
    db_warehouse = Warehouse(**warehouse.dict())
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    
    return success_response(WarehouseInDB.from_orm(db_warehouse).dict(), "Warehouse created successfully")

@router.get("/{warehouse_id}", response_model=dict)
async def get_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    """Get a warehouse by ID"""
    warehouse = db.get(Warehouse, warehouse_id)
    if not warehouse:
        return error_response(f"Warehouse with ID {warehouse_id} not found", status.HTTP_404_NOT_FOUND)
    
    return success_response(WarehouseInDB.from_orm(warehouse).dict())

@router.get("/", response_model=dict)
async def list_warehouses(
    skip: int = 0, 
    limit: int = 10, 
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all warehouses with pagination and search"""
    query = select(Warehouse).where(Warehouse.is_deleted == False)
    
    # Apply search filter if provided
    if search:
        search = f"%{search}%"
        query = query.where(
            (Warehouse.name.ilike(search)) |
            (Warehouse.code.ilike(search)) |
            (Warehouse.address.ilike(search))
        )
    
    # Get total count for pagination
    total = db.scalar(select(Warehouse).select_from(query.subquery()).count())
    
    # Apply pagination
    warehouses = db.execute(
        query.offset(skip).limit(limit)
    ).scalars().all()
    
    # Format response
    items = [WarehouseInDB.from_orm(w).dict() for w in warehouses]
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

@router.put("/{warehouse_id}", response_model=dict)
async def update_warehouse(
    warehouse_id: int, 
    warehouse_update: WarehouseUpdate, 
    db: Session = Depends(get_db)
):
    """Update a warehouse"""
    db_warehouse = db.get(Warehouse, warehouse_id)
    if not db_warehouse:
        return error_response(f"Warehouse with ID {warehouse_id} not found", status.HTTP_404_NOT_FOUND)
    
    # Check if code is being changed to an existing one
    if warehouse_update.code != db_warehouse.code:
        existing = db.execute(
            select(Warehouse).where(Warehouse.code == warehouse_update.code)
        ).scalar_one_or_none()
        if existing:
            return error_response(f"Warehouse code {warehouse_update.code} is already in use", status.HTTP_400_BAD_REQUEST)
    
    # Update warehouse fields
    update_data = warehouse_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_warehouse, field, value)
    
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    
    return success_response(WarehouseInDB.from_orm(db_warehouse).dict(), "Warehouse updated successfully")

@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    """Delete a warehouse (soft delete)"""
    warehouse = db.get(Warehouse, warehouse_id)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse with ID {warehouse_id} not found"
        )
    
    # Check if warehouse has locations
    has_locations = db.execute(
        select(Location).where(Location.warehouse_id == warehouse_id, Location.is_deleted == False)
    ).scalar_one_or_none()
    
    if has_locations:
        return error_response("Cannot delete warehouse with active locations", status.HTTP_400_BAD_REQUEST)
    
    # Soft delete
    warehouse.is_deleted = True
    db.add(warehouse)
    db.commit()
    
    return {"status": "success", "message": "Warehouse deleted successfully"}
