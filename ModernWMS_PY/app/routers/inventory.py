from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Inventory, Product, Warehouse, Location
from ..schemas import (
    InventoryBase, InventoryInDB, success_response, 
    error_response, PaginatedResponse, Pagination
)

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

@router.get("/", response_model=dict)
async def list_inventory(
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    location_id: Optional[int] = None,
    has_stock: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List inventory with filtering and pagination"""
    query = select(Inventory).join(Inventory.product).join(Inventory.warehouse).join(Inventory.location)
    
    # Apply filters
    filters = []
    if product_id is not None:
        filters.append(Inventory.product_id == product_id)
    if warehouse_id is not None:
        filters.append(Inventory.warehouse_id == warehouse_id)
    if location_id is not None:
        filters.append(Inventory.location_id == location_id)
    if has_stock is not None:
        if has_stock:
            filters.append(Inventory.quantity > 0)
        else:
            filters.append(Inventory.quantity == 0)
    
    # Only show non-deleted items
    filters.extend([
        Product.is_deleted == False,
        Warehouse.is_deleted == False,
        Location.is_deleted == False
    ])
    
    query = query.where(and_(*filters))
    
    # Get total count for pagination
    total = db.scalar(select(Inventory).select_from(query.subquery()).count())
    
    # Apply pagination
    inventory_items = db.execute(
        query.offset(skip).limit(limit)
    ).scalars().all()
    
    # Format response
    items = [{
        "id": item.id,
        "product_id": item.product_id,
        "product_name": item.product.name,
        "product_sku": item.product.sku,
        "warehouse_id": item.warehouse_id,
        "warehouse_name": item.warehouse.name,
        "location_id": item.location_id,
        "location_code": item.location.location_code,
        "quantity": float(item.quantity),
        "allocated_quantity": float(item.allocated_quantity),
        "available_quantity": float(item.available_quantity),
        "lot_number": item.lot_number,
        "serial_number": item.serial_number,
        "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None
    } for item in inventory_items]
    
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

@router.post("/receive", response_model=dict, status_code=status.HTTP_201_CREATED)
async def receive_inventory(
    product_id: int,
    warehouse_id: int,
    location_id: int,
    quantity: float,
    lot_number: Optional[str] = None,
    serial_number: Optional[str] = None,
    expiry_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Receive inventory into a location"""
    # Validate product
    product = db.get(Product, product_id)
    if not product or product.is_deleted:
        return error_response(f"Product with ID {product_id} not found", status.HTTP_404_NOT_FOUND)
    
    # Validate warehouse
    warehouse = db.get(Warehouse, warehouse_id)
    if not warehouse or warehouse.is_deleted:
        return error_response(f"Warehouse with ID {warehouse_id} not found", status.HTTP_404_NOT_FOUND)
    
    # Validate location
    location = db.get(Location, location_id)
    if not location or location.is_deleted:
        return error_response(f"Location with ID {location_id} not found", status.HTTP_404_NOT_FOUND)
    
    if location.warehouse_id != warehouse_id:
        return error_response("Location does not belong to the specified warehouse", status.HTTP_400_BAD_REQUEST)
    
    # Check if inventory item already exists with the same product, location, and lot/serial
    query = select(Inventory).where(
        and_(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
            Inventory.location_id == location_id,
            Inventory.is_deleted == False
        )
    )
    
    if lot_number:
        query = query.where(Inventory.lot_number == lot_number)
    else:
        query = query.where(Inventory.lot_number.is_(None))
    
    if serial_number:
        query = query.where(Inventory.serial_number == serial_number)
    else:
        query = query.where(Inventory.serial_number.is_(None))
    
    inventory_item = db.execute(query).scalar_one_or_none()
    
    if inventory_item:
        # Update existing inventory
        inventory_item.quantity += quantity
        inventory_item.available_quantity += quantity
    else:
        # Create new inventory record
        inventory_item = Inventory(
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            quantity=quantity,
            allocated_quantity=0,
            available_quantity=quantity,
            lot_number=lot_number,
            serial_number=serial_number,
            expiry_date=expiry_date
        )
        db.add(inventory_item)
    
    db.commit()
    db.refresh(inventory_item)
    
    return success_response(
        {
            "inventory_id": inventory_item.id,
            "product_id": inventory_item.product_id,
            "warehouse_id": inventory_item.warehouse_id,
            "location_id": inventory_item.location_id,
            "quantity": float(inventory_item.quantity),
            "available_quantity": float(inventory_item.available_quantity)
        },
        "Inventory received successfully"
    )

@router.post("/adjust", response_model=dict)
async def adjust_inventory(
    inventory_id: int,
    adjustment: float,
    reason: str,
    db: Session = Depends(get_db)
):
    """Adjust inventory quantity (positive or negative)"""
    inventory_item = db.get(Inventory, inventory_id)
    if not inventory_item or inventory_item.is_deleted:
        return error_response(f"Inventory with ID {inventory_id} not found", status.HTTP_404_NOT_FOUND)
    
    # Check if adjustment would result in negative quantity
    if (inventory_item.quantity + adjustment) < 0:
        return error_response("Adjustment would result in negative inventory", status.HTTP_400_BAD_REQUEST)
    
    # Update quantities
    inventory_item.quantity += adjustment
    inventory_item.available_quantity += adjustment  # Simplified - in a real app, consider allocated quantities
    
    # In a real app, you would also create an inventory transaction record here
    # to track the adjustment with the reason
    
    db.add(inventory_item)
    db.commit()
    db.refresh(inventory_item)
    
    return success_response(
        {
            "inventory_id": inventory_item.id,
            "new_quantity": float(inventory_item.quantity),
            "new_available_quantity": float(inventory_item.available_quantity)
        },
        "Inventory adjusted successfully"
    )

@router.get("/transactions", response_model=dict)
async def list_inventory_transactions(
    inventory_id: Optional[int] = None,
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    location_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List inventory transactions with filtering"""
    # In a real implementation, this would query an InventoryTransaction table
    # For now, we'll return a placeholder response
    
    # This is a placeholder - in a real app, you would have an InventoryTransaction model
    # and query it with the provided filters
    
    return success_response({
        "items": [],
        "pagination": {
            "total": 0,
            "page": 1,
            "page_size": limit,
            "total_pages": 0
        }
    })
