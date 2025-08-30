from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional

from ..database import get_db
from ..models import Product
from ..schemas import (
    ProductCreate, ProductInDB, ProductUpdate,
    success_response, error_response, PaginatedResponse, Pagination
)

router = APIRouter(prefix="/api/products", tags=["products"])

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    # Check if SKU already exists
    existing = db.execute(select(Product).where(Product.sku == product.sku)).scalar_one_or_none()
    if existing:
        return error_response(f"Product with SKU {product.sku} already exists", status.HTTP_400_BAD_REQUEST)
    
    # Create new product
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return success_response(ProductInDB.from_orm(db_product).dict(), "Product created successfully")

@router.get("/{product_id}", response_model=dict)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a product by ID"""
    product = db.get(Product, product_id)
    if not product:
        return error_response(f"Product with ID {product_id} not found", status.HTTP_404_NOT_FOUND)
    
    return success_response(ProductInDB.from_orm(product).dict())

@router.get("/", response_model=dict)
async def list_products(
    skip: int = 0, 
    limit: int = 10, 
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all products with pagination and search"""
    query = select(Product)
    
    # Apply search filter if provided
    if search:
        search = f"%{search}%"
        query = query.where(
            (Product.name.ilike(search)) |
            (Product.sku.ilike(search)) |
            (Product.barcode.ilike(search))
        )
    
    # Get total count for pagination
    total = db.scalar(select(Product).select_from(query.subquery()).count())
    
    # Apply pagination
    products = db.execute(
        query.offset(skip).limit(limit)
    ).scalars().all()
    
    # Format response
    items = [ProductInDB.from_orm(p).dict() for p in products]
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

@router.put("/{product_id}", response_model=dict)
async def update_product(
    product_id: int, 
    product_update: ProductUpdate, 
    db: Session = Depends(get_db)
):
    """Update a product"""
    db_product = db.get(Product, product_id)
    if not db_product:
        return error_response(f"Product with ID {product_id} not found", status.HTTP_404_NOT_FOUND)
    
    # Check if SKU is being changed to an existing one
    if product_update.sku != db_product.sku:
        existing = db.execute(
            select(Product).where(Product.sku == product_update.sku)
        ).scalar_one_or_none()
        if existing:
            return error_response(f"SKU {product_update.sku} is already in use", status.HTTP_400_BAD_REQUEST)
    
    # Update product fields
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return success_response(ProductInDB.from_orm(db_product).dict(), "Product updated successfully")

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Soft delete
    product.is_deleted = True
    db.add(product)
    db.commit()
    
    return {"status": "success", "message": "Product deleted successfully"}
